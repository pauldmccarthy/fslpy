#!/usr/bin/env python
#
# properties.py - Tkinter control variables encapsulated inside Python
# descriptors.
#
# This module should not be imported directly - import the tkprops
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

import logging as log
import Tkinter as tk


class TkVarProxy(object):
    """
    Proxy object which encapsulates a Tkinter control variable.  One or
    more TkVarProxy objects is created for every property of a
    HasProperties instance.
    """

    def __init__(self, tkProp, owner, tkVarType, value, name=None):
        """
        Creates an instance of the specified tkVarType, and sets a
        trace on it.
        
        Parameters:
        
          - tkProp:    The PropertyBase object which manages this
                       TkVarProxy.
          - owner:     The HasProperties object, the owner of the
                       tkProp property.
          - tkVarType: The type of Tkinter control variable that
                       this TkVarProxy encapsulates.
          - value:     Initial value.
          - name:      Variable name - if not provided, a default,
                       unique name is created.

        """
        
        if name is None: name = '{}_{}'.format(tkProp.label, id(self))
        
        self.tkVarType       = tkVarType
        self.tkProp          = tkProp
        self.owner           = owner
        self.lastValue       = value
        self.changeListeners = {}
        self.name            = name
        self.tkVar           = tkVarType(value=value, name=name)
        self.traceName       = self.tkVar.trace('w', self._traceCb)


    def addListener(self, name, callback):
        """
        Adds a listener for this variable. When the variable value
        changes, the listener callback function is called. The
        callback function must accept these arguments:

          value    - The new property value
          valid    - Whether the new value is valid or invalid
          instance - The HasProperties instance
          tkProp   - The PropertyBase instance
          name     - The name of this TkVarProxy

        If you are only interested in the value, you can define your
        callback function like 'def callback(value, *a): ...'
        """

        log.debug('Adding listener on {}: {}'.format(self.name, name))

        # Save a reference to the listener callback function
        self.changeListeners[name] = callback


    def removeListener(self, name):
        """
        Removes the listener with the given name from the specified
        instance.
        """

        log.debug('Removing listener on {}: {}'.format(self.name, name))
        
        self.changeListeners[instance].pop(name, None)

        
    def _traceCb(self, *args):
        """
        Called whenever the Tkinter control variable value is changed.
        The PropertyBase.validate() method is called on the parent
        property of this TkVarProxy object. If this validate method
        does not raise an error, the new value is stored as the last
        known good value. If the validate method does raise an error,
        the last known good value is not changed. The variable can
        be reverted to its last known good value via the revert
        method.
        
        After the PropertyBase.validate method is called, any registered
        listeners are notified of the variable value change.
        """

        valid     = True
        listeners = self.changeListeners.items()

        # This is silly. Tkinter allows Boolean/Int/Double
        # variables to be set to invalid values (e.g. it
        # allows DoubleVars to be set to strings containing
        # non numeric characters). But then, later calls to
        # get() will fail, as they will attempt to convert
        # the invalid value to a boolean/int/double. So here
        # we attempt to get the current value in the normal
        # way ...
        try:    newValue = self.tkVar.get()

        # and if that fails, we manually look up the value
        # via the current tk context, thus avoiding the
        # failing type cast. Ugly.
        except: newValue = self.tkVar._tk.globalgetvar(self.name)

        # More silliness related to above silliness. All
        # variables in Tk, be they IntVars, BooleanVars, or
        # whatever, are stored as strings, and cannot have no
        # value. If you try to set a Tk variable to None, it
        # will be converted to a string, and stored as 'None',
        # which is quite different. So I'm following the
        # convention that an empty string, for any of the 
        # variable types, is equivalent to None. 
        if newValue == '':
            newValue = None

        # print a log message if the value has changed
        if newValue != self.lastValue:
            log.debug(
                'Variable {} changed: {} (valid: {}, {} listeners)'.format(
                    self.name, newValue, valid, len(listeners)))

        # if the new value is valid, save
        # it as the last known good value
        try:
            self.tkProp.validate(self.owner, newValue)
            self.lastValue = newValue

        except ValueError:
            valid = False

        # Notify all listeners about the change, ignoring
        # any errors - it is up to the listeners to ensure
        # that they handle invalid values
        for (name,func) in listeners:

            log.debug('Notifying listener on {}: {}'.format(self.name, name))
            
            try: func(newValue, valid, self.owner, self.tkProp, self.name)
            except Exception as e:
                log.debug('Listener on {} ({}) raised exception: {}'.format(
                    self.name, name, e))


    def revert(self):
        """
        Sets the Tk variable to its last known good value. This will
        result in any registered listeners being notified of the change.
        """
        self.tkVar.set(self.lastValue)


    def __del__(self):
        """
        Remove the trace on the Tkinter variable.
        """
        self.tkVar.trace_vdelete('w', self.traceName)
        

class PropertyBase(object):
    """
    The base class for properties.  Subclasses should:

      - Ensure that PropertyBase.__init__ is called.

      - Override the validate method to implement any built in
        validation rules, ensuring that the PropertyBase.validate
        method is called.

      - Override __get__ and __set__ for any required implicit
        casting/data transformation rules (see
        properties_types.String for an example).

      - Override _makeTkVar if creation of the TkVarProxy needs
        to be controlled (see properties_types.Choice for an
        example).

      - Override getTkVar for properties which consist of
        more than one TkVarProxy object
        (see properties_types.List for an example).

      - Override whatever you want for advanced usage (see
        properties_types.List for an example).
    """
    
    def __init__(self, tkVarType, default, required=False, validateFunc=None):
        """
        The tkvartype parameter should be one of the Tkinter.*Var
        classes.  For every object (the parent) which has this
        PropertyBase object as a property, one or more TkVarProxy
        instances are created and attached as an attribute of the
        parent. Parameters:
        
          - tkVarType:    Tkinter control variable class. May be
                          None for properties which manage multiple
                          TkVarProxy objects.
        
          - default:      Default/initial value.
        
          - required:     Boolean determining whether or not this
                          property must have a value. May alternately
                          be a function which accepts one parameter,
                          the owning HasProperties instance, and
                          returns True or False.
        
          - validateFunc: Custom validation function. Must accept
                          two parameters:a reference to the
                          HasProperties instance, the owner of
                          this property; and the new property
                          value. Should raise a ValueError if the
                          new value is invalid.
        """
        self.label             = None
        self.tkVarType         = tkVarType
        self.default           = default
        self.required          = required
        self.validateFunc      = validateFunc
        self.changeListeners   = {}

        
    def addListener(self, instance, name, callback):
        """
        Register a listener with this property. When the property value
        changes, the listener will be notified. See TkVarProxy.addListener
        for required callback function signature.
        """

        if instance not in self.changeListeners:
            self.changeListeners[instance] = {}

        log.debug('Adding listener on {}: {}'.format(self.label, name))

        self.changeListeners[instance][name] = callback

        
    def removeListener(self, instance, name):
        """
        De-register the named listener from this property.
        """

        if instance not in self.changeListeners:           return
        if name     not in self.changeListeners[instance]: return

        log.debug('Removing listener on {}: {}'.format(self.label, name))

        self.changeListeners[instance].pop(name)

        
    def forceValidation(self, instance):
        """
        Forces validation of this property value, for the current instance.
        This will result in any registered listeners being notified.
        """

        varProxies = instance.getTkVar(self.label)

        # getTkVar returns either a TkVarProxy object, or a
        # list of TkVarProxy objects (it should do, anyway).
        if isinstance(varProxies, TkVarProxy):
            varProxies = [varProxies]

        for var in varProxies:
            var._traceCb()

        
    def _varChanged(self, value, valid, instance, tkProp, name):
        """
        This function is registered with the TkVarProxy object (or
        objects) which are managed by this PropertyBase instance.
        It notifies any listeners which have been registered to
        this property, (and to the associated HasProperties instance).
        """

        if instance not in self.changeListeners: return
        
        listeners = self.changeListeners[instance].items()

        for (lName, func) in listeners:
            
            log.debug('Notifying listener on {}: {}'.format(self.label, lName))
            
            func(value, valid, instance, tkProp, name)

    
    def _makeTkVar(self, instance):
        """
        Creates a TkVarProxy object, and attaches it to the given
        instance.  Also registers this PropertyBase instance as a
        listener on the TkVarProxy object.
        """

        instval = TkVarProxy(
            self, instance, self.tkVarType, self.default, self.label)
        instance.__dict__[self.label] = instval

        listenerName = 'PropertyBase_{}_{}'.format(self.label, id(instval))

        instval.addListener(listenerName, self._varChanged)

        return instval


    def getTkVar(self, instance):
        """
        Return the TkVarProxy object (or objects) for this property,
        associated with the given HasProperties instance. Properties
        which contain multiple TkVarProxy objects should override
        this method to return a list of said objects.
        """
        return instance.__dict__[self.label]

        
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
            if isinstance(self.required, bool) and self.required:
                raise ValueError('A value is required for {}'.format(
                    self.label))

            # or a function
            elif self.required(instance):
                raise ValueError('A value is required for {}'.format(
                    self.label))

        if self.validateFunc is not None:
            self.validateFunc(instance, value)

            
    def __get__(self, instance, owner):
        """
        If called on the HasProperties class, and not on an instance,
        returns this PropertyBase object. Otherwise, returns the value
        contained in the TkVarProxy variable which is attached to the
        instance.
        """

        if instance is None:
            return self

        instval = instance.__dict__.get(self.label, None)
        if instval is None: instval = self._makeTkVar(instance)

        # See comments in TkVarProxy._traceCb
        # for a brief overview of this silliness.
        try:    val = instval.tkVar.get()
        except: val = instval.tkVar._tk.globalgetvar(instval.tkVar._name)

        if val == '': val = None

        return val

        
    def __set__(self, instance, value):
        """
        Set the Tkinter variable, attached to the given instance, to
        the given value.  
        """

        if value is None: value = ''

        instval = self.getTkVar(instance)
        instval.tkVar.set(value)
            

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
        
        
    def getTkProp(self, propName):
        """
        Return the tkprop PropertyBase object for the given property.
        """
        return getattr(self.__class__, propName)


    def getTkVar(self, propName):
        """
        Return the TkVarProxy object(s) for the given property. 
        """
        return self.getTkProp(propName).getTkVar(self)

        
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
        

    def validateAll(self):
        """
        Validates all of the properties of this HasProperties object.
        A list of strings is returned, with each string containing
        an error message about the property which failed validation.
        If all property values are valid, the returned list will be
        empty.
        """

        names, props = self.getAllProperties()

        errors = []

        for name, prop in zip(names,props):
            
            try:
                val = getattr(self, name)
                prop.validate(self, val)
                
            except ValueError as e:
                errors.append(e.message)

        return errors

        
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
