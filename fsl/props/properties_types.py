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

        
    def validate(self, instance, value):
        props.PropertyBase.validate(self, instance, value)

        if not isinstance(value, bool):
            raise ValueError('Must be a boolean')


class Number(props.PropertyBase):
    """
    Base class for the Int and Double classes. Don't
    use/subclass this, use/subclass one of Int or Double.
    """
    
    def __init__(self, minval=None, maxval=None, **kwargs):
        """
        Optional parameters:
          - minval
          - maxval
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

        kwargs['default'] = default
        kwargs['minval']  = minval
        kwargs['maxval']  = maxval
        props.PropertyBase.__init__(self, **kwargs)

        
    def validate(self, instance, value):
        
        props.PropertyBase.validate(self, instance, value)

        if not isinstance(value, numbers.Number):
            raise ValueError('Must be a number')
        
        minval = self.getConstraint(instance, 'minval')
        maxval = self.getConstraint(instance, 'maxval')

        if minval is not None and value < minval:
            raise ValueError('Must be at least {}'.format(minval))
            
        if maxval is not None and value > maxval:
            raise ValueError('Must be at most {}'.format(maxval))

        
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

        Number.validate(self, instance, value)

        if not isinstance(value, numbers.Integral):
            raise ValueError('Must be an integer')
        

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

        
    def validate(self, instance, value):
        
        Number.validate(self, instance, value)
        
        if not isinstance(value, numbers.Real):
            raise ValueError('Must be a floating point number') 
        

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

        
    def __set__(self, instance, value):
        
        if value == '': value = None
        props.PropertyBase.__set__(self, instance, value)

    def __get__(self, instance, owner):

        val = props.PropertyBase.__get__(self, instance, owner)
        if val == '': val = None
        return val

        
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


class List(props.PropertyBase):
    """
    A property which represents a list of items, of another property type.
    List functionality is not complete - see the documentation for the
    PropertyValueList class, defined in properties_value.py

    This class is a bit different from the other PropertyBase classes, in
    that the validation logic is built into the ListWrapper class, rather
    than this class. 
    """
    
    def __init__(self, listType, minlen=None, maxlen=None, **kwargs):
        """
        Mandatory parameters:
          - listType: A PropertyBase type, specifying the values allowed
                      in the list
        
        Optional parameters:

          - minlen:   minimum list length
          - maxlen:   maximum list length
        """

        if listType is None or not isinstance(listType, props.PropertyBase):
            raise ValueError(
                'A list type (a PropertyBase instance) must be specified')

        self._listType = listType

        kwargs['default'] = kwargs.get('default', [])

        props.PropertyBase.__init__(self, **kwargs)

        
    def _makePropVal(self, instance):
        """
        Creates and returns a PropertyValueList object.
        """
        minlen = self.getConstraint(instance, 'minlen')
        maxlen = self.getConstraint(instance, 'maxlen') 
        instval = props.PropertyValueList(instance,
                                          self,
                                          listType=self._listType,
                                          minlen=minlen,
                                          maxlen=maxlen)
        return instval

    def validate(self, instance, value):

        minlen = self.getConstraint(instance, 'minlen')
        maxlen = self.getConstraint(instance, 'maxlen')

        if minlen is not None and len(value) < minlen:
            raise ValueError('')
        if maxlen is not None and len(value) > maxlen:
            raise ValueError('')

        for v in value:
            self._listType.validate(None, v)
     

# TODO This might be better off as a subclass of Choice. Choice
# would need to be modified to allow for values of any type, not
# just Strings. Shouldn't be a major issue.
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


    def __set__(self, instance, value):
        """
        Set the current ColourMap property value. If a string
        is given, an attempt is made to convert it to a colour map,
        via the matplotlib.cm.get_cmap function.
        """

        if isinstance(value, str):
            value = mplcm.get_cmap(value)
            
        elif not isinstance(value, mplcolors.Colormap):
            raise ValueError(
                'Invalid  ColourMap value: '.format(
                    value.__class__.__name__))

        props.PropertyBase.__set__(self, instance, value)
