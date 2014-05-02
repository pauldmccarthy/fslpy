#!/usr/bin/env python
#
# properties_value.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

from collections import OrderedDict

log = logging.getLogger(__name__)

class PropertyValue(object):
    """
    An object which encapsulates a value of some sort. The value may be
    subjected to validation rules, and listners may be registered for
    notification of value and validity changes.
    """

    def __init__(self,
                 context,
                 name=None,
                 value=None,
                 validateFunc=None,
                 preNotifyFunc=None,
                 postNotifyFunc=None,
                 allowInvalid=True):
        """
        Create a PropertyValue object. Parameters:
        
          - context:        An object which is passed as the first argument to
                            the validate, preNotifyFunc, postNotifyFunc, and
                            any registered listeners.

          - name:           Value name - if not provided, a default, unique
                            name is created.

          - value:          Initial value.
        
          - validateFunc:   Function which accepts two parameters - a context,
                            and a value. This function should test the provided
                            value, and raise a ValueError if it is invalid.

          - preNotifyFunc:  Function to be called whenever the property value
                            changes, but before any registered listeners are
                            called. Must accept three parameters - the context
                            object, the new value, and a boolean value which is
                            true if the new value is valid, False otherwise.
        
          - postNotifyFunc: Function to be called whenever the property value
                            changes, but after any registered listeners are
                            called. Must accept the same parameters as the
                            preNotifyFunc.
        
          - allowInvalid:   If False, any attempt to set the value to something
                            invalid will result in a ValueError. Note that
                            this does not guarantee that the property will
                            never have an invalid value, as the definition of
                            'valid' depends on external factors (i.e. the
                            validateFunc).  Therefore, the validity of a value
                            may change, even if the value itself has not
                            changed.

        """
        
        if name is None: name = 'PropertyValue_{}'.format(id(self))
        
        self._context         = context
        self._validate        = validateFunc
        self._name            = name
        self._preNotifyFunc   = preNotifyFunc
        self._postNotifyFunc  = postNotifyFunc
        self._allowInvalid    = allowInvalid
        self._changeListeners = OrderedDict()
        
        self.__value          = value
        self.__valid          = False
        self.__lastValue      = None
        self.__lastValid      = False


    def addListener(self, name, callback):
        """
        Adds a listener for this value. When the value changes, the
        listener callback function is called. The callback function
        must accept these arguments:

          value    - The property value
          valid    - Whether the value is valid or invalid
          context  - The context object passed in to __init__.
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
        property value or its validity has changed, the preNotifyFunc,
        any registered listeners, and the postNotifyFunc are called.
        If allowInvalid was set to False, and the new value is not
        valid, a ValueError is raised, and listeners are not notified. 
        """

        # Check to see if the new value is valid
        valid = False
        try:
            self._validate(self._context, newValue)
            valid = True
            
        except ValueError as e:

            # Oops, we don't allow invalid values. 
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
        self._notify()

        
    def _notify(self):
        """
        Calls the preNotify function (if it is set), any listeners which have
        been registered with this PropertyValue object, and the postNotify
        function (if it is set).
        """
        
        value        = self.__value
        valid        = self.__valid
        allListeners = []

        # Call prenotify first
        if self._preNotifyFunc is not None:
            allListeners.append(('PreNotify', self._preNotifyFunc))

        # registered listeners second
        allListeners.extend(self._changeListeners.items())

        # and postnotify last
        if self._postNotifyFunc is not None:
            allListeners.append(('PostNotify', self._postNotifyFunc))

        for name, listener in allListeners:

            log.debug('Calling listener {} for {}'.format(name, self._name))

            try: listener(self._context, value, valid)
            except Exception as e:
                log.debug('Listener {} on {} raised '
                          'exception: {}'.format(name, self._name, e)) 


    def revalidate(self):
        """
        Revalidates the current property value, and re-notifies
        any registered listeners if the value validity has changed.
        """
        self.set(self.get())


    def isValid(self):
        """
        Returns true if the current property value is valid, False
        otherwise.
        """
        try: self._validate(self._context, self.get())
        except: return False
        return True
        

class PropertyValueList(PropertyValue):
    """
    A PropertyValue object which stores other PropertyValue objects in a list.
    
    Only basic list operations are supported. List modifications
    occur exclusively in the append, pop, __setitem__ and
    __delitem__ methods.

    This code is hurting my head.
    """

    def __init__(self,
                 context,
                 name=None,
                 values=None,
                 itemValidateFunc=None,
                 listValidateFunc=None,
                 itemAllowInvalid=True,
                 listAllowInvalid=True):
        """
        Parameters:
        """
        if name is None: name = 'PropertyValueList_{}'.format(id(self))

        PropertyValue.__init__(
            self,
            context,
            name,
            validateFunc=listValidateFunc,
            allowInvalid=listAllowInvalid)

        self._name             = name
        self._itemValidateFunc = itemValidateFunc
        self._itemAllowInvalid = itemAllowInvalid
        
        # The list of PropertyValue objects.
        self._propVals = []

        if values is not None:
            self.extend(values)

    def get(self):
        return self[:]

    def set(self, newValue):
        # TODO test individual values ...
        # TODO - update propvals list - could do via a preNotify call?
        raise NotImplementedError()

    def _notify(self):
        pass

        
    def __len__(self): return self.__propVals.__len__()
    
    def __repr__(self):
        return list([i.get() for i in self.__propVals]).__repr__()
        
    def __str__(self):
        return list([i.get() for i in self.__propVals]).__str__()

        
    def getPropertyValueList(self):
        """
        Return (a copy of) the underlying property value list, allowing
        access to the PropertyValue objects which manage each list item.
        """
        return list(self.__propVals)

        
    def __newItem(self, item):
        """
        Called whenever a new item is added to the list.  Encapsulate the
        given item in a PropertyValue object.
        """

        # TODO prenotify to validate entire list whenever an item is changed
        propVal = PropertyValue(
            self._context,
            name='{}_Item'.format(self._name),
            validateFunc=self._itemValidateFunc,
            allowInvalid=self._itemAllowInvalid)

        # raises error allowInvalid is False
        propVal.set(item)
        
        return propVal

        
    def index(self, item):
        """
        Returns the first index of the value, or a ValueError if the
        value is not present.
        """

        for i in range(len(self.__propVals)):
            if self.__propVals[i].get() == item:
                return i
                
        raise ValueError('{} is not present'.format(item))
        

    def __getitem__(self, key):
        """
        Return the value(s) at the specified index/slice.
        """
        
        items = self.__propVals.__getitem__(key)

        if isinstance(key, slice):
            return [i.get() for i in items]
        else:
            return items.get()


    def __iter__(self):
        """
        Returns an iterator over the values in the list.
        """
        
        innerIter = self.__propVals.__iter__()
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

        for i in self.__propVals:
            if i.get() == item:
                c = c + 1
                 
        return c

    
    def append(self, item):
        """
        Appends the given item to the end of the list.  An IndexError is
        raised if the insertion would causes the list to grow beyond its
        maximum length.
        """

        # fail if value is bad
        propVal = self.__newItem(item)

        # fail if list is bad
        self.set(self[:].append(item))

        self.__propVals.append(propVal)


    def extend(self, iterable):
        """
        Appends all items in the given iterable to the end of the
        list.  An IndexError is raised if an insertion would causes
        the list to grow beyond its maximum length.
        """
        iterable = list(iterable)

        # fail if value is bad
        propVals = map(self.__newItem, iterable)

        # fail if list is bad
        self.set(self[:].extend(iterable))
        
        self.__propVals.extend(propVals)

        
    def pop(self, index=-1):
        """
        Remove and return the specified value in the list (default: last).
        An IndexError is raised if the removal would cause the list length
        to shrink below its minimum length.
        """

        # fail if makes list bad
        self.__listPropVal.set(self[:].pop(index))

        propVal = self.__propVals.pop(index)
        val     = propVal.get()

        return val


    def __setitem__(self, key, values):
        """
        Sets the value(s) of the list at the specified index/slice.
        """

        if isinstance(key, slice):
            if (key.step is not None) and (key.step > 1):
                raise ValueError(
                    'PropertyValueList does not support extended slices')
            indices = range(*key.indices(len(self)))

        elif isinstance(key, int):
            indices = [key]
            values  = [values]

        else:
            raise ValueError('Invalid key type')

        # TODO create property values before calling
        # self.set(), so values are validated first

        self.set(self[:].__setitem__(key, values))

        # if the number of indices specified in the key
        # is different from the number of values passed
        # in, it means that we are either adding or
        # removing items from the list
        lenDiff = len(values) - len(indices)
        oldLen  = len(self)
        newLen  = oldLen + lenDiff

        # Replace values of existing items
        if newLen == oldLen:
            for i, v in zip(indices, values):
                self.__propVals[i].set(v)

        # Replace old PropertyValue objects with new ones. 
        else:
            values = [self.__newItem(v) for v in values]
            if len(values) == 1: values = values[0]
            self.__propVals.__setitem__(key, values)

        
    def __delitem__(self, key):
        """
        Remove items at the specified index/slice from the list. An
        IndexError is raised if the removal would cause the list to
        shrink below its minimum length.
        """

        # fail if makes list bad
        self.set(self[:].__delitem__(key))
        self.__propVals.__delitem__(key)
