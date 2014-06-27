#!/usr/bin/env python
#
# properties_value.py - Definitions of the PropertyValue and
#                       PropertyValueList classes.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Definitions of the :class:`PropertyValue` and :class:`PropertyValueList`
classes.

These definitions are really a part of the :mod:`fsl.props.properties` module,
and are intended to be created and managed by
:class:`~fsl.props.properties.PropertyBase` objects. However, the
:class:`PropertyValue` class definitions have absolutely no dependencies upon
the :class:`~fsl.props.properties.PropertyBase` definitions. The same can't be
said for the other way around though.

"""

import logging
import traceback

from collections import OrderedDict

log = logging.getLogger(__name__)

class PropertyValue(object):
    """An object which encapsulates a value of some sort.

    The value may be subjected to validation rules, and listeners may be
    registered for notification of value and validity changes.
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
        """Create a :class:`PropertyValue` object.
        
        :param context:        An object which is passed as the first argument
                               to the ``validateFunc``, ``preNotifyFunc``,
                               ``postNotifyFunc``, and any registered
                               listeners. Can be anything, but will nearly
                               always be a
                               :class:`~fsl.props.properties.HasProperties`
                               instance.

        :param str name:       Value name - if not provided, a default, unique
                               name is created.

        :param value:          Initial value.

        :param castFunc:       Function which performs type casting or data
                               conversion. Must accept three parameters - the
                               context, a dictionary containing the attributes
                               of this object, and the value to cast. Must
                               return that value, cast appropriately.
        
        :param validateFunc:   Function which accepts three parameters - the
                               context, a dictionary containing the attributes
                               of this object, and a value. This function
                               should test the provided value, and raise a
                               :exc:`ValueError` if it is invalid.

        :param preNotifyFunc:  Function to be called whenever the property
                               value changes, but before any registered
                               listeners are called. Must accept three
                               parameters - the new value, a boolean value
                               which is ``True`` if the new value is valid,
                               ``False`` otherwise, and the context object.
        
        :param postNotifyFunc: Function to be called whenever the property
                               value changes, but after any registered
                               listeners are called. Must accept the same
                               parameters as the ``preNotifyFunc``.
        
        :param allowInvalid:   If ``False``, any attempt to set the value to
                               something invalid will result in a
                               :exc:`ValueError`. Note that this does not
                               guarantee that the property will never have an
                               invalid value, as the definition of 'valid'
                               depends on external factors (i.e. the
                               ``validateFunc``).  Therefore, the validity of
                               a value may change, even if the value itself
                               has not changed.
        
        :param attributes:     Any key-value pairs which are to be associated 
                               with this :class:`PropertyValue` object, and 
                               passed to the ``castFunc`` and ``validateFunc`` 
                               functions. Attributes are not used by the 
                               :class:`PropertyValue` or
                               :class:`PropertyValueList` classes, however
                               they are used by the
                               :class:`~fsl.props.properties.ListPropertyBase`
                               and :class:`~fsl.props.properties.PropertyBase`
                               classes to store per-instance property
                               constraints. Listeners may register to be
                               notified when attribute values change.
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
        self.__notification      = True

        
    def enableNotification(self):
        """Enables notification of property value and attribute listeners for
        this :class:`PropertyValue` object.

        """
        self.__notification = True

        
    def disableNotification(self):
        """Disables notification of property value and attribute listeners for
        this :class:`PropertyValue` object. Notification can be re-enabled via
        the :meth:`enableNotification` method.

        """
        self.__notification = False
 
        
    def addAttributeListener(self, name, listener):
        """Adds an attribute listener for this :class:`PropertyValue`. The
        listener callback function must accept the following arguments:
        
          - ``context``:   The context associated with this
                           :class:`PropertyValue`.
          - ``attribute``: The name of the attribute that changed.
          - ``value``:     The new attribute value.

        :param str name: A unique name for the listener. If a listener with
                         the specified name already exists, it will be
                         overwritten.
        
        :param listener: The callback function.
        """
        log.debug('Adding attribute listener on {}.{}: {}'.format(
            self._context.__class__.__name__, self._name, name))
        
        name = 'PropertyValue_{}_{}'.format(self._name, name) 
        self._attributeListeners[name] = listener

        
    def removeAttributeListener(self, name):
        """Removes the attribute listener of the given name."""
        log.debug('Removing attribute listener on {}.{}: {}'.format(
            self._context.__class__.__name__, self._name, name))
        
        name = 'PropertyValue_{}_{}'.format(self._name, name) 
        self._attributeListeners.pop(name, None)


    def getAttributes(self):
        """Returns a dictionary containing all the attributes of this
        :class:`PropertyValue` object.
        """
        return self._attributes.copy()

        
    def getAttribute(self, name):
        """Returns the value of the named attribute."""
        return self._attributes[name]

        
    def setAttribute(self, name, value):
        """Sets the named attribute to the given value, and notifies any
        registered attribute listeners of the change.
        """
        oldVal = self._attributes.get(name, None)

        if oldVal == value: return

        self._attributes[name] = value

        log.debug('Attribute on {} changed: {} = {}'.format(
            self._name, name, value))

        self._notifyAttributeListeners(name, value)

        self.revalidate()


    def _notifyAttributeListeners(self, name, value):
        """Notifies all registered attribute listeners of an attribute change
        (unless notification has been disabled via the
        :meth:`disableNotification` method). This method is separated so that
        it can be called from subclasses (specifically the
        :class:`PropertyValueList`).
        """

        if not self.__notification: return
        
        for cbName, cb in self._attributeListeners.items():
            
            log.debug('Notifying attribute listener: {}'.format(cbName))

            try:
                cb(self._context, name, value)
            except Exception as e:
                log.warn('Attribute listener {} on {} raised '
                         'exception: {}'.format(cbName, self._name, e),
                         exc_info=True)
                traceback.print_stack()
        
        
    def addListener(self, name, callback):
        """Adds a listener for this value.

        When the value changes, the listener callback function is called. The
        callback function must accept these arguments:

          - ``value``:   The property value
          - ``valid``:   Whether the value is valid or invalid
          - ``context``: The context object passed to :meth:`__init__`.

        :param str name: A unique name for this listener. If a listener with
                         the name already exists, it will be overwritten.
        :param callback: The callback function.

        """
        log.debug('Adding listener on {}.{}: {}'.format(
            self._context.__class__.__name__,
            self._name,
            name))
        name = 'PropertyValue_{}_{}'.format(self._name, name)
        self._changeListeners[name] = callback


    def removeListener(self, name):
        """Removes the listener with the given name from this
        :class:`PropertyValue`.
        """
        log.debug('Removing listener on {}.{}: {}'.format(
            self._context.__class__.__name__,
            self._name,
            name))
        name = 'PropertyValue_{}_{}'.format(self._name, name)
        self._changeListeners.pop(name, None)


    def setPreNotifyFunction(self, preNotifyFunc):
        """Sets the function to be called on value changes, before any
        registered listeners.
        """
        self._preNotifyFunc = preNotifyFunc

        
    def get(self):
        """Returns the current property value."""
        return self.__value

        
    def set(self, newValue):
        """Sets the property value.

        The property is validated and, if the property value or its validity
        has changed, the ``preNotifyFunc``, any registered listeners, and the
        ``postNotifyFunc`` are called.  If ``allowInvalid`` was set to
        ``False``, and the new value is not valid, a :exc:`ValueError` is
        raised, and listeners are not notified.
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
                              e, exc_info=True))
                traceback.print_stack()
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
        """Notifies registered listeners.

        Calls the ``preNotify`` function (if it is set), any listeners which
        have been registered with this :class:`PropertyValue` object, and the
        ``postNotify`` function (if it is set). If notification has been
        disabled (via the :meth:`disableNotification` method), this method
        does nothing.
        """

        if not self.__notification: return
        
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
                log.warn('Listener {} on {}.{} raised '
                         'exception: {}'.format(
                             name,
                             self._context.__class__.__name__,
                             self._name,
                             e),
                         exc_info=True)
                traceback.print_stack()


    def revalidate(self):
        """Revalidates the current property value, and re-notifies any
        registered listeners if the value validity has changed.
        """
        self.set(self.get())


    def isValid(self):
        """Returns ``True`` if the current property value is valid, ``False``
        otherwise.
        """
        try: self._validate(self._context, self._attributes, self.get())
        except: return False
        return True


class PropertyValueList(PropertyValue):
    """A :class:`PropertyValue` object which stores other
    :class:`PropertyValue` objects in a list.

    When created, separate validation functions may be passed in for
    individual items, and for the list as a whole. Listeners may be registered
    on individual items (accessible via the :meth:`getPropertyValueList`
    method), or on the entire list.

    This code hurts my head, as it's a bit complicated. The ``__value``
    encapsulated by this :class:`PropertyValue` object (a
    :class:`PropertyValueList` is itself a :class:`PropertyValue`) is just the
    list of raw values.  Alongside this, a separate list is maintained, which
    contains :class:`PropertyValue` objects.  Whenever a list-modifying
    operation occurs on this :class:`PropertyValueList` (which also acts a bit
    like a Python list), both lists are updated.

    The values contained in this :class:`PropertyValueList` may be accessed
    through standard Python list operations, including slice-based access
    and assignment, :meth:`append`, :meth:`extend`, :meth:`pop`,
    :meth:`index`, :meth:`count`, and :meth:`move` (this last one is
    non-standard).

    The main restriction of this list-like functionality is that value
    assigments via indexing must not change the length of the list. For
    example, this is a valid assignment::

      mylist[2:7] = [3,4,5,6,7]

    Whereas this would result in an :exc:`IndexError`::

      mylist[2:7] = [3,4,5,6]


    When a :class:`PropertyValueList` is accessed as an attribute of a
    :class:`~fsl.props.properties.HasProperties` instance (by far the most
    common use-case), there is an important semantic difference between
    an assignment like this::

      myObj.mylist = [1,2,3,4,5]

    and one like this::

      myObj.mylist[:] = [1,2,3,4,5]

    The first approach will result in any existing :class:`PropertyValue`
    objects in the list being discarded, and new ones created for the new list
    values. In contrast, the second approach, in addition to raising a
    :exc:`IndexError` if the existing list length is not ``5``, will not
    result in creation of new :class:`PropertyValue` instances; rather, the
    values of the existing :class:`PropertyValue` objects will be
    updated.

    This is a very important distinction to keep in mind when working with
    list properties and values which may exist for long periods of time and,
    more importantly, for which listeners have been registered with individual
    :class:`PropertyValue` objects contained in the list. If you register
    a listener with a :class:`PropertyValue` item, and then assign values to
    the list using the first assignment approach above, your listener will be
    lost in the ether.

    There are some interesting type-specific subclasses of the
    :class:`PropertyValueList`, which provide additional functionality:

      - The :class:`~fsl.props.properties_types.PointValueList`, for
        :class:`~fsl.props.properties_types.Point` properties.

      - The :class:`~fsl.props.properties_types.BoundsValueList`, for
        :class:`~fsl.props.properties_types.Bounds` properties.
    """

    def __init__(self,
                 context,
                 name=None,
                 values=None,
                 itemCastFunc=None,
                 itemValidateFunc=None,
                 listValidateFunc=None,
                 itemAllowInvalid=True,
                 preNotifyFunc=None,
                 postNotifyFunc=None,
                 listAttributes=None,
                 itemAttributes=None):
        """Create a :class:`PropertyValueList`.

        :param context:               See the :class:`PropertyValue`
                                      constructor.
        
        :param str name:              See the :class:`PropertyValue`
                                      constructor.
        
        :param list values:           Initial list values.
        
        :param itemCastFunc:          Function which casts a single
                                      list item. See the :class:`PropertyValue`
                                      constructor.
        
        :param itemValidateFunc:      Function which validates a single
                                      list item. See the :class:`PropertyValue`
                                      constructor.
        
        :param listValidateFunc:      Function which validates the list as a
                                      whole.
        
        :param bool itemAllowInvalid: Whether items are allowed to containg
                                      invalid values.
        
        :param preNotifyFunc:         See the :class:`PropertyValue`
                                      constructor.
        
        :param postNotifyFunc:        See the :class:`PropertyValue`
                                      constructor.
        
        :param dict listAttributes:   Attributes to be associated with this
                                      :class:`PropertyValueList`.
        
        :param dict itemAttributes:   Attributes to be associated with new
                                      :class:`PropertyValue` items added to
                                      the list.
        """
        if name is None: name = 'PropertyValueList_{}'.format(id(self))
        
        if listAttributes is None: listAttributes = {}

        # The list as a whole must be allowed to contain
        # invalid values because, if an individual
        # PropertyValue item value changes, there is no
        # nice way to propagate those changes on to other
        # (dependent) items without the list as a whole
        # being validated first, and errors being raised.
        PropertyValue.__init__(
            self,
            context,
            name=name,
            value=values,
            allowInvalid=True,
            validateFunc=listValidateFunc,
            preNotifyFunc=preNotifyFunc,
            postNotifyFunc=postNotifyFunc,
            **listAttributes)

        # These attributes are passed to the PropertyValue
        # constructor whenever a new item is added to the list
        self._itemCastFunc     = itemCastFunc
        self._itemValidateFunc = itemValidateFunc
        self._itemAllowInvalid = itemAllowInvalid
        self._itemAttributes   = itemAttributes
        
        # The list of PropertyValue objects.
        if values is not None: self.__propVals = map(self.__newItem, values)
        else:                  self.__propVals = []

        
    def getPropertyValueList(self):
        """Return (a copy of) the underlying property value list, allowing
        access to the :class:`PropertyValue` objects which manage each list
        item.
        """
        return list(self.__propVals)
 
        
    def get(self):
        """Overrides :meth:`PropertyValue.get`. Returns this
        :class:`PropertyValueList` object.
        """
        return self


    def set(self, newValues, recreate=True):
        """Overrides :meth:`PropertyValue.set`.

        Sets the values stored in this :class:`PropertyValueList`.  If the
        ``recreate`` flag is ``True`` (default) all of the
        :class:`PropertyValue` objects managed by this ``PVL`` object are
        discarded, and new ones recreated. This flag is intended for internal
        use only.
        """

        if self._itemCastFunc is not None:
            newValues = map(lambda v: self._itemCastFunc(
                self._context,
                self._itemAttributes,
                v), newValues)
        PropertyValue.set(self, newValues)

        if recreate: 
            self.__propVals = map(self.__newItem, newValues)


    def revalidate(self):
        """Overrides :meth:`PropertyValue.revalidate`.

        Revalidates the values in this list, ensuring that the corresponding
        :class:`PropertyValue` objects are not recreated.
        """
        self.set(PropertyValue.get(self), False)

        
    def __newItem(self, item):
        """Called whenever a new item is added to the list.  Encapsulate the
        given item in a :class:`PropertyValue` object.
        """

        if self._itemAttributes is None: itemAtts = {}
        else:                            itemAtts = self._itemAttributes

        propVal = PropertyValue(
            self._context,
            name='{}_Item'.format(self._name),
            value=item,
            castFunc=self._itemCastFunc,
            allowInvalid=self._itemAllowInvalid,
            validateFunc=self._itemValidateFunc,
            **itemAtts)

        # When a PropertyValue item value changes,
        # sync the list values with it if necessary.
        def postNotify(value, *a):
            idx = self.__propVals.index(propVal)
            if self[idx] != value: self[idx] = value
            
        propVal._postNotifyFunc = postNotify

        # Attribute listeners on the list object are
        # notified of changes to item attributes
        def itemAttChanged(ctx, name, value):
            self._notifyAttributeListeners(name, value)

        propVal.addAttributeListener(self._name, itemAttChanged)
        
        return propVal


    def __getitem__(self, key):
        return PropertyValue.get(self).__getitem__(key)

    def __eq__(      self, other): return self[:].__eq__(other[:])
    def __len__(     self):        return self[:].__len__()
    def __repr__(    self):        return self[:].__repr__()
    def __str__(     self):        return self[:].__str__()
    def __iter__(    self):        return self[:].__iter__()
    def __contains__(self, item):  return self[:].__contains__(item)
    def index(       self, item):  return self[:].index(item)
    def count(       self, item):  return self[:].count(item)
    
    def append(self, item):
        """Appends the given item to the end of the list."""

        listVals = self[:]
        listVals.append(item)
        self.set(listVals, False)
        
        propVal = self.__newItem(item)
        self.__propVals.append(propVal)


    def extend(self, iterable):
        """Appends all items in the given iterable to the end of the list."""
        listVals = self[:]
        listVals.extend(iterable)
        self.set(listVals, False) 
        
        propVals = [self.__newItem(item) for item in iterable]
        self.__propVals.extend(propVals)

        
    def pop(self, index=-1):
        """Remove and return the specified value in the list (default:
        last).
        """
        listVals = self[:]
        listVals.pop(index)
        self.set(listVals, False)

        propVal = self.__propVals.pop(index)
        return propVal.get()

        
    def move(self, from_, to):
        """Move the item from 'from\_' to 'to'."""

        listVals = self[:]
        val = listVals.pop(from_)
        listVals.insert(to, val)
        self.set(listVals, False)

        pval = self.__propVals.pop(from_)
        self.__propVals.insert(to, pval)


    def __setitem__(self, key, values):
        """Sets the value(s) of the list at the specified index/slice."""

        if isinstance(key, slice):
            indices = range(*key.indices(len(self)))
            if len(indices) != len(values):
                raise IndexError(
                    'PropertyValueList does not support complex slices')

        elif isinstance(key, int):
            indices = [key]
            values  = [values]
        else:
            raise IndexError('Invalid key type')

        oldVals = self[:]
        newVals = list(oldVals)
        for idx, val in zip(indices, values):
            propVal = self.__propVals[idx]
            newVals[idx] = propVal._castFunc(propVal._context,
                                             propVal._attributes,
                                             val) 

        # set the list values
        self.set(newVals, False)

        # propagate the changes to the PropertyValue items if
        # necessary. if any of the individual property values
        # are invalid, catch the error, revert the values,
        # and re-raise the error
        try:
            
            for idx, val in zip(indices, values):
                if self.__propVals[idx].get() != val:
                    self.__propVals[idx].set(val)

        except ValueError:
            self.set(oldVals, False)
            raise

        
    def __delitem__(self, key):
        """Remove items at the specified index/slice from the list."""
        listVals = self[:]
        listVals.__delitem__(key)
        self.set(listVals, False)

        self.__propVals.__delitem__(key)
