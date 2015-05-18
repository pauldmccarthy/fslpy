#!/usr/bin/env python
#
# colourmaps.py - Manage colour maps for overlay rendering.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Module which manages the colour maps available for overlay rendering.

When this module is first initialised, it searches in the
``fsl/fslview/colourmaps/`` directory, and attempts to load all files within
which have the suffix ``.cmap``. Such a file is assumed to contain a list of
RGB colours, one per line, with each colour specified by three space-separated
floating point values in the range 0.0 - 1.0.

This list of RGB values is used to create a
:class:`matplotlib.colors.ListedColormap` object, which is then registered
with the :mod:`matplotlib.cm` module (using the file name prefix as the colour
map name), and thus made available for rendering purposes.

If a file named ``order.txt`` exists in the ``fsl/fslview/colourmaps/``
directory, it is assumed to contain a list of colour map names, and colour map
identifiers, defining the order in which the colour maps should be displayed
to the user. Any colour maps which are not listed in the ``order.txt`` file
will be appended to the end of the list.

This module provides a number of functions, the most important of which are:

 - :func:`initColourMaps`:    This function must be called before any of the
                              other functions will work. It loads all present
                              colourmap files.

 - :func:`getDefault`:        Returns the name of the colourmap to be used
                              as the default.

 - :func:`getColourMaps`:     Returns a list of the names of all available
                              colourmaps.

 - :func:`registerColourMap`: Given a text file containing RGB values,
                              loads the data and registers it  with
                              :mod:`matplotlib`.


Some utility functions are also kept in this module, related to calculating
the relationship between a data display range, and brightness/contrast
scales:

 - :func:`displayRangeToBricon`: Given a data range, converts a display range
                                 to brightness/contrast values.

 - :func:`briconToDisplayRange`: Given a data range, converts brigtness/
                                 contrast values to a display range.
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
_cmaps   = None


class _ColourMap(object):
    """A little struct for storing details on each installed/available
    colour map.
    """

    def __init__(self, name, cmfile, installed):
        """
        :arg name:       The name of the colour map (as registered with
                         :mod:`matplotlib.cm`).

        :arg cmfile:     The file from which this colour map was loaded,
                         or ``None`` if this is a built in :mod:`matplotlib`
                         colourmap.

        :arg installed:  ``True`` if this is a built in :mod:`matplotlib`
                         colourmap or is installed in the
                         ``fsl/fslview/colourmaps/`` directory, ``False``
                         otherwise.
        """
        self.name      = name
        self.cmfile    = cmfile
        self.installed = installed

    def __str__(self):
        if self.cmfile is not None: return self.cmfile
        else:                       return self.name
        
    def __repr__(self):
        return self.__str__()

        
def getDefault():
    """Returns the name of the default colour map."""
    return getColourMaps()[0]


def getColourMaps():
    """Returns a list containing the names of all available colour maps."""
    return  _cmaps.keys()


def isRegistered(cmapName):
    """Returns ``True`` if the specified colourmap is registered, ``False``
    otherwise. 
    """ 
    return cmapName in _cmaps


def isInstalled(cmapName):
    """Returns ``True`` if the specified colourmap is installed, ``False``
    otherwise.  A ``KeyError`` is raised if the colourmap is not registered.
    """
    return _cmaps[cmapName].installed


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
    if cmap.cmfile is None:
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

    _cmaps[name] = _ColourMap(name, cmapFile, False)

    
# Load all custom colour maps from the colourmaps/*.cmap files,
# honouring the naming/order specified in order.txt (if it exists).
def initColourMaps():
    """This function must be called before any of the other functions in this
    module can be used.

    It initialises the colour map 'register', loading all colour map files
    that exist.
    """

    global _cmaps

    if _cmaps is not None:
        return

    _cmaps = OrderedDict()

    # Build up a list of cmapKey -> cmapName
    # mappings, from the order.txt file, and
    # any other colour map files in the cmap
    # directory
    allcmaps  = OrderedDict()
    orderFile = op.join(_cmapDir, 'order.txt')

    if op.exists(orderFile):
        with open(orderFile, 'rt') as f:
            lines = f.read().split('\n')

            for line in lines:
                if line.strip() == '':
                    continue
                # The order.txt file is assumed to
                # contain one row per colour map,
                # where the first word is the colour
                # map key (the cmap file name prefix),
                # and the remainder of the line is
                # the colour map name
                key, name = line.split(' ', 1)

                allcmaps[key.strip()] = name.strip()

    # Search through all cmap files that exist -
    # any which were not specified in order.txt
    # are added to the end of the list, and their
    # name is just set to the file name prefix
    for cmapFile in sorted(glob.glob(op.join(_cmapDir, '*.cmap'))):

        name = op.basename(cmapFile).split('.')[0]

        if name not in allcmaps:
            allcmaps[name] = name

    # Now load all of the colour maps
    for key, name in allcmaps.items():
        cmapFile = op.join(_cmapDir, '{}.cmap'.format(key))
        
        try:
            registerColourMap(cmapFile, name)
            _cmaps[name].installed = True

        except:
            log.warn('Error processing custom colour '
                     'map file: {}'.format(cmapFile))


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
    the given ``rgb`` colour.

    :arg rgb:        A sequence of three floating point numbers in the 
                     range ``[0, 1]`` specifying an RGB value.

    :arg brightness: A brightness ledvel in the range ``[0, 1]``.

    :arg contrast:   A brightness ledvel in the range ``[0, 1]``.
    """
    rgb = np.array(rgb)

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
    rgb += offset
  
    rgb  = np.clip(rgb, 0.0, 1.0)
    rgb  = (rgb - 0.5) * scale + 0.5
  
    return np.clip(rgb, 0.0, 1.0)
