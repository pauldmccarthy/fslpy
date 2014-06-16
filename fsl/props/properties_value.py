#!/usr/bin/env python
#
# properties_value.py - Definitions of the PropertyValue and
#                       PropertyValueList classes.
#
# These definitions are a part of properties.py, and are intended
# to be created and managed by PropertyBase objects. However,
# the PropertyValue class definitions have absolutely no dependencies
# upon the PropertyBase definitions. The same can't be said for the
# other way around though.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

from collections import OrderedDict

log = logging.getLogger(__name__)

class PropertyValue(object):
    """
    An object which encapsulates a value of some sort. The value may be
    subjected to validation rules, and listeners may be registered for
    notification of value and validity changes.
    """

    def __init__(self,
                 context,
                 name=None,
                 value=None,
                 castFunc=None,
                 validateFunc=None,
                 preNotifyFunc=None,
                 postNotifyFunc=None,
                 allowInvalid=True,
                 **attributes):
        """
        Create a PropertyValue object. Parameters:
        
          - context:        An object which is passed as the first argument to
                            the validate, preNotifyFunc, postNotifyFunc, and
                            any registered listeners.

          - name:           Value name - if not provided, a default, unique
                            name is created.

          - value:          Initial value.

          - castFunc:       Function which performs type casting or data
                            conversion. Must accept three parameters - the
                            context, a dictionary containing the attributes
                            of this object, and the value to cast. Must
                            return that value, cast appropriately.
        
          - validateFunc:   Function which accepts three parameters - the
                            context, a dictionary containing the attributes
                            of this object, and a value. This function should
                            test the provided value, and raise a ValueError
                            if it is invalid.

          - preNotifyFunc:  Function to be called whenever the property value
                            changes, but before any registered listeners are
                            called. Must accept three parameters - the new
                            value, a boolean value which is true if the new
                            value is valid, False otherwise, and the context
                            object.
        
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
        
          - attributes:     Any key-value pairs which are to be associated with
                            this PropertyValue object, and passed to the cast
                            and validate functions. Attributes are not used
                            by the PropertyValue/List  classes, however they
                            are used by the List/PropertyBase classes to store
                            per-instance property constraints. Listeners may
                            register to be notified when attribute values
                            change.
        """
        
        if name     is     None: name  = 'PropertyValue_{}'.format(id(self))
        if castFunc is not None: value = castFunc(context, attributes, value)
        
        self._context            = context
        self._validate           = validateFunc
        self._name               = name
        self._castFunc           = castFunc
        self._preNotifyFunc      = preNotifyFunc
        self._postNotifyFunc     = postNotifyFunc
        self._allowInvalid       = allowInvalid
        self._attributes         = attributes.copy()
        self._changeListeners    = OrderedDict()
        self._attributeListeners = OrderedDict()
        
        self.__value             = value
        self.__valid             = False
        self.__lastValue         = None
        self.__lastValid         = False

        
    def addAttributeListener(self, name, listener):
        """
        Adds an attribute listener for this PropertyValue. The listener
        callback function must accept the following arguments:
        
          - context:   The context associated with this PropertyValue.
          - attribute: The name of the attribute that changed
          - value:     The new attribute value 
        """
        log.debug('Adding attribute listener on {}.{}: {}'.format(
            self._context.__class__.__name__, self._name, name))
        
        name = 'PropertyValue_{}_{}'.format(self._name, name) 
        self._attributeListeners[name] = listener

        
    def removeAttributeListener(self, name):
        """
        Removes the attribute listener of the given name.
        """
        log.debug('Removing attribute listener on {}.{}: {}'.format(
            self._context.__class__.__name__, self._name, name))
        
        name = 'PropertyValue_{}_{}'.format(self._name, name) 
        self._attributeListeners.pop(name, None)

        
    def getAttribute(self, name):
        """
        Returns the value of the named attribute.
        """
        return self._attributes[name]

        
    def setAttribute(self, name, value):
        """
        Sets the named attribute to the given value, and notifies any
        registered attribute listeners of the change.
        """
        oldVal = self._attributes.get(name, None)

        if oldVal == value: return

        self._attributes[name] = value

        log.debug('Attribute on {} changed: {} = {}'.format(
            self._name, name, value))

        self._notifyAttributeListeners(name, value)


    def _notifyAttributeListeners(self, name, value):
        """
        Notifies all registered attribute listeners of an attribute change.
        This method is separated so that it can be called from subclasses
        (specifically the PropertyValueList, defined below)
        """
        
        for cbName, cb in self._attributeListeners.items():
            
            log.debug('Notifying attribute listener: {}'.format(cbName))

            try:
                cb(self._context, name, value)
            except Exception as e:
                log.debug('Attribute listener {} on {} raised '
                          'exception: {}'.format(cbName, self._name, e),
                          exc_info=True) 
        
        
    def addListener(self, name, callback):
        """
        Adds a listener for this value. When the value changes, the
        listener callback function is called. The callback function
        must accept these arguments:

          value    - The property value
          valid    - Whether the value is valid or invalid
          context  - The context object passed in to __init__.
        """
        log.debug('Adding listener on {}.{}: {}'.format(
            self._context.__class__.__name__,
            self._name,
            name))
        name = 'PropertyValue_{}_{}'.format(self._name, name)
        self._changeListeners[name] = callback


    def removeListener(self, name):
        """
        Removes the listener with the given name from the specified
        instance.
        """
        log.debug('Removing listener on {}.{}: {}'.format(
            self._context.__class__.__name__,
            self._name,
            name))
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

        # cast the value if necessary.
        # Allow any errors to be thrown
        if self._castFunc is not None:
            newValue = self._castFunc(self._context,
                                      self._attributes,
                                      newValue)
            
        # Check to see if the new value is valid
        valid    = False
        validStr = None
        try:
            if self._validate is not None:
                self._validate(self._context, self._attributes, newValue)
            valid = True

        except ValueError as e:

            # Oops, we don't allow invalid values.
            validStr = str(e)
            if not self._allowInvalid:
                log.debug('Attempt to set {}.{} to an invalid value ({}), '
                          'but allowInvalid is False ({})'.format(
                              self._context.__class__.__name__,
                              self._name,
                              newValue,
                              e), exc_info=True) 
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

        log.debug('Value {}.{} changed: {} ({})'.format(
            self._context.__class__.__name__,
            self._name,
            newValue,
            'valid' if valid else 'invalid - {}'.format(validStr)))

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

            log.debug('Calling listener {} for {}.{}'.format(
                name,
                self._context.__class__.__name__,
                self._name))

            try: listener(value, valid, self._context)
            except Exception as e:
                log.debug('Listener {} on {}.{} raised '
                          'exception: {}'.format(
                              name,
                              self._context.__class__.__name__,
                              self._name,
                              e),
                          exc_info=True)


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
        try: self._validate(self._context, self._attributes, self.get())
        except: return False
        return True


class PropertyValueList(PropertyValue):
    """
    A PropertyValue object which stores other PropertyValue objects in
    a list. When created, separate validation functions may be passed in
    for individual items, and for the list as a whole. Listeners may be
    registered on individual items (accessible via the
    getPropertyValueList method), or on the entire list.

    This code hurts my head, as it's a bit complicated. The __value
    encapsulated by this PropertyValue object (a PropertyValueList is
    also a PropertyValue) is just the list of raw values.  Alongside this,
    a separate list is maintained, which contains PropertyValue objects.
    Whenever a list-modifying operation occurs on this PropertyValueList
    (which also acts a bit like a Python list), both lists are updated.
    """

    def __init__(self,
                 context,
                 name=None,
                 values=None,
                 itemCastFunc=None,
                 itemValidateFunc=None,
                 listValidateFunc=None,
                 allowInvalid=True,
                 preNotifyFunc=None,
                 postNotifyFunc=None,
                 listAttributes=None,
                 itemAttributes=None):
        """
        Parameters:
        """
        if name is None: name = 'PropertyValueList_{}'.format(id(self))
        
        if listAttributes is None: listAttributes = {}
        PropertyValue.__init__(
            self,
            context,
            name=name,
            value=values,
            validateFunc=listValidateFunc,
            allowInvalid=allowInvalid,
            preNotifyFunc=preNotifyFunc,
            postNotifyFunc=postNotifyFunc,
            **listAttributes)

        # These attributes are passed to the PropertyValue
        # constructor whenever a new item is added to the list
        self._itemCastFunc     = itemCastFunc
        self._itemValidateFunc = itemValidateFunc
        self._itemAttributes   = itemAttributes
        
        # The list of PropertyValue objects.
        if values is not None: self.__propVals = map(self.__newItem, values)
        else:                  self.__propVals = []

        
    def getPropertyValueList(self):
        """
        Return (a copy of) the underlying property value list, allowing
        access to the PropertyValue objects which manage each list item.
        """
        return list(self.__propVals)
 
        
    def get(self):
        """
        Overrides PropertyValue.get(). Returns this PropertyValueList
        object.
        """
        return self


    def set(self, newValues, recreate=True):
        """
        Overrides PropertyValue.set(). Sets the values stored in this
        PropertyValue list.  If the recreate parameter is True (default)
        all of the PropertyValue objects managed by this PVL object are
        discarded, and new ones recreated. This flag is intended for
        internal use only.
        """
        PropertyValue.set(self, newValues)

        if recreate: 
            self.__propVals = map(self.__newItem, newValues)


    def revalidate(self, usePropVals=False):
        """Overrides PropertyValue.revalidate(). Revalidates the values in this list,
        ensuring that the corresponding PropertyValue objects are not
        recreated. The usePropVals parameter is for internal use.  If it is
        False (the default), the list of values stored in this PropertyValue
        are used. Otherwise, the PropertyValue objects which represent each
        value are queried to retrieve their values.

        """
        if usePropVals: values = [pv.get() for pv in self.__propVals]
        else:           values = PropertyValue.get(self)
        
        self.set(values, False)

        
    def __newItem(self, item):
        """
        Called whenever a new item is added to the list.  Encapsulate the
        given item in a PropertyValue object.
        """

        # The only interesting thing here is the postNotifyFunc -
        # whenever a PropertyValue in this list changes, the entire
        # list is revalidated. This is primarily to ensure that
        # list-listeners are notified of changes to individual list
        # elements.
        if self._itemAttributes is None: itemAtts = {}
        else:                            itemAtts = self._itemAttributes

        propVal = PropertyValue(
            self._context,
            name='{}_Item'.format(self._name),
            value=item,
            castFunc=self._itemCastFunc,
            postNotifyFunc=lambda *a: self.revalidate(True),
            validateFunc=self._itemValidateFunc,
            allowInvalid=self._allowInvalid,
            **itemAtts)

        # Attribute listeners on the list object are
        # notified of changes to item attributes
        def itemAttChanged(ctx, name, value):
            self._notifyAttributeListeners(name, value)

        propVal.addAttributeListener(self._name, itemAttChanged)
        
        return propVal


    def __getitem__(self, key):
        return PropertyValue.get(self).__getitem__(key)
        
    def __len__(     self):       return self[:].__len__()
    def __repr__(    self):       return self[:].__repr__()
    def __str__(     self):       return self[:].__str__()
    def __iter__(    self):       return self[:].__iter__()
    def __contains__(self, item): return self[:].__contains__(item)
    def index(       self, item): return self[:].index(item)
    def count(       self, item): return self[:].count(item)
    
    def append(self, item):
        """
        Appends the given item to the end of the list.  
        """

        listVals = self[:]
        listVals.append(item)
        self.set(listVals, False)
        
        propVal = self.__newItem(item)
        self.__propVals.append(propVal)


    def extend(self, iterable):
        """
        Appends all items in the given iterable to the end of the
        list.  An IndexError is raised if an insertion would causes
        the list to grow beyond its maximum length.
        """
        listVals = self[:]
        listVals.extend(iterable)
        self.set(listVals, False) 
        
        propVals = [self.__newItem(item) for item in iterable]
        self.__propVals.extend(propVals)

        
    def pop(self, index=-1):
        """
        Remove and return the specified value in the list (default: last).
        An IndexError is raised if the removal would cause the list length
        to shrink below its minimum length.
        """
        listVals = self[:]
        listVals.pop(index)
        self.set(listVals, False)

        propVal = self.__propVals.pop(index)
        return propVal.get()

        
    def move(self, from_, to):
        """
        Move the item from 'from_' to 'to'.
        """

        listVals = self[:]
        val = listVals.pop(from_)
        listVals.insert(to, val)
        self.set(listVals, False)

        pval = self.__propVals.pop(from_)
        self.__propVals.insert(to, pval)


    def __setitem__(self, key, values):
        """
        Sets the value(s) of the list at the specified index/slice.
        """

        if isinstance(key, slice):
            indices = range(*key.indices(len(self)))
            if len(indices) != len(values):
                raise ValueError(
                    'PropertyValueList does not support complex slices')

        elif isinstance(key, int):
            indices = [key]
            values  = [values]
        else:
            raise ValueError('Invalid key type')

        oldVals = self[:]
        newVals = list(oldVals)
        for idx, val in zip(indices, values):
            newVals[idx] = val

        # this will raise an error if the
        # new list is not valid
        self.set(newVals, False)

        # if any of the individual property values
        # are invalid, catch the error, revert
        # the values, and re-raise the error
        try:
            
            for idx, val in zip(indices, values):
                self.__propVals[idx].set(val)

        except ValueError:
            self.set(oldVals, False)
            raise

        
    def __delitem__(self, key):
        """
        Remove items at the specified index/slice from the list. An
        IndexError is raised if the removal would cause the list to
        shrink below its minimum length.
        """
        listVals = self[:]
        listVals.__delitem__(key)
        self.set(listVals, False)

        self.__propVals.__delitem__(key)
