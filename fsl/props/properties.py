#!/usr/bin/env python
#
# properties.py - Python descriptors of various types.
#
# This module should not be imported directly - import the fsl.props
# package instead. Property type definitions are in properties_types.py.
#
# Usage:
#
#     >>> import fsl.props as props
#
#     >>> class PropObj(props.HasProperties):
#     >>>     myProperty = props.Boolean()
#
#     >>> myPropObj = PropObj()
#
#
#     # Access the property value as a normal attribute:
#     >>> myPropObj.myProperty = True
#     >>> myPropObj.myProperty
#     >>> True
#
#
#     # access the props.Boolean instance:
#     >>> myPropObj.getProp('myProperty')
#     >>> <props.prop.Boolean at 0x1045e2710>
#
#
#     # access the underlying props.PropertyValue object
#     # (there are caveats for List properties):
#     >>> myPropObj.getPropVal('myProperty')
#     >>> <props.prop.PropertyValue instance at 0x1047ef518>
#
#
#     # Receive notification of property value changes
#     >>> def myPropertyChanged(value, *args):
#     >>>     print('New property value: {}'.format(value))
#
#     >>> myPropObj.addListener(
#     >>>    'myProperty', 'myListener', myPropertyChanged)
# 
#     >>> myPropObj.myProperty = False
#     >>> New property value: False
#
#
#     # Remove a previously added listener
#     >>> myPropObj.removeListener('myListener')
#
# 
# Lots of the code in this file is probably very confusing. First of
# all, you will need to understand python descriptors.  Descriptors are
# a way of adding properties to python objects, and allowing them to be
# accessed as if they were just simple attributes of the object, but
# controlling the way that the attributes are accessed and assigned.
#
# The following link provides a good overview, and contains the ideas
# which form the basis for the implementation in this module:
#
#  -  http://nbviewer.ipython.org/urls/gist.github.com/\
#     ChrisBeaumont/5758381/raw/descriptor_writeup.ipynb
#
# And if you've got 30 minutes, this video gives a very good
# introduction to descriptors:
#
#  - http://pyvideo.org/video/1760/encapsulation-with-descriptors
#
#
# A HasProperties (sub)class contains a collection of PropertyBase instances
# as class attributes. When an instance of the HasProperties class is created,
# one or more PropertyValue objects are created for each of the PropertyBase
# instances. For most properties, there is a one-to-one mapping between
# PropertyValue instances and PropertyBase instances (per HasProperties
# instance), however this is not mandatory.  For example, the List property
# manages multiple PropertyValue objects for each HasProperties instance.
#
#
# Each of these PropertyValue instances encapsulates a single value, of any
# type.  Whenever a variable value changes, the PropertyValue instance passes
# the new value to the validate method of its parent PropertyBase instance to
# determine whether the new value is valid, and notifies any registered
# listeners of the change. The PropertyValue object will allow its underlying
# value to be set to something invalid, but it will tell registered listeners
# whether the new value is valid or invalid (PropertyValue objects  can
# alternately be configured to raise a ValueError on an attempt to set them
# to an invalid value, but this has some caveats - see the
# PropertyValue.__init__ docstring).
#
#
# The default validation logic of most PropertyBase objects can be configured
# via 'constraints'. For example, the Number property  allows 'minval' and
# 'maxval' constraints to be set.  These may be set via PropertyBase
# constructors, (i.e. when it is defined as a class attribute of a
# HasProperties definition), and may be queried and changed on individual
# HasProperties instances via the getConstraint/setConstraint methods,
# which are available on both PropertyBase and HasProperties objects.
#
#
# Application code may be notified of property changes in two ways.  First, a
# listener may be registered with a PropertyBase object, either via the
# HasProperties.addListener instance method, or the PropertyBase.addListener
# class method (these are equivalent).  Such a listener will be notified of
# changes to any of the PropertyValue objects managed by the PropertyBase
# object, and associated with the HasProperties instance. This is important
# for List properties, as it means that a change to a single PropertyValue
# object in a list will result in notification of all registered listeners.
#
#
# If one is interested in changes to a single PropertyValue object (e.g. one
# element of a List property), then a listener may be registered directly with
# the PropertyValue object, via the PropertyValue.addListener instance
# method. This listener will then only be notified of changes to that
# PropertyValue object.
#
#
# author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

from collections import OrderedDict

log = logging.getLogger(__name__)


class PropertyValue(object):
    """
    Proxy object which encapsulates a single value for a property.
    One or more PropertyValue objects is created for every property
    of a HasProperties instance.
    """

    def __init__(self,
                 prop,
                 owner,
                 name=None,
                 preNotifyFunc=None,
                 allowInvalid=True):
        """
        Create a PropertyValue object. You will need to follow this up
        with a call to set() to set the initial value. Parameters:
        
          - prop:          The PropertyBase object which manages this
                           PropertyValue.
        
          - owner:         The HasProperties object, the owner of the
                           prop property.
        
          - name:          Variable name - if not provided, a default,
                           unique name is created.

          - preNotifyFunc: Function to be called whenever the property
                           value changes, but before any registered
                           listeners are called. Must accept two
                           parameters - the HasProperties object, and
                           the new value.
        
          - allowInvalid:  If False, any attempt to set the value to
                           something invalid will result in a ValueError.
                           Note that this does not guarantee that the
                           property will never have an invalid value, as
                           the definition of 'valid' depends on external
                           factors.  Therefore, the validity of a value
                           may change, even if the value itself has not
                           changed.
        """
        
        if name is None: name = '{}_{}'.format(prop.label, id(self))
        
        self._prop            = prop
        self._owner           = owner
        self._name            = name
        self._preNotifyFunc   = preNotifyFunc
        self._allowInvalid    = allowInvalid
        self._changeListeners = OrderedDict()
        self.__value          = None
        self.__valid          = False

        # Two other private attributes are added to a PropertyValue instance
        # on the first call to set(). They are not added here, as they are
        # used by set() to identify the first call to set().
        # self.__lastValue = None
        # self.__lastValid = False


    def addListener(self, name, callback):
        """
        Adds a listener for this value. When the value changes, the
        listener callback function is called. Listener notification
        may also be programmatically triggered via the
        PropertyBase.forceValidation method. The callback function
        must accept these arguments:

          value    - The property value
          valid    - Whether the value is valid or invalid
          instance - The HasProperties instance
          prop     - The PropertyBase instance
          name     - The name of this PropertyValue

        If you are only interested in the value, you can define your
        callback function like 'def callback(value, *a): ...'
        """
        log.debug('Adding listener on {}: {}'.format(self._name, name))
        name = 'PropertyValue_{}_{}'.format(self._name, name)
        self._changeListeners[name] = callback


    def removeListener(self, name):
        """
        Removes the listener with the given name from the specified
        instance.
        """
        log.debug('Removing listener on {}: {}'.format(self._name, name))
        name = 'PropertyValue_{}_{}'.format(self._name, name)
        self._changeListeners.pop(name, None)

        
    def get(self):
        """
        Returns the current property value.
        """
        return self.__value

        
    def set(self, newValue):
        """
        Sets the property value. The property is validated and, if the
        property value or its validity has changed, any registered
        listeners are notified.  If allowInvalid was set to False, and
        the new value is not valid, a ValueError is raised, and listeners
        are not notified. Listener notification is not performed on the
        first call to set().
        """

        # Figure out if this is the first time that set() has been called,
        # by testing for the existence of private attributes __lastValid
        # and/or __lastValue.
        #
        # Listener notification is not performed on the first call, in order
        # to overcome a chicken-egg problem caused by the tight coupling
        # between PropertyValue, PropertyBase, and HasProperties objects.
        # The HasProperties._propChanged method is called every time a
        # property value is changed, and it triggers revalidation of all
        # other properties, in case their validity is dependent upon the
        # value of the changed property. But during initialisation, the data
        # structures for every property are created one by one (in
        # HasProperties.__new__), meaning that a call to _propChanged for
        # an early property would fail, as the data for later properties
        # would not yet exist. The simplest solution to this problem is to
        # skip notification the first time that property value is set, which
        # is precisely what we're doing here.
        #
        firstCall = False
        try:
            self.__lastValid = self.__lastValid
        except:
            firstCall = True
            self.__lastValid = False
            self.__lastValue = None

        # Check to see if the new value is valid
        valid = False
        try:
            self._prop.validate(self._owner, newValue)
            valid = True
            
        except ValueError as e:

            # Oops, we don't allow invalid values. This
            # might cause problems on the first call to
            # set(), but it hasn't yet, so I'm leaving
            # as is for the time being.
            if not self._allowInvalid:
                log.debug('Attempt to set {} to an invalid value ({}), '
                          'but allowInvalid is False ({})'.format(
                              self._name, newValue, e)) 
                raise e

        self.__value = newValue
        self.__valid = valid

        # If the value or its validity has not
        # changed, listeners are not notified
        changed = (self.__value != self.__lastValue) or \
                  (self.__valid != self.__lastValid)

        if not changed: return
        
        self.__lastValue = self.__value
        self.__lastValid = self.__valid

        log.debug('Value {} changed: {} ({})'.format(
            self._name,
            newValue,
            'valid' if valid else 'invalid'))

        # Notify any registered listeners
        if not firstCall: self._notify()

        
    def _notify(self):
        """
        Calls the preNotify function (if it is set), any listeners which have
        been registered with this PropertyValue object, and the HasProperties
        owner.
        """
        
        value     = self.__value
        valid     = self.__valid
        listeners = self._changeListeners.items()

        # Call the prenotify function first, if there is one
        if self._preNotifyFunc is not None:
            log.debug('Calling preNotify function for {}'.format(self._name))

            try: self._preNotifyFunc(self._owner, newValue)
            except Exception as e:
                log.debug('PreNotify function on {} raised '
                          'exception: {}'.format(self._name, e)) 

        # Notify all listeners, ignoring any errors -
        # it is up to the listeners to ensure that
        # they handle invalid values
        for (name, func) in listeners:

            log.debug('Notifying listener on {}: {}'.format(self._name, name))
            
            try: func(value, valid, self._owner, self._prop, self._name)
            except Exception as e:
                log.debug('Listener on {} ({}) raised '
                          'exception: {}'.format(self._name, name, e))

        # Notify the property owner that this property has changed
        self._owner._propChanged(self._prop)


    def revalidate(self):
        """
        Revalidates the current property value, and re-notifies
        any registered listeners if the value validity has changed.
        """
        self.set(self.get())

        
    def isValid(self):
        """
        Returns True if the current property value is valid, False otherwise.
        """
        try:               self._prop.validate(self._owner, self.get())
        except ValueError: return False
        return True


class InstanceData(object):
    """
    An InstanceData object is created for every instance which has
    one of these PropertyBase objects as a class attribute. It stores
    references to the property value(s), listener callback functions
    which are notified whenever the property value changes, and the
    property constraints used to test validity.
    """
    def __init__(self, instance, propVal, **constraints):
        self.instance        = instance
        self.propVal         = propVal
        self.changeListeners = OrderedDict()
        self.constraints     = constraints.copy()


class PropertyBase(object):
    """
    The base class for properties. For every HasProperties object which
    has this PropertyBase object as a property, one or more PropertyValue
    instances are created and attached as an attribute of the parent.

    One important point to note is that a PropertyBase object may exist
    without being bound to a HasProperties object (in which case it will
    not create or manage any PropertyValue objects). This is useful if you
    just want validation functionality via the validate(), getConstraint()
    and setConstraint() methods, passing in None for the instance
    parameter. Nothing else will work properly though.

    Subclasses should:

      - Ensure that PropertyBase.__init__ is called.

      - Override the validate method to implement any built in
        validation rules, ensuring that the PropertyBase.validate
        method is called first.

      - Override _makePropVal for properties which consist of
        more than one PropertyValue object
        (see properties_types.List for an example).
    """

    def __init__(self,
                 default=None,
                 required=False,
                 validateFunc=None,
                 preNotifyFunc=None,
                 allowInvalid=True,
                 **constraints):
        """
        Parameters (all optional):
        
          - default:       Default/initial value.
        
          - required:      Boolean determining whether or not this
                           property must have a value. May alternately
                           be a function which accepts one parameter,
                           the owning HasProperties instance, and
                           returns True or False.
        
          - validateFunc:  Custom validation function. Must accept
                           two parameters: a reference to the
                           HasProperties instance, the owner of
                           this property; and the new property
                           value. Should return True if the property
                           value is valid, False otherwise.

          - preNotifyFunc: Function to be called whenever the property
                           value(s) changes. See PropertyValue.__init__.

          - allowInvalid:  If False, a ValueError will be raised on
                           all attempts to set this property to an
                           invalid value. This does not guarantee that
                           the property value will never be invalid -
                           see caveats in PropertyValue.__init__
                           docstring.
        
          - constraints:   Type specific constraints used to test
                           validity.
        """

        # The _label attribute is set byt the PropertyOwner
        # metaclass when a new HasProperties class is defined
        self._label              = None
        self._default            = default
        self._required           = required
        self._validateFunc       = validateFunc
        self._preNotifyFunc      = preNotifyFunc
        self._allowInvalid       = allowInvalid
        self._defaultConstraints = constraints

        
    def addListener(self, instance, name, callback):
        """
        Register a listener with this property. When the property value(s)
        or their validity managed by this PropertyBase object changes, the
        listener will be notified. See PropertyValue.addListener for
        required callback function signature.
        """
        log.debug('Adding listener on {}: {}'.format(self._label, name))
        fullname = 'PropertyBase_{}_{}'.format(self._label, name)
        self._getInstanceData(instance).changeListeners[fullname] = callback
        
        
    def removeListener(self, instance, name):
        """
        De-register the named listener from this property.
        """
        fullname = 'PropertyBase_{}_{}'.format(self._label, name)
        log.debug('Removing listener on {}: {}'.format(self._label, name))
        self._getInstanceData(instance).changeListeners.pop(fullname)

        
    def getConstraint(self, instance, constraint):
        """
        Returns the value of the named constraint for the specified instance,
        or the default constraint value if instance is None.
        """

        if instance is None:
            return self._defaultConstraints[constraint]
        else:
            return self._getInstanceData(instance).constraints.get(
                constraint, None)


    def setConstraint(self, instance, constraint, value):
        """
        Sets the value of the named constraint for the specified instance,
        or the default value if instance is None.
        """
        
        log.debug('Changing {} constraint on {}: {} = {}'.format(
            self._label,
            'default' if instance is None else 'instance',
            constraint,
            value))

        if instance is None:
            self._defaultConstraints[constraint] = value
        else:
            self._getInstanceData(instance).constraints[constraint] = value


    def getPropVal(self, instance):
        """
        Return the PropertyValue object(s) for this property, associated
        with the given HasProperties instance, or None if there is no
        value for the given instance.
        """
        instData = self._getInstanceData(instance)
        
        if instData is not None: return instData.propVal
        else:                    return None
 

    def _getInstanceData(self, instance):
        """
        Returns the InstanceData object for the given instance, or None
        if there is no InstanceData for the given instance.
        """
        return instance.__dict__.get(self._label, None)

        
    def __newInstance(self, instance):
        """
        Creates an InstanceData object for the new instance, stores it
        as an attribute of the instance (with name self._label), and
        returns it.
        """

        propVal  = self._makePropVal(instance)
        instData = InstanceData(instance,
                                propVal,
                                **self._defaultConstraints)

        # Order here is important - the instanceData object must be
        # added as an attribute of the instance before we attempt to
        # set the property value, as this would otherwise result in
        # an attempt to look up the instanceData object on the
        # instance! This is also why the PropertyValue.__init__
        # method does not allow an initial value to be set.
        instance.__dict__[self._label] = instData

        # TODO not supporting multiple property values here
        propVal.set(self._default)

        # A PropertyBase object registers an 'internal' listener
        # on every PropertyValue object that it manages, purely
        # so that the PropertyBase object can propagate value
        # changes onto its own listeners.
        propVal.addListener('internal', self.__varChanged) 

        return instData

    
    def _makePropVal(self, instance):
        """
        Creates and returns PropertyValue object for the given instance.
        Subclasses which encapsulate multiple values should override this
        method, and return a list of PropertyValue instances.
        """
        return PropertyValue(self,
                             instance,
                             self._label,
                             self._preNotifyFunc,
                             self._allowInvalid)

        
    def __varChanged(self, value, valid, instance, prop, name):
        """
        This function is registered with the PropertyValue object (or
        objects) which are managed by this PropertyBase instance.
        It notifies any listeners which have been registered to
        this property of any value changes.
        """

        listeners = self._getInstanceData(instance).changeListeners.items()

        for (lName, func) in listeners:
            log.debug('Notifying listener on {}: {}'.format(self._label,
                                                            lName))
            try:
                func(value, valid, instance, prop, name)
            except Exception as e:
                log.debug('Listener on {} ({}) raised exvception: {}'.format(
                    self._label, lName, e))

            
    def validate(self, instance, value):
        """
        Called when an attempt is made to set the property value on
        the given instance. The sole purpose of PropertyBase.validate
        is to determine whether a given value is valid or invalid; it
        should not do anything else. In particular, it should not
        modify any other property values on the instance, as bad
        things would happen.
        
        If the given value is invalid, subclass implementations
        should raise a ValueError containing a useful message as to
        why the value is invalid. Otherwise, they should not return
        any value.  The default implementation does nothing, unless
        a custom validate function, and/or required=True, was passed
        to the constructor. If required is True, and the value is
        None, a ValueError is raised. If a custom validate function
        was set, it is called and, if it returns False, a ValueError
        is raised. It may also raise a ValueError of its own for
        invalid values.

        Subclasses which override this method should therefore call
        this superclass implementation in addition to performing
        their own validation.
        """

        # a value is required
        if (self._required is not None) and (value is None):

            # required may either be a boolean value
            if isinstance(self._required, bool):
                if self._required:
                    raise ValueError('A value is required')

            # or a function
            elif self._required(instance):
                raise ValueError('A value is required')

        # a custom validation function has been provided
        if self._validateFunc is not None:
            if not self._validateFunc(instance, value):
                raise ValueError('Value does not meet custom validation rules')

        
    def revalidate(self, instance):
        """
        Forces validation of this property value, for the current instance.
        This will result in any registered listeners being notified, but only
        if the validity of the value has changed.
        """

        propVals = self.getPropVal(instance)

        # getPropVal should return either a
        # PropertyValue object, or a list of them
        if isinstance(propVals, PropertyValue):
            propVals = [propVals]

        for val in propVals:
            val.revalidate()

            
    def __get__(self, instance, owner):
        """
        If called on the HasProperties class, and not on an instance,
        returns this PropertyBase object. Otherwise, returns the value(s)
        contained in the PropertyValue variable(s) which is(are) attached
        to the instance.
        """

        if instance is None:
            return self

        instData = self._getInstanceData(instance)

        if instData is None:
            instData = self.__newInstance(instance)

        if isinstance(instData.propVal, PropertyValue):
            return instData.propVal.get()
        else:
            return [propVal.get() for propVal in instData.propVal]

        
    def __set__(self, instance, value):
        """
        Set the value of this property, as attached to the given
        instance, to the given value.  
        """
        
        propVals = self.getPropVal(instance)

        if isinstance(propVals, PropertyValue):
            propVals.set(value)
        else:
            for propVal, val in zip(propVals, value):
                propVal.set(val)


class PropertyOwner(type):
    """
    Metaclass for classes which contain PropertyBase objects.  
    Sets PropertyBase labels from the class attribute names.
    """
    def __new__(cls, name, bases, attrs):
        for n, v in attrs.items():
            if isinstance(v, PropertyBase):
                v._label = n
                
        return super(PropertyOwner, cls).__new__(cls, name, bases, attrs)


class HasProperties(object):
    """
    Base class for classes which contain PropertyBase objects.
    All classes which contain PropertyBase objects must subclass
    this class.
    """
    __metaclass__ = PropertyOwner

    
    def __new__(cls, *args, **kwargs):
        """
        Here we create a new HasProperties instance, and loop through all
        of its PropertyBase properties to ensure that they are initialised.
        """
        
        inst = super(HasProperties, cls).__new__(cls, *args, **kwargs)
        for attr, value in inst.__class__.__dict__.items():
            if isinstance(value, PropertyBase):

                # all we need to do is access the property to force
                # its initialisation - see PropertyBase.__get__
                value.__get__(inst, cls)

        return inst
        
        
    def getProp(self, propName):
        """
        Return the PropertyBase object for the given property.
        """
        return getattr(self.__class__, propName)


    def getPropVal(self, propName):
        """
        Return the PropertyValue object(s) for the given property. 
        """
        return self.getProp(propName).getPropVal(self)


    def getConstraint(self, propName, constraint):
        """
        Convenience method, returns the value of the named constraint for the
        named property. See PropertyBase.setConstraint.
        """
        return self.getProp(propName).getConstraint(self, constraint)

        
    def setConstraint(self, propName, constraint, value):
        """
        Convenience method, sets the value of the named constraint for the
        named property. See PropertyBase.setConstraint.
        """ 
        return self.getProp(propName).setConstraint(self, constraint, value) 


    def addListener(self, propName, listenerName, callback):
        """
        Convenience method, adds the specified listener to the specified
        property. See PropertyBase.addListener.
        """
        self.getProp(propName).addListener(self, listenerName, callback)

        
    def removeListener(self, propName, listenerName):
        """
        Convenience method, removes the specified listener from the specified
        property. See PropertyBase.addListener.
        """
        self.getProp(propName).removeListener(self, listenerName)

        
    def getAllProperties(self):
        """
        Returns two lists, the first containing the names of all
        properties of this object, and the second containing the
        corresponding PropertyBase objects.
        """

        props = filter(
            lambda (name, prop): isinstance(prop, PropertyBase),
            self.__class__.__dict__.items())
    
        propNames, props = zip(*props)

        return propNames, props


    def isValid(self, propName):
        """
        Returns True if the current value of the specified property
        is valid, False otherwise.
        """
        # TODO not supporting lists here
        return self.getPropVal(propName).isValid()

        
    def validateAll(self):
        """
        Validates all of the properties of this HasProperties object.
        A list of tuples is returned, with each tuple containing a
        property name, and an associated error string. The error string
        is a message about the property which failed validation. If all
        property values are valid, the returned list will be empty.
        """

        names, props = self.getAllProperties()

        errors = []

        for name, prop in zip(names, props):
            
            try:
                val = getattr(self, name)
                prop.validate(self, val)
                
            except ValueError as e:
                errors.append((name, e.message))

        return errors

        
    def _propChanged(self, changedProp):
        """
        Called whenever any property value changes. Forces validation
        for all other properties, and notification of their registered
        listeners, if their value or validity has changed. This is done
        because the validity of some properties may be dependent upon
        the values of others. So when a particular property value
        changes, it may have changed the validity of another property,
        meaning that the listeners of the latter property need to be
        notified of this change in validity.
        """
        propNames, props = self.getAllProperties()

        for prop in props:
            if prop != changedProp:
                prop.revalidate(self)
        
        
    def __str__(self):
        """
        Returns a multi-line string containing the names and values
        of all the properties of this object.
        """
        
        clsname = self.__class__.__name__

        propNames, props = self.getAllProperties()

        propVals = ['{}'.format(getattr(self, propName))
                    for propName in propNames]

        maxNameLength = max(map(len, propNames))

        lines = [clsname]

        for propName, propVal in zip(propNames, propVals):
            fmtStr = '  {:>' + str(maxNameLength) + '} = {}'
            lines.append(fmtStr.format(propName, propVal))
            
        return '\n'.join(lines)


from properties_types import * 
