#!/usr/bin/env python
#
# properties_types.py - Definitions for different property types - see
# properties.py for more information.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op

import numbers

import matplotlib.colors as mplcolors
import matplotlib.cm     as mplcm

import properties as props

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
    Base class for the Int and Double classes. Don't
    use/subclass this, use/subclass one of Int or Double.
    """
    
    def __init__(self,
                 minval=None,
                 maxval=None,
                 clamped=False,
                 editBounds=False,
                 **kwargs):
        """
        Optional parameters:
          - minval:     Minimum value
          - maxval:     Maximum value
          - clamped:    If True, the value will be clamped to its min/max
                        bounds.
          - editBounds: If True, widgets created to modify Number properties
                        will allow the user to change the min/max bounds.
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
        kwargs['editBounds'] = editBounds
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
        

class Double(Number):
    """
    A property which encapsulates a double.  TODO Double is a silly name.
    Change it to Real.
    """
    
    def __init__(self, **kwargs):
        """
        Double constructor. See the Number class for keyword
        arguments.
        """
        Number.__init__(self, **kwargs)


    def cast(self, instance, value):
        return Number.cast(self, instance, float(value))
        

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


class _BoundObject(object):
    """
    An which represents bounds (minimum/maximum values) along
    a number of dimensions (up to 3). The Bounds property type
    uses a _BoundObject to expose its values.
    """

    def __init__(self, ndims, initVal, boundProp, instance):

        if ndims < 1 or ndims > 3:
            raise ValueError('Only one to three dimensions are supported')
        if len(initVal) != 2 * ndims:
            raise ValueError('Wrong number of initial '
                             'values ({} != {})'.format(
                                 len(initVal), 2 * ndims))
        
        self.__dict__['_ndims']     = ndims
        self.__dict__['_boundProp'] = boundProp
        self.__dict__['_instance']  = instance
        self.__dict__['_boundVals'] = initVal


    def __str__(self):
        ndims  = self._ndims
        bounds = self._boundVals
        dims   = ['({}, {})'.format(bounds[i * 2],
                                    bounds[i * 2 + 1])
                  for i in range(ndims)]
        
        return '[{}]'.format(' '.join(dims))

    def __getitem__(self, key):
        return self._boundVals.__getitem__(key)
        
    def __setitem__(self, key, value):
        self._boundVals.__setitem__(key)

    def getmin(self, axis):
        return self._boundVals[axis * 2]
        
    def getmax(self, axis):
        return self._boundVals[axis * 2 + 1]

    def getrange(self, axis):
        return [self.min(axis), self.max(axis)]

    def getlen(self, axis):
        return abs(self.max(axis) - self.min(axis))

    def setmin(self, axis, value):
        self._boundVals[axis * 2] = value
        
    def setmax(self, axis, value):
        self._boundVals[axis * 2 + 1] = value

    def setrange(self, axis, values):
        self.setmin(axis, values[0])
        self.setmax(axis, values[1])
            
    def __getattr__(self, name):

        if   name == 'x':    return self.range(0)
        elif name == 'y':    return self.range(1)
        elif name == 'z':    return self.range(2)
        elif name == 'xmin': return self.min(  0)
        elif name == 'xmax': return self.max(  0)
        elif name == 'ymin': return self.min(  1)
        elif name == 'ymax': return self.max(  1)
        elif name == 'zmin': return self.min(  2)
        elif name == 'zmax': return self.max(  2)
        elif name == 'xlen': return self.len(  0)
        elif name == 'ylen': return self.len(  1)
        elif name == 'zlen': return self.len(  2)
        elif name == 'all':  return list(self._boundVals)

        raise AttributeError('{} has no attribute called {}'.format(
            self.__class__.__name__, name))

        
    def __setattr__(self, name, value):
        
        # could be a single axis name - we return
        # the min/max bounds for that axis
        if   name == 'x':    self.setrange(0, value)
        elif name == 'y':    self.setrange(1, value)
        elif name == 'z':    self.setrange(2, value)
        elif name == 'xmin': self.setmin(  0, value)
        elif name == 'xmax': self.setmax(  0, value)
        elif name == 'ymin': self.setmin(  1, value)
        elif name == 'ymax': self.setmax(  1, value)
        elif name == 'zmin': self.setmin(  2, value)
        elif name == 'zmax': self.setmax(  2, value)
        elif name == 'all':  self._boundVals[:] = value
        else:
            raise AttributeError('{} has no attribute called {}'.format(
                self.__class__.__name__, name)) 

        # and here's the trick
        self._boundProp.__set__(self._instance, self._boundVals)

        
class Bounds(props.PropertyBase):
    """
    Property which represents numeric bounds in any number of dimensions.
    Bound values are stored as a list of floating point values, two values
    (min, max) for each dimension.  _BoundObject instances are created
    whenever an attempt is made to access the property, and used to provide
    convenient getters/setters for the bound values.
    """

    def __init__(self,  ndims=1, **kwargs):

        default = kwargs.get('default', None)

        if default is None:
            default = list([0.0, 0.0] * ndims)
            
        elif len(default) != 2 * ndims:
            raise ValueError('{} bound values are required'.format(2 * ndims))

        kwargs['default'] = default
        self._ndims = ndims

        props.PropertyBase.__init__(self, **kwargs)


    def cast(self, instance, value):
        return list(map(float, value))


    def validate(self, instance, value):
        props.PropertyBase.validate(self, instance, value)

        if len(value) != 2 * self._ndims:
            raise ValueError('{} values required'.format(2 * self._ndims))

        for v in value:
            if not isinstance(v, numbers.Number):
                raise ValueError('Bound values must be numeric')
        

    def __get__(self, instance, owner):
        val   = props.PropertyBase.__get__(self, instance, owner)

        if val is self:
            return val

        return _BoundObject(self._ndims, val, self, instance)
