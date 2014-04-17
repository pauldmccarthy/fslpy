#!/usr/bin/env python
#
# properties.py - Python descriptors of various types.
#
# This module should not be imported directly - import the fsl.props
# package instead. Property type definitions are in properties_types.py.
#
# Usage:
#
#     import Tkinter as tk
#     import tkprops as tkp
#
#
#     class PropObj(tkp.HasProperties):
#         myProperty = tkp.Boolean()
#
#
#     # The Tk root object must be created
#     # before any HasProperties objects.
#     app       = tk.Tk()
#     myPropObj = PropObj()
#
#
#     # Access the property value as a normal attribute:
#     myPropObj.myProperty = True
#     myPropObj.myProperty
#
#     # >>> True
#
#
#     # access the tkp.Boolean instance:
#     myPropObj.getTkProp('myProperty')
#
#     # >>> <tkprops.tkprop.Boolean at 0x1045e2710>
#
#
#     # access the underlying Tkinter control variable
#     # (there are caveats for List properties):
#     myPropObj.getTkVar('myProperty').tkVar
#
#     # >>> <tkinter.BooleanVar instance at 0x1047ef518>
#
#
#     # Receive notification of property value changes
#     def myPropertyChanged(instance, name, value):
#         print('New value for {}: {}'.format(name, value))
#
#     PropObj.myProperty.addListener(
#         myPropObj, 'myListener', myPropertyChanged)
# 
#     myPropObj.myProperty = False
#
#     # >>> New value for myProperty: False
#
#
#     # Remove a previously added listener
#     PropObj.myProperty.removeListener(myPropObj, 'myListener')
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
# Once you know how Python descriptors work, you then need to know how
# Tk control variables work. These are simple objects which may be
# passed to a Tkinter widget object when it is created. When a user
# modifies the widget value, the Tk control variable is
# modified. Conversely, if the value of a Tk control variable object is
# modified, any widgets which are bound to the variable are updated to
# reflect the new value.
#
# This module, and the associated tkpropwidget module, uses magic to
# encapsulate Tkinter control variables within python descriptors, thus
# allowing custom validation rules to be enforced on such control
# variables.
#
# The runtime structure of Tk properties is organised as follows:
#
# A HasProperties (sub)class contains a collection of PropertyBase
# instances. When an instance of the HasProperties class is created, one
# or more TkVarProxy objects are created for each of the PropertyBase
# instances. For most properties, there is a one-to-one mapping between
# TkVarProxy instances and PropertyBase instances (for each
# HasProperties instance), however this is not mandatory.  For example,
# the List property manages multiple TkVarProxy objects for each
# HasProperties instance.

# Each of these TkVarProxy instances encapsulates a single Tkinter
# control variable.  Whenever a variable value changes, the TkVarProxy
# instance passes the new value to the validate method of its parent
# PropertyBase instance to determine whether the new value is valid, and
# notifies any registered listeners of the change. The TkVarProxy object
# will allow its underlying Tkinter variable to be given invalid values,
# but it will tell registered listeners whether the new value is valid
# or invalid.
#
# Application code may be notified of property changes in two ways.
# First, a listener may be registered with a PropertyBase object, by
# passing a reference to the HasProperties instance, a name, and a
# callback function to the PropertyBase.addListener method.  Such a
# listener will be notified of changes to any of the TkVarProxy objects
# managed by the PropertyBase object, and associated with the
# HasProperties instance. This is important for List properties, as it
# means that a change to a single TkVarProxy object in a list will
# result in notification of all registered listeners.
#
# If one is interested in changes to a single TkVarProxy object
# (e.g. one element of a List property), then a listener may be
# registered directly with the TkVarProxy object. This listener will
# then only be notified of changes to that TkVarProxy object.
#
# author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import types
import logging

from collections import OrderedDict

log = logging.getLogger(__name__)


class PropertyValue(object):
    """
    Proxy object which encapsulates a single value for a property.
    One or more PropertyValue objects is created for every property
    of a HasProperties instance.
    """

    def __init__(self, prop, owner, value, name=None):
        """
        Parameters:
        
          - prop:  The PropertyBase object which manages this
                   PropertyValue.
          - owner: The HasProperties object, the owner of the
                   prop property.
          - value: Initial value.
          - name:  Variable name - if not provided, a default,
                   unique name is created.
        """
        
        if name is None: name = '{}_{}'.format(prop.label, id(self))
        
        self.prop            = prop
        self.owner           = owner
        self.name            = name
        self.changeListeners = OrderedDict()
        self._value          = value
        self._lastValue      = value
        self._lastValid      = self.isValid()


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

        log.debug('Adding listener on {}: {}'.format(self.name, name))

        name = 'PropertyValue_{}_{}'.format(self.name, name)

        # Save a reference to the listener callback function
        self.changeListeners[name] = callback


    def removeListener(self, name):
        """
        Removes the listener with the given name from the specified
        instance.
        """

        log.debug('Removing listener on {}: {}'.format(self.name, name))

        name = 'PropertyValue_{}_{}'.format(self.name, name)
        
        self.changeListeners[instance].pop(name, None)

        
    def get(self):
        """
        Returns the current property value.
        """
        return self._value

        
    def set(self, newValue):
        """
        Sets the property value. The property is validated, and any
        registered listeners are notified.
        """

        self._value = newValue

        log.debug('Variable {} changed: {}'.format(self.name, newValue))

        # Call the PropertyBase prenotify function first, if there is one
        if self.prop.preNotifyFunc is not None:
            log.debug('Calling preNotify function for {}'.format(self.name))
            self.prop.preNotifyFunc(self.owner, newValue)

        # Validate the new value and notify any registered listeners
        self.validateAndNotify()
            
        # Notify the property owner that this property has changed
        self.owner._propChanged(self.prop)

        
    def isValid(self):
        """
        Returns True if hte current property value is valid, False
        otherwise. Does not trigger notification of any listeners
        which have been registered with this PropertyValue object.
        """

        try:    self.prop.validate(self.owner, self.get())
        except: return False

        return True

        
    def validateAndNotify(self):
        """
        Passes the current value to the validate() method
        of the PropertyBase object which owns this PropertyValue.
        If the value, or the validity of that value, has changed
        since the last validation, any listeners which have been
        registered with this PropertyValue object are notified.
        """
        
        value     = self.get()
        valid     = self.isValid()
        listeners = self.changeListeners.items()

        # Listeners are only notified if the value or its
        # validity has changed since the last validation
        if (value == self._lastValue) and (valid == self._lastValid):
            return

        self._lastValue = value
        self._lastValid = valid

        # Notify all listeners, ignoring any errors -
        # it is up to the listeners to ensure that
        # they handle invalid values
        for (name,func) in listeners:

            log.debug('Notifying listener on {}: {}'.format(self.name, name))
            
            try: func(value, valid, self.owner, self.prop, self.name)
            except Exception as e:
                log.debug('Listener on {} ({}) raised exception: {}'.format(
                    self.name, name, e))


class PropertyBase(object):
    """
    The base class for properties. For every object which has this
    PropertyBase object as a property, one or more PropertyValue
    instances are created and attached as an attribute of the parent.

    Subclasses should:

      - Ensure that PropertyBase.__init__ is called.

      - Override the validate method to implement any built in
        validation rules, ensuring that the PropertyBase.validate
        method is called first.

      - Override __get__ and __set__ for any required implicit
        casting/data transformation rules.

      - Override _makePropVal if creation of the PropertyValue
        needs to be controlled.

      - Override getPropVal for properties which consist of
        more than one PropertyValue object
        (see properties_types.List for an example).

      - Override whatever you want for advanced usage (see
        properties_types.List for an example).

    """
    
    def __init__(self,
                 default=None,
                 required=False,
                 validateFunc=None,
                 preNotifyFunc=None):
        """
        Parameters:
        
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
                           value(s) changes. This function is called
                           by the PropertyValue object(s) before any
                           listeners are notified.
        """
        self.label             = None
        self.default           = default
        self.required          = required
        self.validateFunc      = validateFunc
        self.preNotifyFunc     = preNotifyFunc
        self.changeListeners   = OrderedDict()

        
    def addListener(self, instance, name, callback):
        """
        Register a listener with this property. When the property value
        changes, the listener will be notified. See PropertyValue.addListener
        for required callback function signature.
        """

        if instance not in self.changeListeners:
            self.changeListeners[instance] = {}

        log.debug('Adding listener on {}: {}'.format(self.label, name))

        fullname = 'PropertyBase_{}_{}'.format(self.label, name)

        self.changeListeners[instance][fullname] = callback

        
    def removeListener(self, instance, name):
        """
        De-register the named listener from this property.
        """

        fullname = 'PropertyBase_{}_{}'.format(self.label, name)

        if instance not in self.changeListeners:           return
        if fullname not in self.changeListeners[instance]: return

        log.debug('Removing listener on {}: {}'.format(self.label, name))

        self.changeListeners[instance].pop(fullname)

        
    def forceValidation(self, instance):
        """
        Forces validation of this property value, for the current instance.
        This will result in any registered listeners being notified.
        """

        propVals = instance.getPropVal(self.label)

        # getPropVal returns either a PropertyValue object,
        # or a list of them (it should do, anyway).
        if isinstance(propVals, PropertyValue):
            propVals = [propVals]

        for val in propVals:
            val.validateAndNotify()

        
    def _varChanged(self, value, valid, instance, prop, name):
        """
        This function is registered with the PropertyValue object (or
        objects) which are managed by this PropertyBase instance.
        It notifies any listeners which have been registered to
        this property, (and to the associated HasProperties instance).
        """

        if instance not in self.changeListeners: return
        
        listeners = self.changeListeners[instance].items()

        for (lName, func) in listeners:
            
            log.debug('Notifying listener on {}: {}'.format(self.label, lName))
            func(value, valid, instance, prop, name)

    
    def _makePropVal(self, instance):
        """
        Creates a PropertyValue object, and attaches it to the given
        instance.  Also registers this PropertyBase instance as a
        listener on the PropertyValue object.
        """

        instval = PropertyValue(self, instance, self.default, self.label)
        instance.__dict__[self.label] = instval

        instval.addListener('internal', self._varChanged)

        return instval


    def getPropVal(self, instance):
        """
        Return the PropertyValue object (or objects) for this property,
        associated with the given HasProperties instance. Properties
        which contain multiple PropertyValue objects should override
        this method to return a list of said objects.
        """
        return instance.__dict__.get(self.label, None)

        
    def validate(self, instance, value):
        """
        Called when an attempt is made to set the property value on
        the given instance. If the given value is invalid, subclass
        implementations should raise a ValueError. Otherwise, they
        should not return any value.  The default implementation
        does nothing, unless a custom validate function was passed
        to the constructor, in which case it is called. Subclasses
        which override this method should therefore call this
        superclass implementation in addition to performing their
        own validation.
        """

        # a value is required
        if (self.required is not None) and (value is None):

            # required may either be a boolean value
            if isinstance(self.required, bool):
                if self.required:
                    raise ValueError('A value is required')

            # or a function
            elif self.required(instance):
                raise ValueError('A value is required')

        if self.validateFunc is not None:
            if not self.validateFunc(instance, value):
                raise ValueError('Value does not meet custom validation rules')

            
    def __get__(self, instance, owner):
        """
        If called on the HasProperties class, and not on an instance,
        returns this PropertyBase object. Otherwise, returns the value
        contained in the PropertyValue variable which is attached to the
        instance.
        """

        if instance is None:
            return self

        instval = self.getPropVal(instance)
        
        if instval is None: instval = self._makePropVal(instance)

        return instval.get()

        
    def __set__(self, instance, value):
        """
        Set the value of this property, as attached to the given
        instance, to the given value.  
        """


        instval = self.getPropVal(instance)
        instval.set(value)
            

class PropertyOwner(type):
    """
    Metaclass for classes which contain PropertyBase objects.  
    Sets PropertyBase labels from the class attribute names.
    """
    def __new__(cls, name, bases, attrs):
        for n, v in attrs.items():
            if isinstance(v, PropertyBase):
                v.label = n
                
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
            lambda (name,prop): isinstance(prop, PropertyBase),
            self.__class__.__dict__.items())
    
        propNames, props = zip(*props)

        return propNames, props


    def isValid(self, propName):
        """
        Returns True if the current value of the specified property
        is valid, False otherwise.
        """
        return self.getPropVal(propName).isValid()

        
    def validateAll(self):
        """
        Validates all of the properties of this HasProperties object.
        A list of tuples is returned, with each tuple containing a
        property name, and an associated error string. The error
        string is a  message about the property which failed
        validation. If all property values are valid, the returned
        list will be empty.
        """

        names, props = self.getAllProperties()

        errors = []

        for name, prop in zip(names,props):
            
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
        changes, it may ahve changed the validity of another property,
        meaning that the listeners of the latter property need to be
        notified of this change in validity.
        """
        propNames, props = self.getAllProperties()

        for prop in props:
            if prop == changedProp: continue
            prop.forceValidation(self)
        
        
    def __str__(self):
        """
        Returns a multi-line string containing the names and values
        of all the properties of this object.
        """
        
        clsname = self.__class__.__name__

        propNames,props = self.getAllProperties()

        propVals = ['{}'.format(getattr(self, propName))
                    for propName in propNames]

        maxNameLength = max(map(len, propNames))

        lines = [clsname]

        for propName,propVal in zip(propNames,propVals):
            fmtStr = '  {:>' + str(maxNameLength) + '} = {}'
            lines.append(fmtStr.format(propName, propVal))
            
        return '\n'.join(lines)


from properties_types import * 
