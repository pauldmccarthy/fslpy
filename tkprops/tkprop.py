#!/usr/bin/env python
#
# tkprop.py - Tkinter control variables encapsulated inside Python
# descriptors.
#
# Usage:
#
#     import Tkinter as tk
#     import tkprops as tkp
#
#     app = tk.Tk()
#
#     class PropObj(tkp.HasProperties):
#         myProperty = tkp.BooleanProp()
#
#     myPropObj = PropObj()
#
#     # access the property value as normal:
#     myPropObj.myProperty = True
#
#     myPropObj.myProperty
#
#     # >>> True
#
#     # access the tkp.Boolean instance:
#     myPropObj.myProperty_tkProp
#
#     # >>> <tkprops.tkprop.Boolean at 0x1045e2710>
#
#     # access the underlying Tkinter object:
#     myPropObj.myProperty_tkVar
#
#     # >>> <Tkinter.BooleanVar instance at 0x1047ef518>
#
# author: Paul McCarthy <pauldmccarthy@gmail.com>
#
import os
import os.path as op

import Tkinter as tk

class PropertyBase(object):
    """
    The base class for objects which represent a property. Provides default
    getter/setter methods.
    """
    
    def __init__(self, tkvartype, default):
        self.label      = None
        self._tkvartype = tkvartype
        self.default    = default

    def _make_instval(self, instance):
        
        instval = self._tkvartype(value=self.default, name=self.label)
        instance.__dict__[self.label] = instval
        return instval

    def __get__(self, instance, owner):

        if instance is None:
            return self

        instval = instance.__dict__.get(self.label, None)
        if instval is None: instval = self._make_instval(instance)
        return instval.get()

    def __set__(self, instance, value):

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
        Here, we add some extra fields to a newly created HssProperties
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
                

class Boolean(PropertyBase):
    """
    A property which encapsulates a Tkinter.BooleanVar object.
    """

    def __init__(self, default=False):
        super(Boolean, self).__init__(tk.BooleanVar, default)

    def __get__(self, instance, owner):
        result = super(Boolean, self).__get__(instance, owner)

        # tk.BooleanVar.get() returns an int, 0 or 1, so
        # here we're casting it to a python bool, unless
        # this was a class level attribute access.
        if instance is None: return result
        else:                return bool(result)

    def __set__(self, instance, value):
        super(Boolean, self).__set__(instance, bool(value))


class Number(PropertyBase):
    """
    Base class for the Int and Double classes. Don't subclass
    this, subclass one of Int or Double.
    """
    
    def __init__(self, tkvartype, default=0, minval=None, maxval=None):

        self.minval = minval
        self.maxval = maxval
        
        super(Number, self).__init__(tkvartype, default)

    def __set__(self, instance, value):

        if self.minval is not None and value < self.minval:
            raise ValueError('{} must be at least {}'.format(
                self.label, self.minval))
            
        if self.maxval is not None and value > self.maxval:
            raise ValueError('{} must be at most {}'.format(
                self.label, self.maxval))

        super(Number, self).__set__(instance, value)

        
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
        super(Int, self).__init__(tk.IntVar, **kwargs)

    def __set__(self, instance, value):
        value = int(value)
        super(Int, self).__set__(instance, value)
        

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
        super(Double, self).__init__(tk.DoubleVar, **kwargs)

    def __set__(self, instance, value):
        value = float(value)
        super(Double, self).__set__(instance, value)


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
        super(String, self).__init__(tk.StringVar, default)

    def __set__(self, instance, value):
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
        
        super(String, self).__set__(instance, value)


class Choice(String): # why only string?
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

    def __set__(self, instance, value):

        value = str(value)

        if value not in self.choices:
            raise ValueError('Invalid choice for {}: {}'.format(
                self.label, value))
        
        super(Choice, self).__set__(instance, value)


class FilePath(String):
    """
    A property which represents a file path.
    """

    def __init__(self, default=None, exists=False):

        self.exists = exists
        super(FilePath, self).__init__(default=default)

    def __set__(self, instance, value):

        value = str(value)

        if self.exists and (not op.exists(value)):
            raise ValueError('{} must be a file that exists ({})'.format(
                self.label, value))

        super(FilePath, self).__set__(instance, value)

