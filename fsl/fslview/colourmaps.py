#!/usr/bin/env python
#
# colourmaps.py - Manage colour maps and lookup tables for overlay rendering.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Module which manages the colour maps and lookup tables available for
overlay rendering.


The :func:`init` function must be called before any colour maps or lookup
tables can be accessed. When :func:`init` is called, it searches in the
``fsl/fslview/colourmaps/`` and ``fsl/fslview/luts/``directories, and attempts
to load all files within which have the suffix ``.cmap`` or ``.lut``
respectively.


-----------
Colour maps
-----------


A ``.cmap`` file defines a colour map which may be used to display a range of
intensity values - see the :attr:`.VolumeOpts.cmap` property for an example. A
``.cmap`` file must contain a list of RGB colours, one per line, with each
colour specified by three space-separated floating point values in the range
0.0 - 1.0, for example::


        1.000000 0.260217 0.000000
        0.000000 0.687239 1.000000
        0.738949 0.000000 1.000000


This list of RGB values is used to create a :class:`.ListedColormap` object,
which is then registered with the :mod:`matplotlib.cm` module (using the file
name prefix as the colour map name), and thus made available for rendering
purposes.


If a file named ``order.txt`` exists in the ``fsl/fslview/colourmaps/``
directory, it is assumed to contain a list of colour map names, and colour map
identifiers, defining the order in which the colour maps should be displayed
to the user. Any colour maps which are not listed in the ``order.txt`` file
will be appended to the end of the list, and their name will be derived from
the file name.


This module provides a number of functions, the most important of which are:

 - :func:`getColourMaps`:         Returns a list of the names of all available
                                  colourmaps.

 - :func:`registerColourMap`:     Given a text file containing RGB values,
                                  loads the data and registers it  with
                                  :mod:`matplotlib`.

 - :func:`installColourMap`:

 - :func:`isColourMapRegistered`: 

 - :func:`isColourMapInstalled`:  


-------------
Lookup tables
-------------


A `.lut` file defines a lookup table which may be used to display images
wherein each voxel has a discrete integer label. Each of the possible voxel
values such an image has an associated colour and name. Each line in a
``.lut`` file must specify the label value, RGB colour, and associated name.
The first column (where columns are space-separated) defines the label value,
the second to fourth columns specify the RGB values, and all remaining columns
give the label name. For example::


        1  0.00000 0.93333 0.00000 Frontal Pole
        2  0.62745 0.32157 0.17647 Insular Cortex
        3  1.00000 0.85490 0.72549 Superior Frontal Gyrus


 - :func:`getLookupTables`:

 - :func:`registerLookupTable`:

 - :func:`installLookupTable`:

 - :func:`isLookupTableRegistered`: 

 - :func:`isLookupTableInstalled`:

 - :func:`saveLookupTable`:         TODO - update an installed lookup table


-------------
Miscellaneous
-------------


Some utility functions are also kept in this module, related to calculating
the relationship between a data display range and brightness/contrast scales,
and generating/manipulating colours.:

 - :func:`displayRangeToBricon`: Given a data range, converts a display range
                                 to brightness/contrast values.

 - :func:`briconToDisplayRange`: Given a data range, converts brigtness/
                                 contrast values to a display range.

 - :func:`applyBricon`:          Given a RGB colour, brightness, and contrast
                                 value, scales the colour according to the
                                 brightness and contrast.

 - :func:`randomColour`:         Generates a random RGB colour.

 - :func:`randomBrightColour`:   Generates a random saturated RGB colour.

"""

import glob
import shutil
import os.path as op

from collections import OrderedDict

import numpy             as np
import matplotlib.colors as colors
import matplotlib.cm     as mplcm

import logging


log = logging.getLogger(__name__)


_cmapDir = op.join(op.dirname(__file__), 'colourmaps')
_lutDir  = op.join(op.dirname(__file__), 'luts')

_cmaps   = None
_luts    = None


class _Map(object):
    """A little class for storing details on each installed/available
    colour map/lookup table. This class is only used internally.
    """

    def __init__(self, name, mapObj, mapFile, installed):
        """
        :arg name:       The name of the colour map/lookup table.

        :arg mapObj:     The colourmap/lut object, either a
                        :class:`matplotlib.col.lors..Colormap`, or a
                        :class:`LookupTable` instance.

        :arg mapFile:    The file from which this map was loaded,
                         or ``None`` if this cmap/lookup table only
                         exists in memory, or is a built in :mod:`matplotlib`
                         colourmap.

        :arg installed:  ``True`` if this is a built in :mod:`matplotlib`
                         colourmap or is installed in the
                         ``fsl/fslview/colourmaps/`` or ``fsl/fslview/luts/``
                         directory, ``False`` otherwise.
        """
        self.name      = name
        self.mapObj    = mapObj
        self.mapFile   = mapFile
        self.installed = installed

        
    def __str__(self):
        if self.mapFile is not None: return self.mapFile
        else:                        return self.name

        
    def __repr__(self):
        return self.__str__()

    
class LookupTable(object):
    """Class which encapsulates a list of labels and associated colours and names,
    defining a lookup table to be used for colouring label images.
    """

    
    def __init__(self, lutName):
        self.__lutName = lutName
        self.__names   = {}
        self.__enabled = {}
        self.__colours = {}


    def __len__(self):
        return len(self.__names.keys())

        
    def lutName(self):
        return self.__lutName


    def values(self):
        return sorted(self.__names.keys())


    def names(self):
        return [self.__names[v] for v in self.values()]

    
    def colours(self):
        return [self.__colours[v] for v in self.values()]

    
    def name(self, value):
        return self.__names[value]

        
    def colour(self, value):
        return self.__colours[value]


    def enabled(self, value):
        return self.__enabled[value]


    def set(self, value, **kwargs):

        # At the moment, we are restricting
        # lookup tables to be unsigned 16 bit.
        # See gl/textures/lookuptabletexture.py
        if not isinstance(value, (int, long)) or \
           value < 0 or value > 65535:
            raise ValueError('Lookup table values must be '
                             '16 bit unsigned integers.')

        name    = kwargs.get('name',    self.__names  .get(value, 'Label'))
        colour  = kwargs.get('colour',  self.__colours.get(value, (0, 0, 0)))
        enabled = kwargs.get('enabled', self.__enabled.get(value, True))
          
        self.__names[  value] = name
        self.__colours[value] = colour
        self.__enabled[value] = enabled


    def load(self, lutFile):
        
        with open(lutFile, 'rt') as f:
            lines = f.readlines()

            for line in lines:
                tkns = line.split()

                label = int(     tkns[0])
                r     = float(   tkns[1])
                g     = float(   tkns[2])
                b     = float(   tkns[3])
                lName = ' '.join(tkns[4:])

                self.set(label, name=lName, colour=(r, g, b), enabled=True)

        return self


def init():
    """This function must be called before any of the other functions in this
    module can be used.

    It initialises the colour map and lookup table registers, loading all
    colour map and lookup table files that exist.
    """

    global _cmaps
    global _luts

    registers = []

    if _cmaps is None:
        _cmaps = OrderedDict()
        registers.append((_cmaps, _cmapDir, 'cmap'))

    if _luts is None:
        _luts = OrderedDict()
        registers.append((_luts, _lutDir, 'lut'))

    if len(registers) == 0:
        return

    for register, rdir, suffix in registers:

        # Build up a list of key -> name mappings,
        # from the order.txt file, and any other
        # colour map/lookup table  files in the
        # cmap/lut directory
        allmaps   = OrderedDict()
        orderFile = op.join(rdir, 'order.txt')

        if op.exists(orderFile):
            with open(orderFile, 'rt') as f:
                lines = f.read().split('\n')

                for line in lines:
                    if line.strip() == '':
                        continue
                    
                    # The order.txt file is assumed to
                    # contain one row per cmap/lut,
                    # where the first word is the key
                    # (the cmap/lut file name prefix),
                    # and the remainder of the line is
                    # the cmap/lut name
                    key, name = line.split(' ', 1)

                    allmaps[key.strip()] = name.strip()

        # Search through all cmap/lut files that exist -
        # any which were not specified in order.txt
        # are added to the end of the list, and their
        # name is just set to the file name prefix
        for mapFile in sorted(glob.glob(op.join(rdir, '*.{}'.format(suffix)))):

            name = op.basename(mapFile).split('.')[0]

            if name not in allmaps:
                allmaps[name] = name

        # Now load all of the cmaps/luts
        for key, name in allmaps.items():
            mapFile = op.join(rdir, '{}.{}'.format(key, suffix))

            try:
                if   suffix == 'cmap': registerColourMap(  mapFile, name)
                elif suffix == 'lut':  registerLookupTable(mapFile, name)
                
                register[name].installed = True

            except Exception as e:
                log.warn('Error processing custom {} '
                         'file {}: {}'.format(suffix, mapFile, str(e)))


def registerColourMap(cmapFile, name=None):
    """Loads RGB data from the given file, and registers
    it as a :mod:`matplotlib` :class:`~matplotlib.colors.ListedColormap`
    instance.

    :arg cmapFile: Name of a file containing RGB values
    
    :arg name:     Name to give the colour map. If ``None``, defaults
                   to the file name prefix.
    """
    if name is None:
        name = op.basename(cmapFile).split('.')[0]

    data = np.loadtxt(cmapFile)
    cmap = colors.ListedColormap(data, name)

    log.debug('Loading and registering custom '
              'colour map: {}'.format(cmapFile))

    mplcm.register_cmap(name, cmap)

    _cmaps[name] = _Map(name, cmap, cmapFile, False)
                

def registerLookupTable(lut, name=None):

    if isinstance(lut, basestring): lutFile = lut
    else:                           lutFile = None

    # lut may be either a file name
    # or a LookupTable instance
    if lutFile is not None:

        if name is None:
            name = op.basename(lutFile).split('.')[0]

        log.debug('Loading and registering custom '
                  'lookup table: {}'.format(lutFile)) 
        
        lut = LookupTable(name).load(lutFile)

    _luts[name] = _Map(name, lut, lutFile, False)


def getLookupTables():
    """Returns a list containing all available lookup tables."""
    return [_luts[lutName].mapObj for lutName in _luts.keys()]

        
def getColourMaps():
    """Returns a list containing the names of all available colour maps."""
    return  _cmaps.keys()


def isColourMapRegistered(cmapName):
    """Returns ``True`` if the specified colourmap is registered, ``False``
    otherwise. 
    """ 
    return cmapName in _cmaps


def isLookupTableRegistered(lutName):
    """Returns ``True`` if the specified lookup table is registered, ``False``
    otherwise. 
    """ 
    return lutName in _luts


def isColourMapInstalled(cmapName):
    """Returns ``True`` if the specified colourmap is installed, ``False``
    otherwise.  A ``KeyError`` is raised if the colourmap is not registered.
    """
    return _cmaps[cmapName].installed


def isLookupTableInstalled(lutName):
    """Returns ``True`` if the specified loolup table is installed, ``False``
    otherwise.  A ``KeyError`` is raised if the lookup tabler is not
    registered.
    """
    return _luts[lutName].installed 


def installColourMap(cmapName):
    """Attempts to install a previously registered colourmap into the
    ``fsl/fslview/colourmaps`` directory.

    A ``KeyError`` is raised if the colourmap is not registered, a
    ``RuntimeError`` if the colourmap cannot be installed, or an
    ``IOError`` if the colourmap file cannot be copied.
    """

    # keyerror if not registered
    cmap = _cmaps[cmapName]

    # built-in, or already installed
    if cmap.installed:
        return

    # cmap has been incorrectly registered
    if cmap.mapFile is None:
        raise RuntimeError('Colour map {} appears to have been '
                           'incorrectly registered'.format(cmapName))

    destfile = op.join(op.dirname(__file__),
                       'colourmaps',
                       '{}.cmap'.format(cmapName))

    # destination file already exists
    if op.exists(destfile):
        raise RuntimeError('Destination file for colour map {} already '
                           'exists: {}'.format(cmapName, destfile))

    log.debug('Installing colour map {} to {}'.format(cmapName, destfile))
        
    shutil.copyfile(cmap.cmfile, destfile)


def installLookupTable(lutName):
    
    # keyerror if not registered
    lut = _luts[lutName]

    # built-in, or already installed
    if lut.installed:
        return

    # cmap has been incorrectly registered
    if lut.mapFile is None:
        raise RuntimeError('Lookup table {} appears to have been '
                           'incorrectly registered'.format(lutName))
    
    log.warn('Lookup table installation not implemented yet')


###############
# Miscellaneous
###############


def briconToDisplayRange(dataRange, brightness, contrast):
    """Converts the given brightness/contrast values to a display range,
    given the data range.

    :arg dataRange:  The full range of the data being displayed, a
                     (min, max) tuple.
    
    :arg brightness: A brightness value between 0 and 1.
    
    :arg contrast:   A contrast value between 0 and 1.
    """

    # Turn the given bricon values into
    # values between 1 and 0 (inverted)
    brightness = 1.0 - brightness
    contrast   = 1.0 - contrast

    dmin, dmax = dataRange
    drange     = dmax - dmin
    dmid       = dmin + 0.5 * drange

    # The brightness is applied as a linear offset,
    # with 0.5 equivalent to an offset of 0.0.                
    offset = (brightness * 2 - 1) * drange

    # If the contrast lies between 0.0 and 0.5, it is
    # applied to the colour as a linear scaling factor.
    scale = contrast * 2

    # If the contrast lies between 0.5 and 1, it
    # is applied as an exponential scaling factor,
    # so lower values (closer to 0.5) have less of
    # an effect than higher values (closer to 1.0).
    if contrast > 0.5:
        scale += np.exp((contrast - 0.5) * 6) - 1

    # Calculate the new display range, keeping it
    # centered in the middle of the data range
    # (but offset according to the brightness)
    dlo = (dmid + offset) - 0.5 * drange * scale 
    dhi = (dmid + offset) + 0.5 * drange * scale

    return dlo, dhi


def displayRangeToBricon(dataRange, displayRange):
    """Converts the given brightness/contrast values to a display range,
    given the data range.

    :arg dataRange:    The full range of the data being displayed, a
                       (min, max) tuple.
    
    :arg displayRange: A (min, max) tuple containing the display range.
    """    

    dmin, dmax = dataRange
    dlo,  dhi  = displayRange
    drange     = dmax - dmin
    dmid       = dmin + 0.5 * drange

    # These are inversions of the equations in
    # the briconToDisplayRange function above,
    # which calculate the display ranges from
    # the bricon offset/scale
    offset = dlo + 0.5 * (dhi - dlo) - dmid
    scale  = (dhi - dlo) / drange

    brightness = 0.5 * (offset / drange + 1)

    if scale <= 1: contrast = scale / 2.0
    else:          contrast = np.log(scale + 1) / 6.0 + 0.5

    brightness = 1.0 - brightness
    contrast   = 1.0 - contrast

    return brightness, contrast


def applyBricon(rgb, brightness, contrast):
    """Applies the given ``brightness`` and ``contrast`` levels to
    the given ``rgb`` colour(s).

    Passing in ``0.5`` for both the ``brightness``  and ``contrast`` will
    result in the colour being returned unchanged.

    :arg rgb:        A sequence of three or four floating point numbers in 
                     the range ``[0, 1]`` specifying an RGB(A) value, or a
                     :mod:`numpy` array of shape ``(n, 3)`` or ``(n, 4)``
                     specifying ``n`` colours. If alpha values are passed
                     in, they are returned unchanged.

    :arg brightness: A brightness level in the range ``[0, 1]``.

    :arg contrast:   A brightness level in the range ``[0, 1]``.
    """
    rgb = np.array(rgb)
    rgb = rgb.reshape(-1, rgb.shape[-1])

    # The brightness is applied as a linear offset,
    # with 0.5 equivalent to an offset of 0.0.
    offset = (brightness * 2 - 1)

    # If the contrast lies between 0.0 and 0.5, it is
    # applied to the colour as a linear scaling factor.
    scale = contrast * 2

    # If the contrast lies between 0.5 and 0.1, it
    # is applied as an exponential scaling factor,
    # so lower values (closer to 0.5) have less of
    # an effect than higher values (closer to 1.0).
    if (contrast > 0.5):
        scale += np.exp((contrast - 0.5) * 6) - 1

    # The contrast factor scales the existing colour
    # range, but keeps the new range centred at 0.5.
    rgb[:, :3] += offset
  
    rgb[:, :3]  = np.clip(rgb[:, :3], 0.0, 1.0)
    rgb[:, :3]  = (rgb[:, :3] - 0.5) * scale + 0.5
  
    return np.clip(rgb[:, :3], 0.0, 1.0)


def randomColour():
    """Generates a random RGB colour. """
    return np.random.random(3)


def randomBrightColour():
    """Generates a random saturated RGB colour. """
    colour                  = np.random.random(3)
    colour[colour.argmax()] = 1
    colour[colour.argmin()] = 0

    np.random.shuffle(colour)

    return colour
