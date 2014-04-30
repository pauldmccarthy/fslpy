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
    Proxy object which encapsulates a single value for a property.
    One or more PropertyValue objects is created for every property
    of a HasProperties instance.
    """

    def __init__(self,
                 prop,
                 owner=None,
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
        
        if name is None: name = '{}_{}'.format(prop._label, id(self))
        
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
        # between PropertyValue, PropertyBase, and HasProperties objects.  The
        # PropertyBase._valChanged method is called every time a property
        # value is changed, and it triggers revalidation of all other
        # properties of the owning HasProperties object, in case their
        # validity is dependent upon the value of the changed property. But
        # during initialisation, the data structures for every property are
        # created one by one (in HasProperties.__new__), meaning that a call
        # to _valChanged for an early property would fail, as the data for
        # later properties would not yet exist. The simplest solution to this
        # problem is to skip notification the first time that property value
        # is set, which is precisely what we're doing here.
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

            try: self._preNotifyFunc(self._owner, value)
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

        # Notify the managing PropertyBase object
        # that this value has changed
        if self._owner is not None:
            self._prop._valChanged(
                value, valid, self._owner, self._prop, self._name)


    def revalidate(self):
        """
        Revalidates the current property value, and re-notifies
        any registered listeners if the value validity has changed.
        """
        self.set(self.get())


class PropertyValueList(object):
    """
    An object which acts like a list, but for which items are
    embedded in PropertyValue objects, minimum/maximum list length
    may be enforced, and value/type constraints enforced on the
    values added to it.
    
    Only basic list operations are supported. List modifications
    occur exclusively in the append, pop, __setitem__ and
    __delitem__ methods.

    A PropertyValue object is created for each item that is added
    to the list.  When a list value is changed, instead of a new
    variable being created, the value of the existing variable
    is changed.


    """

    def __init__(self,
                 owner,
                 listProp,
                 listType, 
                 minlen=None,
                 maxlen=None):
        """
        Parameters:
         - owner:    The HasProperties object, of which the List object
                     which is managing this ListWrapper object, is a
                     property.
        
         - listProp: The PropertyBase object which is managing this
                     PropertyValueList. Whenever the list, or a value
                     within the list is modified, listProp._valChanged
                     is called.
        
         - listType: A PropertyBase object specifying the type of
                     data allowed in this list. 

         - maxlen:   minimum list length
        
         - minlen:   maximum list length
        """

        self._owner           = owner
        self._listProp        = listProp
        self._listType        = listType
        self._listType._label = None
        self._minlen          = minlen
        self._maxlen          = maxlen

        # The list of PropertyValue objects.
        self._propVals = []
       
        if self._minlen is not None:

            for i in range(self._minlen):
                self._propVals.append(self.__newItem(listType._default))

        
    def __len__(self): return self._propVals.__len__()
    
    def __repr__(self):
        return list([i.get() for i in self._propVals]).__repr__()
        
    def __str__(self):
        return list([i.get() for i in self._propVals]).__str__()

        
    def getPropertyValueList(self):
        """
        Return (a copy of) the underlying property value list, allowing
        access to the PropertyValue objects which manage each list item.
        """
        return list(self._propVals)

        
    def _checkMaxlen(self, change=1):
        """
        Test that adding the given number of items to the list would
        not cause the list to grow beyond its maximum length.
        """
        if (self._maxlen is not None) and \
           (len(self._propVals) + change > self._maxlen):
            raise IndexError('{} must have a length of at most {}'.format(
                self._listProp._label, self._maxlen))


    def _checkMinlen(self, change=1):
        """
        Test that removing the given number of items to the list would
        not cause the list to shrink beyond its minimum length.
        """ 
        if (self._minlen is not None) and \
           (len(self._propVals) - change < self._minlen):
            raise IndexError('{} must have a length of at least {}'.format(
                self._listProp._label, self._minlen))

            
    def _notify(self, valid=True):
        """
        Called on list additions/removals. Notifies the List property via
        its _valChanged method.
        """
        self._listProp._valChanged(
            self[:], valid, self._owner, self._listProp, self._listProp._label) 

        
    def __newItem(self, item):
        """
        Called whenever a new item is added to the list.  Encapsulate the
        given item in a PropertyValue object.
        """
        propVal = PropertyValue(
            self._listType,
            None,
            '{}_Item'.format(self._listProp._label),
            None,
            self._listProp._allowInvalid or self._listType._allowInvalid)

        propVal.set(item)

        #propVal.addListener(
        #    'PropertyValueList',
        #    lambda value, valid, *a: self._notify(valid))
        
        return propVal

        
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

        if isinstance(key, slice):
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

        newVal = self.__newItem(item)
        
        self._propVals.append(newVal)
        self._notify()


    def extend(self, iterable):
        """
        Appends all items in the given iterable to the end of the
        list.  An IndexError is raised if an insertion would causes
        the list to grow beyond its maximum length.
        """

        toAdd = list(iterable)
        self._checkMaxlen(len(toAdd))
        
        for i in toAdd:
            self.append(i)

        
    def pop(self, index=-1):
        """
        Remove and return the specified value in the list (default: last).
        An IndexError is raised if the removal would cause the list length
        to shrink below its minimum length.
        """

        self._checkMinlen()
        
        propVal = self._propVals.pop(index)
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
                    'PropertyValueList does not support extended slices')
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
            for i, v in zip(indices, values):
                self._propVals[i].set(v)

        # Replace old PropertyValue objects with new ones. 
        else:
            values = [self.__newItem(v) for v in values]
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
