#!/usr/bin/env python
#
# properties.py - Python descriptor framework.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Python descriptor framework.

This module defines the :class:`PropertyBase`, :class:`ListPropertyBase`, and
:class:`HasProperties` classes, which form the basis for defining class
properties. See also the :mod:`~fsl.props.properties_value` and
:mod:`~fsl.props.properties_types` modules.
"""

import logging
log = logging.getLogger(__name__)


class InstanceData(object):
    """An :class:`InstanceData` object is created for every :class:`PropertyBase`
    object of a :class:`HasProperties` instance. It stores references to the
    the instance and the associated property value(s).
    """
    
    def __init__(self, instance, propVal):
        self.instance = instance
        self.propVal  = propVal

        
class PropertyBase(object):
    """The base class for properties.

    For every :class:`HasProperties` object which has this
    :class:`PropertyBase` object as a property, one :class:`InstanceData`
    object is created and attached as an attribute of the
    :class:`HasProperties` object.

    One important point to note is that a :class:`PropertyBase` object may
    exist without being bound to a :class:`HasProperties` object (in which
    case it will not create or manage any
    :class:`~fsl.props.properties_value.PropertyValue` objects). This is
    useful if you just want validation functionality via the :meth:`validate`,
    :meth:`getConstraint` and :meth:`setConstraint` methods, passing in
    ``None`` for the instance parameter. Nothing else will work properly
    though.

    Subclasses should:

      - Ensure that the superclass :meth:`__init__` is called.

      - Override the :meth:`validate` method to implement any built in
        validation rules, ensuring that the the superclass implementation
        is called first.

      - Override the :meth:`cast` method for implicit casting/conversion logic
        (see :class:`~fsl.props.properties_types.Boolean` for an example).

    """

    def __init__(self,
                 default=None,
                 validateFunc=None,
                 preNotifyFunc=None,
                 required=False,
                 allowInvalid=True,
                 **constraints):
        """Define a :class:`PropertyBase` property.
        
        :param default:           Default/initial value.
        
        :param bool required:     Boolean determining whether or not this
                                  property must have a value. May alternately
                                  be a function which accepts one parameter,
                                  the owning :class:`HasProperties` instance,
                                  and returns ``True`` or ``False``.
        
        :param validateFunc:      Custom validation function. Must accept
                                  three parameters: a reference to the
                                  :class:`HasProperties` instance, the owner
                                  of this property; a dictionary containing
                                  the constraints for this property; and the
                                  new property value. Should return ``True``
                                  if the property value is valid, ``False``
                                  otherwise.

        :param preNotifyFunc:     Function to be called whenever the property
                                  value(s) changes. See
                            :class:`~fsl.props.properties_value.PropertyValue`.

        :param bool allowInvalid: If ``False``, a :exc:`ValueError` will be
                                  raised on all attempts to set this property
                                  to an invalid value. This does not guarantee
                                  that the property value will never be
                                  invalid - see caveats in the
                             :class:`~fsl.props.properties_value.PropertyValue`.
                                  documentation.
        
        :param constraints:       Type specific constraints used to test
                                  validity.
        """

        # The _label attribute is set by the PropertyOwner
        # metaclass when a new HasProperties class is defined
        self._label              = None
        self._default            = default
        self._required           = required
        self._validateFunc       = validateFunc
        self._preNotifyFunc      = preNotifyFunc
        self._allowInvalid       = allowInvalid
        self._defaultConstraints = constraints

        
    def addListener(self, instance, name, callback):
        """Register a listener with the
        :class:`~fsl.props.properties_value.PropertyValue` object managed by
        this property. See
        :meth:`~fsl.props.properties_value.PropertyValue.addListener`.

        :param instance: The :class:`HasProperties` instance on which the
                         listener is to be registered.
        :param str name: A name for the listener.
        :param callback: The listener callback function
        """
        self._getInstanceData(instance).propVal.addListener(name, callback)
        
        
    def removeListener(self, instance, name):
        """De-register the named listener from the
        :class:`~fsl.props.properties_value.PropertyValue` object managed by
        this property.
        """
        instData = self._getInstanceData(instance)
        
        if instData is None: return
        else:                instData.propVal.removeListener(name)


    def setPreNotifyFunction(self, instance, preNotifyFunc):
        """Sets the function to be called on property value changes, before any
        registered listeners.
        """ 
        instData = self._getInstanceData(instance)
        
        if instData is None:
            return
        else:
            instData.propVal.setPreNotifyFunction(preNotifyFunc) 

        
    def addConstraintListener(self, instance, name, listener):
        """Add a listener which will be notified whenever any constraint on the
        :class:`~fsl.props.properties_value.PropertyValue` object bound to the
        given instance change. An :exc:`AttributeError` will be raised if
        instance is ``None``.  The listener function must accept the following
        parameters:
        
          - ``instance``:   The :class:`HasProperties` instance
          - ``constraint``: The name of the constraint that changed
          - ``value``:      The new constraint value
        """
        instData = self._getInstanceData(instance)
        instData.propVal.addAttributeListener(name, listener)

        
    def removeConstraintListener(self, instance, name):
        """Removes the named constraint listener."""
        instData = self._getInstanceData(instance)
        
        if instData is None: return
        else:                instData.propVal.removeAttributeListener(name)

        
    def getConstraint(self, instance, constraint):
        """Returns the value of the named constraint for the specified
        instance, or the default constraint value if instance is ``None``.
        """
        instData = self._getInstanceData(instance)
        
        if instData is None: return self._defaultConstraints[constraint]
        else:                return instData.propVal.getAttribute(constraint)


    def setConstraint(self, instance, constraint, value):
        """Sets the value of the named constraint for the specified instance, or the
        default value if instance is ``None``.

        """
        log.debug('Changing {} constraint on {}: {} = {}'.format(
            self._label,
            'default' if instance is None else 'instance',
            constraint,
            value))

        instData = self._getInstanceData(instance)

        if instData is None: oldVal = self._defaultConstraints[constraint]
        else:                oldVal = instData.propVal.getAttribute(constraint)

        if value == oldVal: return

        if instData is None: self._defaultConstraints[constraint] = value
        else:                instData.propVal.setAttribute(constraint, value)


    def getPropVal(self, instance):
        """Return the :class:`~fsl.props.properties_value.PropertyValue`
        object(s) for this property, associated with the given
        :class:`HasProperties` instance, or ``None`` if there is no value
        for the given instance.
        """
        instData = self._getInstanceData(instance)
        if instData is None: return None
        return instData.propVal


    def _getInstanceData(self, instance):
        """Returns the :class:`InstanceData` object for the given instance, or
        ``None`` if there is no :class:`InstanceData` for the given
        instance. An :class:`InstanceData` object, which provides a binding
        between a :class:`PropertyBase` object and a :class:`HasProperties`
        instance, is created by that :class:`HasProperties` instance when it
        is created (see :meth:`HasProperties.__new__`).
        """
        return instance.__dict__.get(self._label, None)

        
    def _makePropVal(self, instance):
        """Creates and returns a
        :class:`~fsl.props.properties_value.PropertyValue object for the given
        :class:HasProperties` instance.  
        """
        return PropertyValue(instance,
                             name=self._label,
                             value=self._default,
                             castFunc=self.cast,
                             validateFunc=self.validate,
                             preNotifyFunc=self._preNotifyFunc,
                             postNotifyFunc=self._valChanged,
                             allowInvalid=self._allowInvalid,
                             **self._defaultConstraints)

        
    def _valChanged(self, value, valid, instance):
        """This function is called by PropertyValue objects which are managed
        by this PropertyBase object. It notifies any listeners which have been
        registered to this property of any value changes.
        """

        instData = self._getInstanceData(instance)

        if instData is None: return

        # Force validation for all other properties of the instance, and
        # notification of their registered listeners, This is done because the
        # validity of some properties may be dependent upon the values of this
        # one. So when the value of this property changes, it may have changed
        # the validity of another property, meaning that the listeners of the
        # latter property need to be notified of this change in validity.

        #
        # I don't like this here. It should be in HasProperties. Any reason
        # against the HasProperties instance registering an 'internal' listener
        # with every property?
        #
        propNames, props = instance.getAllProperties()
        for prop in props:
            if prop is not self:
                prop.revalidate(instance) 

            
    def validate(self, instance, attributes, value):
        """Called when an attempt is made to set the property value on the
        given instance.

        Called by :class:`PropertyValue` objects when their value changes. The
        sole purpose of :meth:`validate` is to determine whether a given value
        is valid or invalid; it should not do anything else. In particular, it
        should not modify any other property values on the instance, as bad
        things will probably happen.
        
        If the given value is invalid, subclass implementations should raise a
        :exc:`ValueError` containing a useful message as to why the value is
        invalid. Otherwise, they should not return any value.  The default
        implementation does nothing, unless a custom validate function, and/or
        ``required=True``, was passed to the constructor. If ``required`` is
        ``True``, and the value is ``None``, a :exc:`ValueError` is raised. If
        a custom validate function was set, it is called and, if it returns
        ``False``, a :exc:`ValueError` is raised. It may also raise a
        :exc:`ValueError` of its own for invalid values.

        Subclasses which override this method should therefore call this
        superclass implementation in addition to performing their own
        validation.

        :param instance:        The :class:`HasProperties` instance which
                                owns this :class:`PropertyBase` instance,
                                or ``None`` for an unbound property value.
        
        :param dict attributes: Attributes of the :class:`PropertyValue`
                                object, which are used to store type-specific
                                constraints for :class:`PropertyBase`
                                subclasses.
        
        :param value:           The value to be validated.
        """

        # a value is required
        if (self._required is not None) and (value is None):

            # required may either be a boolean value
            if isinstance(self._required, bool):
                if self._required:
                    raise ValueError('A value is required')

            # or a function
            elif self._required(instance):
                raise ValueError('A value is required')

        # a custom validation function has been provided
        if self._validateFunc is not None:
            if not self._validateFunc(instance, attributes, value):
                raise ValueError('Value does not meet custom validation rules')

        
    def cast(self, instance, attributes, value):
        """This method is called when a value is assigned to this
        :class:`PropertyBase` object through a :class:`HasProperties`
        attribute access. The default implementaton just returns the given
        value. Subclasses may override this method to perform any required
        implicit casting or conversion rules.
        """
        return value
 
        
    def revalidate(self, instance):
        """Forces validation of this property value, for the current instance.
        This will result in any registered listeners being notified, but only
        if the validity of the value has changed.
        """

        propVal = self.getPropVal(instance)
        propVal.revalidate()

            
    def __get__(self, instance, owner):
        """If called on the :class:`HasProperties` class, and not on an
        instance, returns this :class:`PropertyBase` object. Otherwise,
        returns the value contained in the
        :class:`~fsl.props.properties_value.PropertyValue` object which is
        attached to the instance.
        """

        if instance is None:
            return self
            
        instData = self._getInstanceData(instance)
        return instData.propVal.get()

        
    def __set__(self, instance, value):
        """Set the value of this property, as attached to the given instance,
        to the given value.
        """
        
        propVal = self.getPropVal(instance)
        propVal.set(value)


class ListPropertyBase(PropertyBase):
    """A :class:`PropertyBase` for properties which encapsulate more than
    one value.
    """
    
    def __init__(self, listType, **kwargs):
        """Define a :class:`ListPropertyBase` property.

        :param listType: An unbound :class:`PropertyBase` instance, defining
                         the type of value allowed in the list. This is
                         optional; if not provided, values of any type will be
                         allowed in the list, but no validation or casting
                         will be performed.
        """
        PropertyBase.__init__(self, **kwargs)
        self._listType = listType

        
    def _makePropVal(self, instance):
        """Creates and returns a
        :class:`~fsl.props.properties_value.PropertyValueList` object to be
        associated with the given :class:`HasProperties` instance.
        """

        if self._listType is not None:
            itemCastFunc     = self._listType.cast
            itemValidateFunc = self._listType.validate
            itemAllowInvalid = self._listType._allowInvalid
            itemAttributes   = self._listType._defaultConstraints
        else:
            itemCastFunc     = None
            itemValidateFunc = None
            itemAllowInvalid = True
            itemAttributes   = None
        
        return PropertyValueList(
            instance,
            name=self._label, 
            values=self._default,
            itemCastFunc=itemCastFunc,
            itemValidateFunc=itemValidateFunc,
            listValidateFunc=self.validate,
            itemAllowInvalid=itemAllowInvalid,
            postNotifyFunc=self._valChanged,
            listAttributes=self._defaultConstraints,
            itemAttributes=itemAttributes)

        
    def getPropValList(self, instance):
        """Returns the list of
        :class:`~fsl.props.properties_value.PropertyValue` objects which
        represent the items stored in this list.
        """
        propVal = self.getPropVal(instance)
        if propVal is not None: return propVal.getPropertyValueList()
        else:                   return None


    def addItemListener(self, instance, index, name, callback):
        """Convenience method which adds a listener to the property value
        object at the given index.
        """
        self.getPropValList(instance)[index].addListener(name, callback)

        
    def removeItemListener(self, instance, index, name):
        """Convenience method which removes the named listener from the
        property value at the given index.
        """
        pvl = self.getPropValList(instance)
        if pvl is not None: pvl[index].removeListener(name)


    def addItemConstraintListener(self, instance, index, name, listener):
        """Convenience method which adds a constraint listener (actually an
        attribute listener) to the PropertyValue object at the given index.
        """
        self.getPropValList(instance)[index].addAttributeListener(
            name, listener)

        
    def removeItemConstraintListener(self, instance, index, name):
        """Convenience method which removes the named constraint listener
        from the property value at the given index.
        """
        pvl = self.getPropValList(instance)
        if pvl is not None: pvl[index].removeAttributeListener(name)

        
    def getItemConstraint(self, instance, index, constraint):
        """Convenience method which returns the specified constraint for the
        property value at the given index. If instance is ``None``, the index
        is ignored, and the default list type constraint value is returned.
        If no list type was specified for this list, an :exc:AttributeError`
        is raised.
        """

        propVal = self.getPropVal(instance)

        if propVal is not None:
            propVal.getPropertyValueList()[index].getAttribute(constraint)
        else:
            self._listType.getConstraint(instance, constraint)

        
    def setItemConstraint(self, instance, index, constraint, value):
        """Convenience method which sets the specified constraint to the
        specified value, for the property value at the given index. If
        instance is ``None``, the index is ignored, and the default list
        type constraint value is changed. If no list type was specified
        for this list, an :exc:`AttributeError` is raised.
        """

        propVal = self.getPropVal(instance)

        if propVal is not None:
            propVal.getPropertyValueList()[index].getAttribute(constraint)
        else:
            self._listType.setConstraint(instance, constraint) 

        
class PropertyOwner(type):
    """Metaclass for classes which contain :class:`PropertyBase` objects. Sets
    :class:`PropertyBase` labels from the corresponding class attribute names.
    """
    def __new__(cls, name, bases, attrs):
        for n, v in attrs.items():
            if isinstance(v, PropertyBase):
                v._label = n
                
        return super(PropertyOwner, cls).__new__(cls, name, bases, attrs)


class HasProperties(object):
    """Base class for classes which contain :class:`PropertyBase` objects.  All
    classes which contain :class:`PropertyBase` objects must subclass this
    class.
    """
    __metaclass__ = PropertyOwner
    
    def __new__(cls, *args, **kwargs):
        """Here we create a new :class:`HasProperties` instance, and loop
        through all of its :class:`PropertyBase` properties to ensure that
        they are initialised.
        """
        
        instance  = super(HasProperties, cls).__new__(cls, *args, **kwargs)
        propNames = dir(instance.__class__)
        
        for propName in propNames:
            
            prop = getattr(instance.__class__, propName)
            if not isinstance(prop, PropertyBase): continue

            # Create a PropertyValue and an InstanceData
            # object, which bind the PropertyBase object
            # to this HasProperties instance.
            propVal  = prop._makePropVal(instance)
            instData = InstanceData(instance, propVal)

            # Store the InstanceData object
            # on the instance itself
            instance.__dict__[propName] = instData

        # Perform validation of the initial
        # value for each property
        for propName in propNames:
            
            prop = getattr(instance.__class__, propName)
            if isinstance(prop, PropertyBase): 
                prop.revalidate(instance)

        return instance

        
    @classmethod
    def getAllProperties(cls):
        """Returns two lists, the first containing the names of all properties
        of this object, and the second containing the corresponding
        :class:`PropertyBase` objects.
        """

        propNames = dir(cls)
        props     = map(lambda n: getattr(cls, n), propNames)

        props, propNames = zip(*filter(
            lambda (p, n): isinstance(p, PropertyBase),
            zip(props, propNames)))

        return propNames, props


    @classmethod
    def getProp(cls, propName):
        """Return the :class:`PropertyBase` object for the given property."""
        return getattr(cls, propName)


    def getPropVal(self, propName):
        """Return the :class:`~fsl.props.properties_value.PropertyValue`
        object(s) for the given property.
        """
        return self.getProp(propName).getPropVal(self)


    def getConstraint(self, propName, constraint):
        """Convenience method, returns the value of the named constraint for
        the named property. See :meth:`PropertyBase.getConstraint`.
        """
        return self.getProp(propName).getConstraint(self, constraint)

        
    def setConstraint(self, propName, constraint, value):
        """Convenience method, sets the value of the named constraint for
        the named property. See :meth:`PropertyBase.setConstraint`.
        """ 
        return self.getProp(propName).setConstraint(self, constraint, value)


    def getItemConstraint(self, propName, index, constraint):
        """Convenience method, returns the value of the named constraint for
        the value at the specified index of the named list property. See
        :meth:`ListPropertyBase.getItemConstraint`. If the named property is
        not a list property, an :exc:`AttributeError` is raised.
        """
        return self.getProp(propName).getItemConstraint(
            self, index, constraint)

        
    def setItemConstraint(self, propName, index, constraint, value):
        """Convenience method, sets the value of the named constraint for
        the value at the specified index of the named list property. See
        :meth:`ListPropertyBase.setItemConstraint`. If the named property
        is not a list property, an :exc:`AttributeError` is raised.

        """ 
        return self.getProp(propName).setItemConstraint(
            self, index, constraint, value)

        
    def setPreNotifyFunction(self, instance, preNotifyFunc):
        """Convenience method, sets the pre-notify function. See
        :meth:`PropertyBase.setPreNotifyFunction`.
        """ 
        self.getProp().setPreNotifyFunction(preNotifyFunc) 
 


    def addListener(self, propName, listenerName, callback):
        """Convenience method, adds the specified listener to the specified
        property. See :meth:`PropertyBase.addListener`.
        """
        self.getProp(propName).addListener(self, listenerName, callback)

        
    def removeListener(self, propName, listenerName):
        """Convenience method, removes the specified listener from the specified
        property. See :meth:`PropertyBase.addListener`.
        """
        self.getProp(propName).removeListener(self, listenerName)


    def addConstraintListener(self, propName, listenerName, callback):
        """Convenience method, adds the specified constraint listener to the
        specified property. See :meth:`PropertyBase.addConstraintListener`.
        """ 
        self.getProp(propName).addConstraintListener(
            self, listenerName, callback)

        
    def removeConstraintListener(self, propName, listenerName):
        """Convenience method, removes the specified constraint listener
        from the specified property. See
        :meth:`PropertyBase.removeConstraintListener`.
        """
        self.getProp(propName).removeConstraintListener(self, listenerName) 


    def isValid(self, propName):
        """Returns ``True`` if the current value of the specified property is
        valid, ``False`` otherwise.
        """

        prop    = self.getProp(propName)
        propVal = prop.getPropVal(self)
        
        try: prop.validate(self, propVal.getAttributes(), propVal.get())
        except ValueError: return False

        return True

        
    def validateAll(self):
        """Validates all of the properties of this :class:`HasProperties`
        object.  A list of tuples is returned, with each tuple containing
        a property name, and an associated error string. The error string
        is a message about the property which failed validation. If all
        property values are valid, the returned list will be empty.
        """

        names, props = self.getAllProperties()

        errors = []

        for name, prop in zip(names, props):

            propVal = prop.getPropVal(self)
            
            try:
                prop.validate(self, propVal.getAttributes(), propVal.get())
                
            except ValueError as e:
                errors.append((name, e.message))

        return errors

        
    def __str__(self):
        """Returns a multi-line string containing the names and values of
        all the properties of this object.
        """
        
        clsname = self.__class__.__name__

        propNames, props = self.getAllProperties()

        propVals = ['{}'.format(getattr(self, propName))
                    for propName in propNames]

        maxNameLength = max(map(len, propNames))

        lines = [clsname]

        for propName, propVal in zip(propNames, propVals):
            fmtStr = '  {:>' + str(maxNameLength) + '} = {}'
            lines.append(fmtStr.format(propName, propVal))
            
        return '\n'.join(lines)

from properties_value import *
from properties_types import *
