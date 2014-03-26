#!/usr/bin/env python
#
# properties_types.py - Definitions for different property types - see
# properties.py for more information.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import            os
import os.path as op
import logging as log

from collections import OrderedDict

import properties as props

class Boolean(props.PropertyBase):
    """
    A property which encapsulates a boolean value.
    """

    def __init__(self, **kwargs):

        kwargs['default'] = kwargs.get('default', False)
        props.PropertyBase.__init__(self, **kwargs)

        
    def validate(self, instance, value):
        props.PropertyBase.validate(self, instance, value)

        try:    value = bool(value)
        except: raise ValueError('Must be a boolean')


class Number(props.PropertyBase):
    """
    Base class for the Int and Double classes. Don't
    use/subclass this, use/subclass one of Int or Double.
    """
    
    def __init__(self, minval=None, maxval=None, **kwargs):

        self.minval = minval
        self.maxval = maxval

        default = kwargs.get('default', None)

        if default is None:
            if self.minval is not None and self.maxval is not None:
                default = (self.minval + self.maxval) / 2
            elif self.minval is not None:
                default = self.minval
            elif self.maxval is not None:
                default = self.maxval 
                
        kwargs['default'] = default
        props.PropertyBase.__init__(self, **kwargs)

        
    def validate(self, instance, value):
        
        props.PropertyBase.validate(self, instance, value)

        if self.minval is not None and value < self.minval:
            raise ValueError('Must be at least {}'.format(self.minval))
            
        if self.maxval is not None and value > self.maxval:
            raise ValueError('Must be at most {}'.format(self.maxval))

        
class Int(Number):
    """
    A property which encapsulates an integer. 
    """
    
    def __init__(self, **kwargs):
        """
        Int constructor. See the Number class for keyword
        arguments.
        """
        Number.__init__(self, **kwargs)

        
    def validate(self, instance, value):

        try:    value = int(value)
        except: raise ValueError('Must be an integer ({})'.format(value))
        
        Number.validate(self, instance, value)


class Double(Number):
    """
    A property which encapsulates a double. 
    """
    
    def __init__(self, **kwargs):
        """
        Double constructor. See the Number class for keyword
        arguments.
        """
        Number.__init__(self, **kwargs)

        
    def validate(self, instance, value):

        try:    value = float(value)
        except: raise ValueError('Must be a number ({})'.format(value))
        
        Number.validate(self, instance, value)


class Percentage(Double):
    """
    A property which represents a percentage. 
    """

    def __init__(self, **kwargs):
        kwargs['minval']  = 0.0
        kwargs['maxval']  = 100.0
        kwargs['default'] = kwargs.get('default', 50.0)
        Double.__init__(self, **kwargs)


class String(props.PropertyBase):
    """
    A property which encapsulates a string. 
    """
    
    def __init__(self, minlen=None, maxlen=None, **kwargs):
        """
        String contructor. Optional keyword arguments:
          - minlen
          - maxlen
        """ 
        self.minlen = minlen
        self.maxlen = maxlen
        
        kwargs['default'] = kwargs.get('default', None)
        props.PropertyBase.__init__(self, **kwargs)

        
    def validate(self, instance, value):
        props.PropertyBase.validate(self, instance, value)

        if value is None: return
        if value == '':   return

        value = str(value)

        if self.minlen is not None and len(value) < self.minlen:
            raise ValueError('Must have length at least {}'.format(self.minlen))

        if self.maxlen is not None and len(value) > self.maxlen:
            raise ValueError('Must have length at most {}'.format(self.maxlen))
        

class Choice(String):
    """
    A property which may only be set to one of a set of predefined
    strings.
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

        kwargs['default'] = kwargs.get('default', self.choices[0])

        String.__init__(self, **kwargs)

        
    def validate(self, instance, value):
        """
        Rejects values that are not in the choices list.
        """
        String.validate(self, instance, value)

        value = str(value)

        if value not in self.choices:
            raise ValueError('Invalid choice ({})'.format(value))


class FilePath(String):
    """
    A property which represents a file or directory path.
    There is currently no support for validating a path which
    may be either a file or a directory.
    """

    def __init__(self, exists=False, isFile=True, suffixes=[], **kwargs):
        """
        FilePath constructor. Optional arguments:
          - exists:       If True, the path must exist.
          - isFile:       If True, the path must be a file. If False, the
                          path must be a directory. This check is only
                          performed if exists=True.
          - suffixes:     List of acceptable file suffixes (only relevant
                          if isFile is True).
        """

        self.exists   = exists
        self.isFile   = isFile
        self.suffixes = suffixes
        
        String.__init__(self, **kwargs)

        
    def validate(self, instance, value):

        String.validate(self, instance, value)

        if value is None:   return
        if value == '':     return
        if not self.exists: return

        if self.isFile:

            values = [value]

            # if suffixes have been specified, check to
            # see if any file exists with each of the
            # suffixes (in addition to the specified path)
            if len(self.suffixes) > 0:
                values.extend(['{}{}'.format(value, s) for s in self.suffixes])

            files = map(op.isfile, values)

            if not any(map(op.isfile, values)):
                if len(self.suffixes) == 0:
                    raise ValueError('Must be a file ({})'.format(value))
                else:
                    raise ValueError(
                        'Must be a file ending in [{}] ({})'.format(
                            ','.join(self.suffixes), value))

        elif not op.isdir(value):
            raise ValueError('Must be a directory ({})'.format(value))


class ListWrapper(object):
    """
    Used by the List property type, defined below. An object which
    acts like a list, but for which items are embedded in
    PropertyValue objects, minimum/maximum list length may be
    enforced, and value/type constraints enforced on the values
    added to it.
    
    Only basic list operations are supported. List modifications
    occur exclusively in the append, pop, __setitem__ and
    __delitem__ methods.

    A PropertyValue object is created for each item that is added
    to the list.  When a list value is changed, instead of a new
    variable being created, the value of the existing variable
    is changed.  References to the list of PropertyValue objects
    may be accessed via the List.getPropVal method of the
    enclosing List object.
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
                     which is managing this ListWrapper object, is a
                     property.
        
         - listProp: The List property object which is managing this
                     ListWrapper object. Whenever the list, or a value
                     within the list is modified, listProp._valueChanged
                     is called.
        
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

        # This is the list that the ListWrapper wraps.
        # It contains TkVarProxy objects.
        self._propVals = []

        # Set the list to the given initial values
        if values is not None:
            self.extend(values)

        # Or create a list of length at least
        # minlen, containing default values
        elif self._minlen is not None:
            
            for i in range(self._minlen):
                self.append(listType.default)

        
    def __len__(self): return self._propVals.__len__()
    
    def __repr__(self):
        return list([i.get() for i in self._propVals]).__repr__()
        
    def __str__(self):
        return list([i.get() for i in self._propVals]).__str__()
 
    
    def _checkMaxlen(self, change=1):
        """
        Test that adding the given number of items to the list would
        not cause the list to grow beyond its maximum length.
        """
        if (self._maxlen is not None) and \
           (len(self._propVals) + change > self._maxlen):
            raise IndexError('{} must have a length of at most {}'.format(
                self._listProp.label, self._maxlen))


    def _checkMinlen(self, change=1):
        """
        Test that removing the given number of items to the list would
        not cause the list to shrink beyond its minimum length.
        """ 
        if (self._minlen is not None) and \
           (len(self._propVals) - change < self._minlen):
            raise IndexError('{} must have a length of at least {}'.format(
                self._listProp.label, self._minlen))

            
    def _notify(self):
        """
        Called on list modifications. Notifies the List property via
        its _varChanged method.
        """
        
        self._listProp._varChanged(
            self, True, self._owner, self._listProp, self._listProp.label) 

        
    def _makePropVal(self, value):
        """
        Encapsulate the given value in a PropertyValue object.
        """

        tkval = props.PropertyValue(self._listType, self._owner, value)
        
        return tkval

        
    def index(self, item):
        """
        Returns the first index of the value, or a ValueError if the
        value is not present.
        """

        for i in range(len(self._propVals)):
            if self._propVals[i].get() == item:
                return i
                
        raise ValueError('{} is not present'.format(item))
        

    def __getitem__(self, key):
        """
        Return the value(s) at the specified index/slice.
        """
        
        items = self._propVals.__getitem__(key)

        if isinstance(key,slice):
            return [i.get() for i in items]
        else:
            return items.get()


    def __iter__(self):
        """
        Returns an iterator over the values in the list.
        """
        
        innerIter = self._propVals.__iter__()
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

        for i in self._propVals:
            if i.get() == item:
                 c = c + 1
                 
        return c

    
    def append(self, item):
        """
        Appends the given item to the end of the list.  An IndexError is
        raised if the insertion would causes the list to grow beyond its
        maximum length.
        """

        self._checkMaxlen()

        newVal = self._makePropVal(item)
        
        self._propVals.append(newVal)
        self._notify()


    def extend(self, iterable):
        """
        Appends all items in the given iterable to the end of the
        list.  An IndexError is raised if an insertion would causes
        the list to grow beyond its maximum length.
        """

        toAdd = list(iterable)
        self.checkMaxlen(len(toAdd))
        
        for i in toAdd:
            self.append(i)

        
    def pop(self):
        """
        Remove and return the last value in the list. An IndexError is
        raised if the removal would cause the list length to shrink
        below its minimum length.
        """

        self._checkMinlen()
        
        propVal = self._propVals.pop()
        val     = propVal.get()
        
        self._notify()
        return val


    def __setitem__(self, key, values):
        """
        Sets the value(s) of the list at the specified index/slice.
        """

        if isinstance(key, slice):
            if (key.step is not None) and (key.step > 1):
               raise ValueError(
                   'ListWrapper does not support extended slices')
            indices = range(*key.indices(len(self)))

        elif isinstance(key, int):
            indices = [key]
            values  = [values]

        else:
            raise ValueError('Invalid key type')

        # if the number of indices specified in the key
        # is different from the number of values passed
        # in, it means that we are either adding or
        # removing items from the list
        lenDiff = len(values) - len(indices)
        oldLen  = len(self)
        newLen  = oldLen + lenDiff

        # adding items
        if   newLen > oldLen: self._checkMaxlen( lenDiff)

        # removing items
        elif newLen < oldLen: self._checkMinlen(-lenDiff)

        # Replace values of existing items
        if newLen == oldLen:
            for i,v in zip(indices, values):
                self._propVals[i].set(v)

        # Replace old PropertyValue objects with new ones. 
        else:
            values = [self._makePropVal(v) for v in values]
            if len(values) == 1: values = values[0]
            self._propVals.__setitem__(key, values)
            
        self._notify() 

        
    def __delitem__(self, key):
        """
        Remove items at the specified index/slice from the list. An
        IndexError is raised if the removal would cause the list to
        shrink below its minimum length.
        """

        if isinstance(key, slice): indices = range(*key.indices(len(self)))
        else:                      indices = [key]

        self._checkMinlen(len(indices))
        self._propVals.__delitem__(key)
        self._notify() 


class List(props.PropertyBase):
    """
    A property which represents a list of items, of another property type.
    List functionality is not complete - see the documentation for the
    ListWrapper class, defined above.

    This class is a bit different from the other PropertyBase classes, in
    that the validation logic is built into the ListWrapper class, rather
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

        if listType is None or not isinstance(listType, props.PropertyBase):
            raise ValueError(
                'A list type (a PropertyBase instance) must be specified')

        self.listType = listType
        self.minlen   = minlen
        self.maxlen   = maxlen

        kwargs['default'] = kwargs.get('default', None)

        props.PropertyBase.__init__(self, **kwargs)

        
    def getPropVal(self, instance, index=None):
        """
        Return a list of PropertyValue objects or, if index is specified, 
        the PropertyValue object at the specified index.
        """
        propVal = instance.__dict__.get(self.label, None)
        if propVal is None: return None
        
        if index is None: return propVal._propVals
        else:             return propVal._propVals[index]


    def _makePropVal(self, instance):
        """
        Creates a ListWrapper object, and attaches it to the
        given instance.
        """
        instval = ListWrapper(instance,
                              self,
                              values=self.default,
                              listType=self.listType,
                              minlen=self.minlen,
                              maxlen=self.maxlen)
        instance.__dict__[self.label] = instval

        return instval

        
    def validate(self, instance, values):
        """
        Validates the list and all of its values.
        """
        props.PropertyBase.validate(self, instance, values)

        if values is None:
            return
            
        if (self.minlen is not None) and (len(values) < self.minlen):
            raise ValueError('Must have length at least {}'.format(self.minlen))
            
        if (self.maxlen is not None) and (len(values) > self.maxlen):
            raise ValueError('Must have length at most {}'.format(self.maxlen))

        for v in values:
            self.listType.validate(instance, v)
            
     
    def __get__(self, instance, owner):
        """
        If instance is None, returns this List object. Otherwise returns
        the ListWrapper instance attached to the given instance.
        """
        
        if instance is None:
            return self

        instval = instance.__dict__.get(self.label, None)
        if instval is None: instval = self._makePropVal(instance) 
        
        return instval

        
    def __set__(self, instance, value):
        """
        Replaces the contents of the ListWrapper object attached
        to the given instance.
        """

        if value is None: value = []

        instval    = getattr(instance, self.label)
        instval[:] = value
