#!/usr/bin/env python
#
# properties_types.py - Definitions for different property types - see
# properties.py for more information.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op

import matplotlib.colors as mplcolors
import matplotlib.cm     as mplcm

import properties       as props
import properties_value as propvals

class Boolean(props.PropertyBase):
    """
    A property which encapsulates a boolean value.
    """

    def __init__(self, **kwargs):

        kwargs['default'] = kwargs.get('default', False)
        props.PropertyBase.__init__(self, **kwargs)

        
    def cast(self, instance, value):
        return bool(value)


class Number(props.PropertyBase):
    """
    Base class for the Int and Real classes. Don't
    use/subclass this, use/subclass one of Int or Real.
    """
    
    def __init__(self,
                 minval=None,
                 maxval=None,
                 clamped=False,
                 editLimits=False,
                 **kwargs):
        """
        Optional parameters:
          - minval:     Minimum value
          - maxval:     Maximum value
          - clamped:    If True, the value will be clamped to its min/max
                        bounds.
          - editLimits: If True, widgets created to modify Number properties
                        will allow the user to change the min/max limits.
        """

        default = kwargs.get('default', None)

        if default is None:
            if minval is not None and maxval is not None:
                default = (minval + maxval) / 2
            elif minval is not None:
                default = minval
            elif maxval is not None:
                default = maxval
            else:
                default = 0

        kwargs['default']    = default
        kwargs['minval']     = minval
        kwargs['maxval']     = maxval
        kwargs['editLimits'] = editLimits
        kwargs['clamped']    = clamped
        props.PropertyBase.__init__(self, **kwargs)

        
    def validate(self, instance, value):
        
        props.PropertyBase.validate(self, instance, value)
        
        minval = self.getConstraint(instance, 'minval')
        maxval = self.getConstraint(instance, 'maxval')

        if minval is not None and value < minval:
            raise ValueError('Must be at least {}'.format(minval))
            
        if maxval is not None and value > maxval:
            raise ValueError('Must be at most {}'.format(maxval))


    def cast(self, instance, value):

        clamped = self.getConstraint(instance, 'clamped')
        
        if not clamped: return value

        minval = self.getConstraint(instance, 'minval')
        maxval = self.getConstraint(instance, 'maxval') 

        if minval is not None and value < minval: return minval
        if maxval is not None and value > maxval: return maxval

        return value
        
        
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

        
    def cast(self, instance, value):
        return Number.cast(self, instance, int(value))
        

class Real(Number):
    """
    A property which encapsulates a real number (as a python floating
    point).
    """
    
    def __init__(self, **kwargs):
        """
        Real constructor. See the Number class for keyword
        arguments.
        """
        Number.__init__(self, **kwargs)


    def cast(self, instance, value):
        return Number.cast(self, instance, float(value))
        

class Percentage(Real):
    """
    A property which represents a percentage. 
    """

    def __init__(self, **kwargs):
        kwargs['minval']  = 0.0
        kwargs['maxval']  = 100.0
        kwargs['default'] = kwargs.get('default', 50.0)
        Real.__init__(self, **kwargs)


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
        
        kwargs['default'] = kwargs.get('default', None)
        kwargs['minlen']  = minlen
        kwargs['maxlen']  = maxlen
        props.PropertyBase.__init__(self, **kwargs)


    def cast(self, instance, value):

        if value is None: value = ''
        else:             value = str(value)
        
        if value == '': value = None
        return value

        
    def validate(self, instance, value):
        
        if value == '': value = None
        
        props.PropertyBase.validate(self, instance, value)

        if value is None: return

        if not isinstance(value, basestring):
            raise ValueError('Must be a string')

        minlen = self.getConstraint(instance, 'minlen')
        maxlen = self.getConstraint(instance, 'maxlen')

        if minlen is not None and len(value) < minlen:
            raise ValueError('Must have length at least {}'.format(minlen))

        if maxlen is not None and len(value) > maxlen:
            raise ValueError('Must have length at most {}'.format(maxlen))
        

class Choice(props.PropertyBase):
    """
    A property which may only be set to one of a set of predefined
    values.
    """

    def __init__(self, choices, choiceLabels=None, **kwargs):
        """
        Choice constructor. Parameters:
        
          - choices:      List of values, the possible values that
                          this property can take.
        
        Optional parameters
        
          - choiceLabels: List of string labels, one for each choice,
                          to be used for display purposes.

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
            self.choiceLabels = map(str, self.choices)

        kwargs['default'] = kwargs.get('default', self.choices[0])

        props.PropertyBase.__init__(self, **kwargs)

        
    def validate(self, instance, value):
        """
        Rejects values that are not in the choices list.
        """
        props.PropertyBase.validate(self, instance, value)

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

        kwargs['exists']   = exists
        kwargs['isFile']   = isFile
        kwargs['suffixes'] = suffixes
        
        String.__init__(self, **kwargs)

        
    def validate(self, instance, value):

        String.validate(self, instance, value)

        exists   = self.getConstraint(instance, 'exists')
        isFile   = self.getConstraint(instance, 'isFile')
        suffixes = self.getConstraint(instance, 'suffixes')

        if value is None: return
        if value == '':   return
        if not exists:    return

        if isFile:

            matchesSuffix = any(map(lambda s: value.endswith(s), suffixes))

            # If the file doesn't exist, it's bad
            if not op.isfile(value):
                raise ValueError('Must be a file ({})'.format(value))

            # if the file exists, and matches one of
            # the specified suffixes, then it's good
            if len(suffixes) == 0 or matchesSuffix: return

            # Otherwise it's bad
            else:
                raise ValueError(
                    'Must be a file ending in [{}] ({})'.format(
                        ','.join(suffixes), value))

        elif not op.isdir(value):
            raise ValueError('Must be a directory ({})'.format(value))


class List(props.ListPropertyBase):
    """
    A property which represents a list of items, of another property type.
    List functionality is not complete - see the documentation for the
    PropertyValueList class, defined in properties_value.py.
    """
    
    def __init__(self, listType=None, minlen=None, maxlen=None, **kwargs):
        """

        Parameters (all optional):
          - listType: A PropertyBase type, specifying the values allowed
                      in the list. If None, anything can be stored in the
                      list.
                
          - minlen:   minimum list length
          - maxlen:   maximum list length
        """

        if (listType is not None) and \
           (not isinstance(listType, props.PropertyBase)):
            raise ValueError(
                'A list type (a PropertyBase instance) must be specified')

        kwargs['default'] = kwargs.get('default', [])
        kwargs['minlen']  = minlen
        kwargs['maxlen']  = maxlen

        props.ListPropertyBase.__init__(self, listType,  **kwargs)


    def validate(self, instance, value):
        """
        Checks that the given value (which should be a list) meets the
        minlen/maxlen constraints. Raises a ValueError if it does not.
        """

        minlen = self.getConstraint(instance, 'minlen')
        maxlen = self.getConstraint(instance, 'maxlen')

        if minlen is not None and len(value) < minlen:
            raise ValueError('Must have length at least {}'.format(minlen))
        if maxlen is not None and len(value) > maxlen:
            raise ValueError('Must have length at most {}'.format(maxlen))
     

# TODO This might be better off as a subclass of Choice. 
class ColourMap(props.PropertyBase):
    """
    A property which encapsulates a matplotlib.colors.Colormap.
    """

    def __init__(self, **kwargs):
        """
        Creates a ColourMap property. If a default value is not
        given, the matplotlib.cm.Greys_r colour map is used.
        """

        default = kwargs.get('default', None)

        if default is None:
            default = mplcm.Greys_r
            
        elif isinstance(default, str):
            default = mplcm.get_cmap(default)
            
        elif not isinstance(default, mplcolors.Colormap):
            raise ValueError(
                'Invalid  ColourMap default: '.format(
                    default.__class__.__name__))

        kwargs['default'] = default
        props.PropertyBase.__init__(self, **kwargs)


    def cast(self, instance, value):
        """
        If the provided value is a string, an attempt is made
        to convert it to a colour map, via the
        matplotlib.cm.get_cmap function.
        """

        if isinstance(value, str):
            value = mplcm.get_cmap(value)
            
        return value


class BoundsValueList(propvals.PropertyValueList):
    """
    A list of values which represent bounds along a number of
    dimensions. This class just adds some convenience methods
    and attributes.  For a single dimension, a bound object
    has a 'lo' value and a 'hi' value, specifying the bounds
    along that dimension.
    """

    def __init__(self, *args, **kwargs):
        propvals.PropertyValueList.__init__(self, *args, **kwargs)

    def getLo(self, axis):
        return self[axis * 2]
        
    def getHi(self, axis):
        return self[axis * 2 + 1]

    def getRange(self, axis):
        return [self.getLo(axis), self.getHi(axis)]

    def getLen(self, axis):
        return abs(self.getHi(axis) - self.getLo(axis))

    def setLo(self, axis, value):
        self[axis * 2] = value
        
    def setHi(self, axis, value):
        self[axis * 2 + 1] = value

    def setRange(self, axis, values):
        self.setMin(axis, values[0])
        self.setMax(axis, values[1])

    def getMin(self, axis):
        return self.getPropertyValueList()[axis * 2].getAttribute('minval')
        
    def getMax(self, axis):
        return self.getPropertyValueList()[axis * 2 + 1].getAttribute('maxval') 

    def setMin(self, axis, value):
        self.getPropertyValueList()[axis * 2]    .setAttribute('minval', value)
        self.getPropertyValueList()[axis * 2 + 1].setAttribute('minval', value)
        
    def setMax(self, axis, value):
        self.getPropertyValueList()[axis * 2]    .setAttribute('maxval', value)
        self.getPropertyValueList()[axis * 2 + 1].setAttribute('maxval', value) 
            
    def __getattr__(self, name):

        lname = name.lower()

        if   lname == 'x':    return self.getRange(0)
        elif lname == 'y':    return self.getRange(1)
        elif lname == 'z':    return self.getRange(2)
        elif lname == 'xlo':  return self.getLo(   0)
        elif lname == 'xhi':  return self.getHi(   0)
        elif lname == 'ylo':  return self.getLo(   1)
        elif lname == 'yhi':  return self.getHi(   1)
        elif lname == 'zlo':  return self.getLo(   2)
        elif lname == 'zhi':  return self.getHi(   2)
        elif lname == 'xlen': return self.getLen(  0)
        elif lname == 'ylen': return self.getLen(  1)
        elif lname == 'zlen': return self.getLen(  2)
        elif lname == 'all':  return self[:]

        raise AttributeError('{} has no attribute called {}'.format(
            self.__class__.__name__, name))

    def __setattr__(self, name, value):

        lname = name.lower()
        
        if   lname == 'x':    self.setRange(0, value)
        elif lname == 'y':    self.setRange(1, value)
        elif lname == 'z':    self.setRange(2, value)
        elif lname == 'xlo':  self.setLo(   0, value)
        elif lname == 'xhi':  self.setHi(   0, value)
        elif lname == 'ylo':  self.setLo(   1, value)
        elif lname == 'yhi':  self.setHi(   1, value)
        elif lname == 'zlo':  self.setLo(   2, value)
        elif lname == 'zhi':  self.setHi(   2, value)
        elif lname == 'all':  self[:] = value
        else:                 self.__dict__[name] = value


class Bounds(List):
    """
    Property which represents numeric bounds in any number of dimensions.
    Bound values are stored in a BoundValueList, a list of floating point
    values, two values (lo, hi) for each dimension.  

    Bound values may also have bounds of their own, i.e. minimium/maximum
    values that the bound values can take. These bound-limits are referred
    to as 'min' and 'max', and can be set via the BoundValueList
    setMin/setMax methods. The advantage to using these methods, instead
    of using HasProperties.setItemConstraint, is that if you use the latter
    you will have to set the constraints on both the low and the high
    values.
    """

    def __init__(self,
                 ndims=1,
                 minDistance=None,
                 editLimits=False,
                 labels=None,
                 **kwargs):
        """
        Initialise a Bounds property. Parameters:
          - ndims:       Number of dimensions. This is (currently) not a
                         property constraint, hence it cannot be changed
                         on HasProperties instances.
          - minDistance: Minimum distance to be maintained between the
                         low/high values for each dimension.
          - editLimits:  If True, widgets created to edit this Bounds
                         will allow the user to edit the min/max limits
          - labels:      List of labels of length (2*ndims), containing
                         (low, high) labels for each dimension.
        """

        default = kwargs.get('default', None)

        if default is None:
            default = [0.0, 0.0] * ndims

        if ndims < 1 or ndims > 3:
            raise ValueError('Only bounds of one to three '
                             'dimensions are supported')

        elif len(default) != 2 * ndims:
            raise ValueError('{} bound values are required'.format(2 * ndims))

        if labels is not None and len(labels) != 2 * ndims:
            raise ValueError('A label for each dimension is required')

        if minDistance is None:
            minDistance = 0

        kwargs['default']     = default
        kwargs['minDistance'] = minDistance
        kwargs['editLimits']  = editLimits

        self._ndims  = ndims
        self._labels = labels

        List.__init__(self,
                      listType=Real(clamped=True, editLimits=editLimits),
                      minlen=ndims * 2,
                      maxlen=ndims * 2,
                      **kwargs)

        
    def _makePropVal(self, instance):
        """
        Overrides ListPropertyBase._makePropVal - creates and returns a
        BoundsValueList instead of a PropertyValueList, so callers get
        to use the convenience methods/attributes defined in the BVL
        class.
        """

        bvl = BoundsValueList(
            instance,
            name=self._label,
            values=self._default,
            itemCastFunc=self._listType.cast,
            itemValidateFunc=self._listType.validate,
            listValidateFunc=self.validate,
            allowInvalid=False,
            postNotifyFunc=self._valChanged,
            listAttributes=self._defaultConstraints,
            itemAttributes=self._listType._defaultConstraints)
        
        return bvl

        
    def validate(self, instance, value):
        """
        Raises a ValueError if the given value (a list of min/max values)
        is of the wrong length or data type, or if any of the min values
        are greater than the corresponding max value.
        """

        minDistance = self.getConstraint(instance, 'minDistance')

        # the List.validate method will check
        # the value length and type for us
        List.validate(self, instance, value)

        for i in range(self._ndims):

            imin = value[i * 2]
            imax = value[i * 2 + 1]

            if imin > imax:
                raise ValueError('Minimum bound must be smaller '
                                 'than maximum bound (dimension {}, '
                                 '{} - {}'.format(i, imin, imax))

            if imax - imin < minDistance:
                raise ValueError('Minimum and maximum bounds must be at '
                                 'least {} apart'.format(minDistance))


class PointValueList(propvals.PropertyValueList):
    """
    A list of values which represent a point in some n-dimensional space.
    Some convenience methods and attributes are available, including
    GLSL-like swizzling.
    
      [http://www.opengl.org/wiki/Data_Type_(GLSL)#Swizzling]
    """

    def __init__(self, *args, **kwargs):
        propvals.PropertyValueList.__init__(self, *args, **kwargs)

    def getPos(self, axis):
        return self[axis]
        
    def setPos(self, axis, value):
        self[axis] = value

    def getMin(self, axis):
        return self.getPropertyValueList()[axis].getAttribute('minval')
        
    def getMax(self, axis):
        return self.getPropertyValueList()[axis].getAttribute('maxval')

    def setMin(self, axis, value):
        self.getPropertyValueList()[axis].setAttribute('minval', value)
        
    def setMax(self, axis, value):
        self.getPropertyValueList()[axis].setAttribute('maxval', value) 

    def __getattr__(self, name):

        lname = name.lower()

        if any([dim not in 'xyz' for dim in lname]):
            raise AttributeError('{} has no attribute called {}'.format(
                self.__class__.__name__, name))

        res = []
        for dim in lname:
            if   dim == 'x': res.append(self[0])
            elif dim == 'y': res.append(self[1])
            elif dim == 'z': res.append(self[2])
            
        if len(res) == 1: return res[0]
        return res
        
    def __setattr__(self, name, value):

        lname = name.lower()

        if any([dim not in 'xyz' for dim in lname]):
            self.__dict__[name] = value
            return

        if len(lname) == 1:
            value = [value]

        if len(lname) != len(value):
            raise AttributeError('Improper number of values '
                                 '({}) for attribute {}'.format(
                                     len(value), lname))
        
        for dim, val in zip(lname, value):
            if   dim == 'x': self[0] = val
            elif dim == 'y': self[1] = val
            elif dim == 'z': self[2] = val


class Point(List):
    """
    A property which represents a point in some n-dimensional space
    (where n must be either 2 or 3 for the time being).
    """

    def __init__(self, ndims=2, editLimits=False, labels=None, **kwargs):
        """
        Initialise a Point property. Parameters:
        
          - ndims:      Number of dimensions.
          - editLimits: If True, widgets created to edit this Point
                        will allow the user to edit the min/max limits
          - labels:     List of labels, one for each dimension.
        """

        default = kwargs.get('default', None)

        if default is None:
            default = [0.0] * ndims

        if ndims < 2 or ndims > 3:
            raise ValueError('Only points of two to three '
                             'dimensions are supported')
            
        elif len(default) != ndims:
            raise ValueError('{} point values are required'.format(ndims))

        if labels is not None and len(labels) != ndims:
            raise ValueError('A label for each dimension is required')

        kwargs['default']    = default
        kwargs['editLimits'] = editLimits
        
        self._ndims  = ndims
        self._labels = labels

        List.__init__(self,
                      listType=Real(clamped=True, editLimits=editLimits),
                      minlen=ndims,
                      maxlen=ndims,
                      **kwargs)

        
    def _makePropVal(self, instance):
        """
        Overrides ListPropertyBase._makePropVal - creates and returns a
        PointjValueList instead of a PropertyValueList, so callers get
        to use the convenience methods/attributes defined in the PVL
        class.
        """

        pvl = PointValueList(
            instance,
            name=self._label,
            values=self._default,
            itemCastFunc=self._listType.cast,
            itemValidateFunc=self._listType.validate,
            listValidateFunc=self.validate,
            allowInvalid=False,
            postNotifyFunc=self._valChanged,
            listAttributes=self._defaultConstraints,
            itemAttributes=self._listType._defaultConstraints)
        
        return pvl
