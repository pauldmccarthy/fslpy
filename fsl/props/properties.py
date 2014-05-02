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
# a PropertyValue or PropertyValueList (see properties_value.py) object is
# created for each of the PropertyBase instances. 
#
#
# Each of these PropertyValue instances encapsulates a single value, of any
# type (a PropertyValueList instance encapsulates multiple PropertyValue
# instances).  Whenever a variable value changes, the PropertyValue instance
# passes the new value to the validate method of its parent PropertyBase
# instance to determine whether the new value is valid, and notifies any
# registered listeners of the change. The PropertyValue object will allow its
# underlying value to be set to something invalid, but it will tell registered
# listeners whether the new value is valid or invalid (PropertyValue objects
# can alternately be configured to raise a ValueError on an attempt to set
# them to an invalid value, but this has some caveats - see the
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
        self.constraints     = constraints.copy()


class PropertyBase(object):
    """
    The base class for properties. For every HasProperties object which
    has this PropertyBase object as a property, one InstanceData object
    is created and attached as an attribute of the parent.

    One important point to note is that a PropertyBase object may exist
    without being bound to a HasProperties object (in which case it will
    not create or manage a PropertyValue object). This is useful if you
    just want validation functionality via the validate(), getConstraint()
    and setConstraint() methods, passing in None for the instance
    parameter. Nothing else will work properly though.

    Subclasses should:

      - Ensure that PropertyBase.__init__ is called.

      - Override the validate method to implement any built in
        validation rules, ensuring that the PropertyBase.validate
        method is called first.

      - Override _cast for implicit casting/conversion logic (see
        properties_types.Boolean for an example).
    """

    def __init__(self,
                 default=None,
                 validateFunc=None,
                 preNotifyFunc=None,
                 required=False,
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
        Register a listener with this the PropertyValue object managed by this
        property. 
        """
        self._getInstanceData(instance).propVal.addListener(name, callback)
        
        
    def removeListener(self, instance, name):
        """
        De-register the named listener from the PropertyValue object managed
        by this property.
        """
        self._getInstanceData(instance).propVal.removeListener(name)

        
    def getConstraint(self, instance, constraint):
        """
        Returns the value of the named constraint for the specified instance,
        or the default constraint value if instance is None.
        """
        instData = self._getInstanceData(instance)
        
        if instData is None:
            return self._defaultConstraints[constraint]

        return instData.constraints.get(constraint, None)


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

        instData = self._getInstanceData(instance)

        if instData is None: self._defaultConstraints[constraint] = value
        else:                instData.constraints[    constraint] = value


    def getPropVal(self, instance):
        """
        Return the PropertyValue object(s) for this property, associated
        with the given HasProperties instance, or None if there is no
        value for the given instance.
        """
        instData = self._getInstanceData(instance)
        if instData is None: return None
        return instData.propVal


    def _getInstanceData(self, instance):
        """
        Returns the InstanceData object for the given instance, or None
        if there is no InstanceData for the given instance. An InstanceData
        object, which provides a binding between a PropertyBase object and
        a  HasProperties instance, is created by that HasProperties
        instance when it is created (see HasProperties.__new__).
        """
        return instance.__dict__.get(self._label, None)

        
    def _makePropVal(self, instance):
        """
        Creates and returns PropertyValue object for the given instance.
        Subclasses which encapsulate multiple values should override this
        method, and return a PropertyValueList object instead.
        """
        return PropertyValue(instance,
                             name=self._label,
                             value=self._default,
                             castFunc=self._cast,
                             validateFunc=self.validate,
                             preNotifyFunc=self._preNotifyFunc,
                             postNotifyFunc=self._valChanged,
                             allowInvalid=self._allowInvalid)

        
    def _valChanged(self, instance, value, valid):
        """
        This function is called by PropertyValue objects which are
        managed by this PropertyBase object. It notifies any listeners
        which have been registered to this property of any value changes.
        """

        instData = self._getInstanceData(instance)

        if instData is None: return

        # Force validation for all other properties of the instance, and
        # notification of their registered listeners, This is done because the
        # validity of some properties may be dependent upon the values of this
        # one. So when the value of this property changes, it may have changed
        # the validity of another property, meaning that the listeners of the
        # latter property need to be notified of this change in validity.

        #
        # I don't like this here. It should be in HasProperties. Any reason
        # against the HasProperties instance registering an 'internal' listener
        # with every property?
        #
        propNames, props = instance.getAllProperties()
        for prop in props:
            if prop is not self:
                prop.revalidate(instance) 

            
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

        propVal = self.getPropVal(instance)
        propVal.revalidate()

            
    def __get__(self, instance, owner):
        """
        If called on the HasProperties class, and not on an instance,
        returns this PropertyBase object. Otherwise, returns the value
        contained in the PropertyValue variable which is attached
        to the instance.
        """

        if instance is None:
            return self
            
        instData = self._getInstanceData(instance)
        return instData.propVal.get()

        
    def _cast(self, value):
        return value

        
    def __set__(self, instance, value):
        """
        Set the value of this property, as attached to the given
        instance, to the given value.  
        """
        
        propVal = self.getPropVal(instance)
        value   = self._cast(value)
        propVal.set(value)


class ListPropertyBase(PropertyBase):
    """
    PropertyBase for properties which encapsulate more than one value.
    """
    
    def __init__(self, listType, **kwargs):
        """
        """
        PropertyBase.__init__(self, **kwargs)
        self._listType = listType

    def _makePropVal(self, instance):
        """
        """
        return PropertyValueList(
            instance,
            name=self._label, 
            values=self._default,
            itemCastFunc=self._listType._cast,
            itemValidateFunc=self._listType.validate,
            listValidateFunc=self.validate,
            itemAllowInvalid=self._listType._allowInvalid,
            listAllowInvalid=self._allowInvalid,
            postNotifyFunc=self._valChanged)

    def getPropValList(self, instance):
        return self.getPropVal(instance).getPropertyValueList()

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
        
        instance = super(HasProperties, cls).__new__(cls, *args, **kwargs)

        props = instance.__class__.__dict__.items()
        
        for propName, prop in props:
            if not isinstance(prop, PropertyBase): continue

            # Create a PropertyValue and an InstanceData
            # object, which bind the PropertyBase object
            # to this HasProperties instance.
            propVal  = prop._makePropVal(instance)
            instData = InstanceData(instance,
                                    propVal,
                                    **prop._defaultConstraints)

            # Store the InstanceData object
            # on the instance itself
            instance.__dict__[propName] = instData

        # Perform validation of the initial
        # value for each property
        for propName, prop in props:
            if isinstance(prop, PropertyBase): 
                prop.revalidate(instance)

        return instance

        
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

        prop   = self.getProp(propName)
        curVal = getattr(self, propName)
        try: prop.validate(self, curVal)
        except ValueError: return False

        return True

        
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
from properties_value import * 
