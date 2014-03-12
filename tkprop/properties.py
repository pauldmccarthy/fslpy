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
#     myPropObj.myProperty_tkProp
#
#     # >>> <tkprops.tkprop.Boolean at 0x1045e2710>
#
#
#     # access the underlying Tkinter control variable:
#     myPropObj.myProperty_tkVar
#
#     # >>> <_tkprops.tkprop._BooleanVar instance at 0x1047ef518>
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

import Tkinter as tk

# The classes below are used in place of the Tkinter.*Var classes.
# They are identical to the Tkinter versions, with the following
# exceptions:
#
#   1. A reference to a PropertyBase object is saved when the
#      Var object is created.
#
#   2. When the set() method is called on the Var object, the
#      PropertyBase.validate method is called, to test that
#      the new value is valid. If the new value is not valid,
#      a ValueError is raised.

class _StringVar(tk.StringVar):
    def __init__(self, tkProp, **kwargs):
        self.tkProp = tkProp
        tk.StringVar.__init__(self, **kwargs)
    def set(self, value):
        self.tkProp.validate(value)
        tk.StringVar.set(self, value)

class _DoubleVar(tk.DoubleVar):
    def __init__(self, tkProp, **kwargs):
        self.tkProp = tkProp
        tk.DoubleVar.__init__(self, **kwargs)
    def set(self, value):
        self.tkProp.validate(value)
        tk.DoubleVar.set(self, value)

class _IntVar(tk.IntVar):
    def __init__(self, tkProp, **kwargs):
        self.tkProp = tkProp
        tk.IntVar.__init__(self, **kwargs)
    def set(self, value):
        self.tkProp.validate(value)
        tk.IntVar.set(self, value)

class _BooleanVar(tk.BooleanVar):
    def __init__(self, tkProp, **kwargs):
        self.tkProp = tkProp
        tk.BooleanVar.__init__(self, **kwargs)

    def get(self):
        
        # For some reason, tk.BooleanVar.get() returns an int,
        # 0 or 1, so here we're casting it to a python bool
        return bool(tk.BooleanVar.get(self))
        
    def set(self, value):
        self.tkProp.validate(value)
        tk.BooleanVar.set(self, value)
 

class PropertyBase(object):
    """
    The base class for descriptor objects. Provides default getter/setter
    methods. Subclasses should override the validate method to implement
    any required validation rules.
    """
    
    def __init__(self, tkvartype, default):
        """
        The tkvartype parameter should be one of the Tkinter.*Var
        class replacements, defined above (e.g. _BooleanVar, _IntVar,
        etc).  For every object which has this PropertyBase object
        as a property, an instance of the tkvartype is created and
        attached to the instance.
        """
        self.label      = None
        self._tkvartype = tkvartype
        self.default    = default

        
    def _make_instval(self, instance):
        """
        Creates a Tkinter control variable of the appropriate
        type, and attaches it to the given instance.
        """
        
        instval = self._tkvartype(self, value=self.default, name=self.label)
        instance.__dict__[self.label] = instval
        return instval

        
    def validate(self, value):
        """
        Called when an attempt is made to set the property value.
        If the given value is invalid, subclass implementations
        shouldd raise an Error. Otherwise, they should not return
        any value.  The default implementation does nothing.
        """
        pass

        
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
        if instval is None: instval = self._make_instval(instance)
        return instval.get()

        
    def __set__(self, instance, value):
        """
        Attempts to set the Tk variable, attached to the given instance,
        to the given value.  The set() method of the tk variable will
        call the validate() method of this PropertyBase object, which
        will raise an Error if the value is not valid.
        """

        instval = instance.__dict__.get(self.label, None)
        if instval is None: instval = self._make_instval(instance)
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
        Here, we add some extra fields to a newly created HasProperties
        instance. These fields provided direct access to the Tkinter.*Var
        objects, and the tkprop objects. This overcomes the need for the
        slightly ugly default methods of access, i.e.:
        
          MyPropClass.propName

        to access the tkprop property object, and
        
          myPropObj.__dict__['propName']

        to access Tkinter.*Var obj. Instead, the tkprop property object can
        be accessed by the field:
        
          myPropObj.propName_tkProp

        and the Tkinter Var object via:
        
          myPropObj.propName_tkVar
        """

        inst = super(HasProperties, cls).__new__(cls, *args, **kwargs)
        
        for attr,value in inst.__class__.__dict__.items():

            if isinstance(value, PropertyBase):
                value.__get__(inst, cls)

                tkVar  = inst.__dict__[attr]
                tkProp = value

                # test to see if attrs already exist and throw an error?
                
                setattr(inst, '{}_tkVar' .format(attr), tkVar)
                setattr(inst, '{}_tkProp'.format(attr), tkProp)
                
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

    def __init__(self, default=False):
        super(Boolean, self).__init__(_BooleanVar, default)


class Number(PropertyBase):
    """
    Base class for the Int and Double classes. Don't subclass
    this, subclass one of Int or Double.
    """
    
    def __init__(self, tkvartype, default=0, minval=None, maxval=None):

        self.minval = minval
        self.maxval = maxval
        
        super(Number, self).__init__(tkvartype, default)

    def validate(self, value):

        if self.minval is not None and value < self.minval:
            raise ValueError('{} must be at least {}'.format(
                self.label, self.minval))
            
        if self.maxval is not None and value > self.maxval:
            raise ValueError('{} must be at most {}'.format(
                self.label, self.maxval))

        
class Int(Number):
    """
    A property which encapsulates a Tkinter.IntVar object. 
    """
    
    def __init__(self, **kwargs):
        """
        Int constructor. Optional keyword arguments:
          - default
          - minval
          - maxval 
        """
        super(Int, self).__init__(_IntVar, **kwargs)

    def validate(self, value):
        value = int(value)
        Number.validate(self, value)


class Double(Number):
    """
    A property which encapsulates a Tkinter.DoubleVar object. 
    """
    
    def __init__(self, **kwargs):
        """
        Double constructor. Optional keyword arguments:
          - default
          - minval
          - maxval
        """
        super(Double, self).__init__(_DoubleVar, **kwargs)

    def validate(self, value):
        value = float(value)
        Number.validate(self, value)


class Percentage(Double):
    """
    A property which represents a percentage.
    """

    def __init__(self, default=0):
        super(Percentage, self).__init__(
            default=default, minval=0.0, maxval=100.0)


class String(PropertyBase):
    """
    A property which encapsulates a Tkinter.StringVar object. 
    """
    
    def __init__(self, default='', minlen=None, maxlen=None, filterFunc=None):
        """
        String contructor. Optional keyword arguments:
          - default
          - minlen
          - maxlen
          - filterFunc: function of the form filterFunc(str) -> bool. A
            ValueError is raised if an attempt is made to set a String
            property to a value for which the filterFunc returns false.
        """ 
        self.minlen     = minlen
        self.maxlen     = maxlen
        self.filterFunc = filterFunc
        super(String, self).__init__(_StringVar, default)

    def validate(self, value):

        if value is None:
            return
        
        value = str(value)

        if self.minlen is not None and len(value) < self.minlen:
            raise ValueError('{} must have length at least {}'.format(
                self.label, self.minlen))

        if self.maxlen is not None and len(value) > self.maxlen:
            raise ValueError('{} must have length at most {}'.format(
                self.label, self.maxlen))

        if self.filterFunc is not None and (not self.filterFunc(value)):
            raise ValueError('Invalid value for {}: {}'.format(
                self.label, value))
        

class Choice(String):
    """
    A property which may only be set to one of a set of predefined values.
    """

    def __init__(self, choices, default=None, choiceLabels=None):
        """
        Choice constructor. Arguments:
          - choices: list of strings, the possible values that this
            property can take.
          - default (optional)
        """

        self.choices = choices

        if default is None:
            default = self.choices[0]

        super(Choice, self).__init__(default=default)

    def validate(self, value):

        value = str(value)

        if value not in self.choices:
            raise ValueError('Invalid choice for {}: {}'.format(
                self.label, value))


class FilePath(String):
    """
    A property which represents a file or directory path.
    """

    def __init__(self, exists=False, isFile=True):
        """
        FilePath constructor. Optional arguments:
          - exists: If True, the path must exist.
          - isFile: If True, the path must be a file. If False, the
                    path must be a directory. This check is only
                    performed if exists=True.
        """

        self.exists = exists
        self.isFile = isFile
        super(FilePath, self).__init__()

    def validate(self, value):

        if (value != '') and (value is not None) and self.exists:

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
    added to it.

    Not all list operations are supported.  The only way that new
    items may be added to the list is via append(), and the only
    way that items may be removed is via pop(). Item values may be
    modified, however, via standard list slice assignment.

    A Tk Variable object is created for each item that is added to
    the list.  When a list value is changed, instead of a new
    Tk Variable being created, the value of the existing variable
    is changed.  References to every Tk variable in the list may
    be accessed via the _tkVars attribute of hte _ListWrapper
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
        self._tkVars = []

        if values is not None:
            self.extend(values)
                
        elif self._minlen is not None:
            for i in range(self._minlen):
                self.append(listType.default)

        
    def __len__( self): return self._tkVars.__len__()
    def __repr__(self): return list([i.get() for i in self._tkVars]).__repr__()
    def __str__( self): return list([i.get() for i in self._tkVars]).__str__()
 
    
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
        Encapsulate the given value in a Tkinter variable.  A
        ValueError is raised if the value does not meet the
        list type/value constraints.
        """

        # ValueError will be raised here if value is bad
        tkval = self._listType._tkvartype(self._listType, value=value)
        return tkval


    def index(self, item):
        """
        Returns the first index of the value, or a ValueError if the
        value is not present.
        """

        for i in range(len(self._tkVars)):
            if self._tkVars[i].get() == item:
                return i
                
        raise ValueError('{} is not present'.format(item))
        

    def __getitem__(self, key):
        """
        Return the value(s) at the specified index/slice.
        """
        
        items = self._tkVars.__getitem__(key)

        if isinstance(key,slice):
            return [i.get() for i in items]
        else:
            return items.get()


    def __iter__(self):
        """
        Returns an iterator over the values in the list.
        """
        
        innerIter = self._tkVars.__iter__()
        for i in innerIter:
            yield i.get()

        
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
            if i.get() == item:
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
        return self._tkVars.pop(index).get()


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

        self._tkVars.__delitem__(key)


class List(PropertyBase):
    """
    A property which represents a list of items, of another property type.
    List functionality is not complete - see the documentation for the
    _ListWrapper class, defined above.
    """
    
    def __init__(self, default=None, listType=None, minlen=None, maxlen=None):
        """
        Optional parameters:
          - default:  Default/initial list of values
          - listType: A PropertyBase instance, specifying the values allowed
                      in the list
          - minlen:   minimum list length
          - maxlen:   maximum list length
        """

        self.listType = listType
        self.minlen   = minlen
        self.maxlen   = maxlen
        
        PropertyBase.__init__(self, None, default)

     
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
