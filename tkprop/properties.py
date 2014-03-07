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

        if value is None: value = ''
        
        if (value != '') and self.exists:

            if self.isFile and (not op.isfile(value)):
                raise ValueError('{} must be a file ({})'.format(
                    self.label, value)) 

                if (not self.isFile) and (not op.isdir(value)):
                    raise ValueError('{} must be a directory ({})'.format(
                        self.label, value)) 
