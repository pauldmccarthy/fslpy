#!/usr/bin/env python
#
# properties.py - Tkinter control variables encapsulated inside Python
# descriptors.
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
#     # access the property value as normal:
#     myPropObj.myProperty = True
#
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
#     # access the underlying Tkinter control variable:
#     myPropObj.getTkVar('myProperty')
#
#     # >>> <tkinter.BooleanVar instance at 0x1047ef518>
#
#
#     # Receive notification of property value changes
#     def myPropertyChanged(instance, propName, newValue):
#         print('New value for {}: {}'.format(propname, newValue)
#
#     PropObj.myProperty.addListener(
#         myPropObj, 'myListener', myPropertyChanged)
#
#
#     # Remove a previously added listener
#     PropObj.myProperty.removeListener(myPropObj, 'myListener')
#
#
#
#
# 
# Lots of the code in this file is probably very confusing. First
# of all, you will need to understand python descriptors.
# Descriptors are a way of adding properties to python objects,
# and allowing them to be accessed as if they were just simple
# attributes of the object, but controlling the way that the
# attributes are accessed and assigned.
#
# The following link provides a good overview, and contains the
# ideas which form the basis for the implementation in this module:
#
#  -  http://nbviewer.ipython.org/urls/gist.github.com/\
#     ChrisBeaumont/5758381/raw/descriptor_writeup.ipynb
#
# And if you've got 30 minutes, this video gives a very good
# introduction to descriptors:
#
#  - http://pyvideo.org/video/1760/encapsulation-with-descriptors
#
# Once you know how Python descriptors work, you then need to know
# how Tk control variables work. These are simple objects which
# may be passed to a Tkinter widget object when it is created. When
# a user modifies the widget value, the Tk control variable is
# modified. Conversely, if the value of a Tk control variable object
# is modified, any widgets which are bound to the variable are
# updated to reflect the new value.
#
# This module, and the associated tkpropwidget module, uses magic to
# encapsulate Tkinter control variables within python descriptors,
# thus allowing custom validation rules to be enforced on such 
# control variables.
#
# author: Paul McCarthy <pauldmccarthy@gmail.com>
#
import os
import os.path as op

from collections import OrderedDict

import Tkinter as tk


class _TkVarProxy(object):
    """
    Proxy object which encapsulates a Tkinter control variable.
    A _TkVarProxy object is created for every property of a
    HasProperties instance.  
    """

    def __init__(self, tkProp, instance, tkVarType, value=None, name=None):
        """
        Creates an instance of the specified TkVarType, and sets
        a trace on it.
        """
        
        self.tkVarType = tkVarType
        self.tkProp    = tkProp
        self.instance  = instance
        self.lastValue = value
        self.tkVar     = tkVarType(value=value, name=name)
        self.traceName = self.tkVar.trace('w', self._traceCb)

        
    def _traceCb(self, *args):
        """
        Called whenever the Tkinter control variable value is changed.
        The PropertyBase.validate() method is called on the parent
        property of this TkVarProxy object. If this validate method
        raises an error, the Tkinter variable value is reverted to its
        last good value. Otherwise, the PropertyBase._notify() method
        is called, to notify it of the value change.
        """
        
        try:
            newValue = self.tkVar.get()
            self.tkProp.validate(self.instance, newValue)
            self.lastValue = newValue
            self.tkProp._notify(self.instance, newValue)
            
        except ValueError:
            self.tkVar.set(self.lastValue)
 

class PropertyBase(object):
    """
    The base class for descriptor objects.  Subclasses should override the
    validate method to implement any required validation rules and, in
    special cases, may override __get__, __set__, and _makeTkVar, with care.
    """
    
    def __init__(self, tkVarType, default, validateFunc=None):
        """
        The tkvartype parameter should be one of the Tkinter.*Var
        classes.  For every object (the parent) which has this
        PropertyBase object as a property, a _TkVarProxy instance
        is created and attached as an attribute of the parent.
        Subclasses should call this superclass constructor,
        passing it the tkvartype and default value, and an optional
        custom validation function.
        """
        self.label             = None
        self.tkVarType         = tkVarType
        self.default           = default
        self.validateFunc      = validateFunc
        self.changeListeners   = {}

        
    def _makeTkVar(self, instance):
        """
        Creates a _TkVarProxy object, and attaches it to the given
        instance.
        """

        instval = _TkVarProxy(
            self, instance, self.tkVarType, self.default, self.label)
        instance.__dict__[self.label] = instval

        return instval

        
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

        if self.validateFunc is not None:
            self.validateFunc(instance, value)

            
    def _notify(self, instance, value):
        """
        Function which is used as a trace callback on the Tkinter
        variable of this property, when one or more listeners
        functions have been registered via the addListener method.
        This function is called when the Tkinter variable value
        changes; it propagates the change event on to any
        registered listeners.
        """
        
        if instance not in self.changeListeners: return

        for name, func in self.changeListeners[instance].items():
            func(instance, name, value)


    def addListener(self, instance, name, callback):
        """
        Adds a listener for this property object, on the specified
        HasProperties instance (the owner of this property). When
        the value of this property changes, the listener callback
        function is called. The callback function must accept three
        arguments:
        
          instance - The HasProperties instance
          name     - Name of the property that changed
          value    - The new property value
        """

        # initialise a listener dictionary for this instance,
        # if no listeners have previously been registered
        if instance not in self.changeListeners:
            self.changeListeners[instance] = {}

        # Save a reference to the listeenr callback function
        self.changeListeners[instance][name] = callback


    def removeListener(self, instance, name):
        """
        Removes the listener with the given name from the specified
        instance.
        """

        if instance not in self.changeListeners:            return
        if name     not in self.changeListeners[instance]:  return

        # remove the listener with the specified name
        self.changeListeners[instance].pop(name)

            
    def __get__(self, instance, owner):
        """
        If called on the HasProperties class, and not on an instance,
        returns this PropertyBase object. Otherwise, returns the value
        contained in the Tk control variable which is attached to the
        instance.
        """

        if instance is None:
            return self

        instval = instance.__dict__.get(self.label, None)
        if instval is None: instval = self._makeTkVar(instance)
        return instval.tkVar.get()

        
    def __set__(self, instance, value):
        """
        Attempts to set the Tkinter variable, attached to the given
        instance, to the given value.  If the new value is invalid,
        the _TkVarProxy object which controls the Tkinter variable
        will revert the change.
        """

        instval = instance.__dict__.get(self.label, None)
        if instval is None: instval = self._makeTkVar(instance)
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

        
    def getTkProp(self, propName):
        """
        Return the tkprop PropertyBase object for the given property.
        """
        return getattr(self.__class__, propName)


    def getTkVar(self, propName):
        """
        Return the Tkinter control variable for the given property.
        """
        return self.__dict__[propName].tkVar


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
        
        
    def __str__(self):
        """
        Returns a multi-line string containing the names and values
        of all the properties of this object.
        """
        
        name = self.__class__.__name__

        props = filter(
            lambda (name,prop): isinstance(prop, PropertyBase),
            self.__class__.__dict__.items())
    
        propNames,props = zip(*props)

        propVals = ['{}'.format(getattr(self, propName))
                    for propName in propNames]

        maxNameLength = max(map(len, propNames))

        lines = [name]

        for propName,propVal in zip(propNames,propVals):
            fmtStr = '  {:>' + str(maxNameLength) + '} = {}'
            lines.append(fmtStr.format(propName, propVal))
            
        return '\n'.join(lines)
                

class Boolean(PropertyBase):
    """
    A property which encapsulates a Tkinter.BooleanVar object.
    """

    def __init__(self, **kwargs):

        kwargs['default'] = kwargs.get('default', False)
        PropertyBase.__init__(self, tk.BooleanVar, **kwargs)


class _Number(PropertyBase):
    """
    Base class for the Int and Double classes. Don't
    subclass this, subclass one of Int or Double.
    """
    
    def __init__(self, tkvartype, minval=None, maxval=None, **kwargs):

        self.minval = minval
        self.maxval = maxval

        kwargs['default'] = kwargs.get('default', 0)
        PropertyBase.__init__(self, tkvartype, **kwargs)

        
    def validate(self, instance, value):
        
        PropertyBase.validate(self, instance, value)

        if self.minval is not None and value < self.minval:
            raise ValueError('{} must be at least {}'.format(
                self.label, self.minval))
            
        if self.maxval is not None and value > self.maxval:
            raise ValueError('{} must be at most {}'.format(
                self.label, self.maxval))

        
class Int(_Number):
    """
    A property which encapsulates a Tkinter.IntVar object. 
    """
    
    def __init__(self, **kwargs):
        """
        Int constructor. See the Number class for keyword
        arguments.
        """
        _Number.__init__(self, tk.IntVar, **kwargs)

        
    def validate(self, instance, value):

        try:
            value = int(value)
        except:
            raise ValueError('{} must be an integer ({})'.format(
                self.label, value))
        _Number.validate(self, instance, value)


class Double(_Number):
    """
    A property which encapsulates a Tkinter.DoubleVar object. 
    """
    
    def __init__(self, **kwargs):
        """
        Double constructor. See the Number class for keyword
        arguments.
        """
        _Number.__init__(self, tk.DoubleVar, **kwargs)

        
    def validate(self, instance, value):

        try:
            value = float(value)
        except:
            raise ValueError('{} must be a floating point number ({})'.format(
                self.label, value)) 
        _Number.validate(self, instance, value)


class Percentage(Double):
    """
    A property which represents a percentage. 
    """

    def __init__(self, **kwargs):
        kwargs['minval']  = 0.0
        kwargs['maxval']  = 100.0
        kwargs['default'] = kwargs.get('default', 50.0)
        Double.__init__(self, **kwargs)


class String(PropertyBase):
    """
    A property which encapsulates a Tkinter.StringVar object. 
    """
    
    def __init__(self, minlen=None, maxlen=None, **kwargs):
        """
        String contructor. Optional keyword arguments:
          - minlen
          - maxlen
        """ 
        self.minlen = minlen
        self.maxlen = maxlen
        
        kwargs['default'] = kwargs.get('default', '')
        PropertyBase.__init__(self, tk.StringVar, **kwargs)

    def __get__(self, instance, owner):
        val = PropertyBase.__get__(self, instance, owner)

        if val == '': return None
        return val

        
    def validate(self, instance, value):

        if value is None:
            return

        PropertyBase.validate(self, instance, value)
        
        value = str(value)

        if self.minlen is not None and len(value) < self.minlen:
            raise ValueError('{} must have length at least {}'.format(
                self.label, self.minlen))

        if self.maxlen is not None and len(value) > self.maxlen:
            raise ValueError('{} must have length at most {}'.format(
                self.label, self.maxlen))
        

class Choice(String):
    """
    A property which may only be set to one of a set of predefined values.
    """

    def __init__(self, choices, choiceLabels=None, **kwargs):
        """
        Choice constructor. Parameters:
        
          - choices:      List of strings, the possible values that
                          this property can take.
        
        Optional parameters
        
          - choiceLabels: List of labels, one for each choice, to
                          be used for display purposes.

        As an alternative to passing in separate choice and
        choiceLabels lists, you may pass in a dict as the
        choice parameter. The keys will be used as the
        choices, and the values as labels. Make sure to use
        a collections.OrderedDict if the display order is
        important.
        """

        if choices is None:
            raise ValueError('A list of choices must be provided')

        if isinstance(choices, dict):
            self.choices, self.choiceLabels = zip(*choices.items())
            
        else:
            self.choices      = choices
            self.choiceLabels = choiceLabels

        if self.choiceLabels is None:
            self.choiceLabels = self.choices

        # Lookup dictionaries for choices -> labels,
        # and vice versa. See _makeTkVar below.
        self.choiceDict = OrderedDict(zip(self.choices, self.choiceLabels))
        self.labelDict  = OrderedDict(zip(self.choiceLabels, self.choices))

        # Dict for storing references to Tkinter
        # label control variables - see _makeTkVar.
        self.labelVars  = {}

        kwargs['default'] = kwargs.get('default', self.choices[0])

        String.__init__(self, **kwargs)

        
    def validate(self, instance, value):
        """
        Rejects values that are not in the choices list.
        """

        value = str(value)

        PropertyBase.validate(self, instance, value)

        if value not in self.choices:
            raise ValueError('Invalid choice for {}: {}'.format(
                self.label, value))

            
    def getLabelVar(self, instance):
        """
        Return the label variable for the given instance.
        """
        return self.labelVars[instance]


    def _makeTkVar(self, instance):
        """
        We're using a bit of trickery here. For visual editing of a Choice
        property, we want to display the labels, rather than the choices.  But
        the ttk.Combobox doesn't allow anything like this, so if we were to
        link the Tk control variable to the combo box, and display the labels,
        the tk variable would be set to the selected label value, rather than
        the corresponding choice value. So instead of passing the TK control
        variable, we use another control variable as a proxy, and set a trace
        on it so that whenever its value changes (one of the label values),
        the real control variable is set to the corresponding choice.
        Similarly, we add a trace to the original control variable, so that
        when its choice value is modified, the label variable value is
        changed.  Even though this circular event callback situation looks
        incredibly dangerous, Tkinter (in python 2.7.6) seems to be smart
        enough to inhibit an infinitely recursive event explosion.

        The label control variable is accessible via the Choice.getLabelVar()
        method.
        """

        choiceVarProxy = String._makeTkVar(self, instance)
        choiceVar      = choiceVarProxy.tkVar
        labelVar       = tk.StringVar()

        labelVar.set(self.choiceDict[choiceVar.get()])

        self.labelVars[instance] = labelVar
        
        def choiceChanged(*a): labelVar .set(self.choiceDict[choiceVar.get()])
        def labelChanged (*a): choiceVar.set(self.labelDict [labelVar .get()])

        choiceVar.trace('w', choiceChanged)
        labelVar .trace('w', labelChanged)

        return choiceVarProxy


class FilePath(String):
    """
    A property which represents a file or directory path.
    There is currently no support for validating a path which
    may be either a file or a directory.
    """

    def __init__(self, exists=False, isFile=True, **kwargs):
        """
        FilePath constructor. Optional arguments:
          - exists: If True, the path must exist.
          - isFile: If True, the path must be a file. If False, the
                    path must be a directory. This check is only
                    performed if exists=True.
        """

        self.exists = exists
        self.isFile = isFile
        String.__init__(self, **kwargs)

        
    def validate(self, instance, value):

        if value is None: return
        if value == '':   return

        PropertyBase.validate(self, instance, value)

        if self.exists:

            if self.isFile and (not op.isfile(value)):
                raise ValueError('{} must be a file ({})'.format(
                    self.label, value)) 

            if (not self.isFile) and (not op.isdir(value)):
                raise ValueError('{} must be a directory ({})'.format(
                    self.label, value))


class _ListWrapper(object):
    """
    Used by the List property type, defined below. An object which
    acts like a list, but for which items are embedded in an
    appropriate Tkinter variable, a minimum/maximum list length may
    be enforced, and value/type constraints enforced on the values
    added to it. Not all list operations are supported.  

    A _TkVarProxy object is created for each item that is added to
    the list.  When a list value is changed, instead of a new
    variable being created, the value of the existing variable
    is changed.  References to every Tk variable in the list may
    be accessed via the _tkVars attribute of the _ListWrapper
    object.
    """

    def __init__(self,
                 owner,
                 listProp,
                 values=None,
                 listType=None,
                 minlen=None,
                 maxlen=None):
        """
        Parameters:
         - owner:    The HasProperties object, of which the List object
                     which is managing this _ListWrapper object, is a
                     property.
         - listProp: The List property object which is managing this
                     _ListWrapper object.
         - values:   list of initial values.
         - listType: A PropertyBase instance, specifying the type of
                     data allowed in this list.
         - minlen:   minimum list length
         - maxlen:   maximum list length
        """

        self._owner          = owner
        self._listProp       = listProp
        self._listType       = listType
        self._listType.label = self._listProp.label 
        self._minlen         = minlen
        self._maxlen         = maxlen

        # This is the list that the _ListWrapper wraps.
        # It contains _TkVarProxy objects.
        self._tkVars = []

        if values is not None:
            self.extend(values)

        elif self._minlen is not None:
            
            for i in range(self._minlen):
                self.append(listType.default)

    @property
    def tkVar(self):
        """
        There is a bit of trickery going on here.  The HasProperties
        class thinks that all properties are represented by a _TkVarProxy
        object, which encapsulates a Tkinter control variable, which in
        turn controls the property value. The Tkinter control variable
        is accessible via the 'tkVar' attribute of the _TkVarProxy class.
        
        However, this is not possible for List properties, because a single
        List property has multiple values, and is thus represented by a
        _ListWrapper class.  So here, we are exposing an attribute called
        'tkVar', which just returns this _ListWrapper object.  General
        code will be none the wiser, and code which knows that it is dealing
        with a List property will know.
        """
        return self

        
    def __len__(self): return self._tkVars.__len__()
    
    def __repr__(self):
        return list([i.tkVar.get() for i in self._tkVars]).__repr__()
        
    def __str__(self):
        return list([i.tkVar.get() for i in self._tkVars]).__str__()
 
    
    def _check_maxlen(self, change=1):
        """
        Test that adding the given number of items to the list would
        not cause the list to grow beyond its maximum length.
        """
        if (self._maxlen is not None) and \
           (len(self._tkVars) + change > self._maxlen):
            raise IndexError('{} must have a length of at most {}'.format(
                self._listProp.label, self._maxlen))


    def _check_minlen(self, change=1):
        """
        Test that removing the given number of items to the list would
        not cause the list to shrink beyond its minimum length.
        """ 
        if (self._minlen is not None) and \
           (len(self._tkVars) - change < self._minlen):
            raise IndexError('{} must have a length of at least {}'.format(
                self._listProp.label, self._minlen))

            
    def _makeTkVar(self, value):
        """
        Encapsulate the given value in a _TkVarProxy object.
        """

        tkval = _TkVarProxy(
            self._listType, self._owner, self._listType.tkVarType, value)
        
        return tkval


    def index(self, item):
        """
        Returns the first index of the value, or a ValueError if the
        value is not present.
        """

        for i in range(len(self._tkVars)):
            if self._tkVars[i].tkVar.get() == item:
                return i
                
        raise ValueError('{} is not present'.format(item))
        

    def __getitem__(self, key):
        """
        Return the value(s) at the specified index/slice.
        """
        
        items = self._tkVars.__getitem__(key)

        if isinstance(key,slice):
            return [i.tkVar.get() for i in items]
        else:
            return items.tkVar.get()


    def __iter__(self):
        """
        Returns an iterator over the values in the list.
        """
        
        innerIter = self._tkVars.__iter__()
        for i in innerIter:
            yield i.tkVar.get()

        
    def __contains__(self, item):
        """
        Returns True if the given is in the list, False otherwise.
        """
        
        try:    self.index(item)
        except: return False
        return True

        
    def count(self, item):
        """
        Counts the number of occurrences of the given value.
        """

        c = 0

        for i in self._tkVars:
            if i.tkVar.get() == item:
                 c = c + 1
                 
        return c

    
    def append(self, item):
        """
        Appends the given item to the end of the list.  A
        ValueError is raised if the item does not meet the list
        type/value constraints. An IndexError is raised if the
        insertion would causes the list to grow beyond its
        maximum length. 
        """
        
        self._check_maxlen()
        
        index = len(self._tkVars)
        tkVal = self._makeTkVar(item)
        
        self._tkVars.append(tkVal)


    def extend(self, iterable):
        """
        Appends all items in the given iterable to the end of the
        list.  A ValueError is raised if any item does not meet the
        list type/value constraints. An IndexError is raised if
        an insertion would causes the list to grow beyond its
        maximum length.
        """

        toAdd = list(iterable)
        self._check_maxlen(len(toAdd))

        for i in toAdd:
            self.append(i)

        
    def pop(self):
        """
        Remove and return the last value in the list. An IndexError is
        raised if the removal would cause the list length to shrink
        below its minimum length.
        """
        
        index = len(self._tkVars) - 1
        self._check_minlen()
        val = self._tkVars[index].tkVar.get()
        self.__delitem__(index)
        return val


    def __setitem__(self, key, value):
        """
        Sets the value(s) of the list at the specified index/slice.
        A ValueError is raised if any of the values do not meet the
        list type/value constraints. 
        """

        if isinstance(key, slice):
            if (key.step is not None) and (key.step > 1):
               raise ValueError(
                   '_ListWrapper does not support extended slices')
            indices = range(*key.indices(len(self)))
            
        elif isinstance(key, int):
            indices = [key]
            value   = [value]
            
        else:
            raise ValueError('Invalid key type')

        # if the number of indices specified in the key
        # is different from the number of values passed
        # in, it means that we are either adding or
        # removing items from the list
        lenDiff = len(value) - len(indices)
        oldLen  = len(self)
        newLen  = oldLen + lenDiff

        if   newLen > oldLen: self._check_maxlen( lenDiff)
        elif newLen < oldLen: self._check_minlen(-lenDiff)

        value = [self._makeTkVar(v) for v in value]
        if len(value) == 1: value = value[0]
        self._tkVars.__setitem__(key, value)

                
    def __delitem__(self, key):
        """
        Remove items at the specified index/slice from the list. An
        IndexError is raised if the removal would cause the list to
        shrink below its minimum length.
        """

        if isinstance(key, slice):
            indices = range(*key.indices(len(self)))
        else:
            indices = [key]

        self._check_minlen(len(indices))

        for i in indices:
            t = self._tkVars[i]
            t.tkVar.trace_vdelete('w', t.traceName)

        self._tkVars.__delitem__(key)


class List(PropertyBase):
    """
    A property which represents a list of items, of another property type.
    List functionality is not complete - see the documentation for the
    _ListWrapper class, defined above.

    This class is a bit different from the other PropertyBase classes, in
    that the validation logic is built into the _ListWrapper class, rather
    than this class.
    """
    
    def __init__(self, listType, minlen=None, maxlen=None, **kwargs):
        """
        Mandatory parameters:
          - listType: A PropertyBase instance, specifying the values allowed
                      in the list
        
        Optional parameters:

          - minlen:   minimum list length
          - maxlen:   maximum list length
        """

        if listType is None or not isinstance(listType, PropertyBase):
            raise ValueError(
                'A list type (a PropertyBase instance) must be specified')

        self.listType = listType
        self.minlen   = minlen
        self.maxlen   = maxlen

        kwargs['default'] = kwargs.get('default', None)
        
        PropertyBase.__init__(self, None, **kwargs)

     
    def __get__(self, instance, owner):
        if instance is None:
            return self

        instval = instance.__dict__.get(self.label, None)
        if instval is None:
            instval = _ListWrapper(instance,
                                   self,
                                   values=self.default,
                                   listType=self.listType,
                                   minlen=self.minlen,
                                   maxlen=self.maxlen)
            instance.__dict__[self.label] = instval
            
        return instval

        
    def __set__(self, instance, value):

        instval    = getattr(instance, self.label)
        instval[:] = value

