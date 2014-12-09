#!/usr/bin/env python
#
# colourmaps.py - Manage colour maps for image rendering.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Module which manages the colour maps available for image rendering.

When this module is first initialised, it searches in the
``fsl/fslview/colourmaps/`` directory, and attempts to load all files within
which have the suffix ``.cmap``. Such a file is assumed to contain a list of
RGB colours, one per line, with each colour specified by three space-separated
floating point values in the range 0.0 - 1.0.

This list of RGB values is used to create a
:class:`matplotlib.colors.ListedColormap` object, which is then registered
with the :mod:`matplotlib.cm` module (using the file name prefix as the colour
map name), and thus made available for rendering purposes.

In addition to these custom `.cmap` colour maps, a handful of built-in
matplotlib colour maps are also made available.  The built-in colour maps
which are included are defined by the :attr:`_builtins` list.

This module provides a number of functions, the most important of which are:

 - :func:`getDefault`:        Returns the name of the colourmap to be used
                              as the default.

 - :func:`getColourMaps`:     Returns a list of the names of all available
                              colourmaps.

 - :func:`registerColourMap`: Given a text file containing RGB values,
                              loads the data and registers it  with
                              :mod:`matplotlib`.
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


_default  = 'Greys_r'
_cmaps    = OrderedDict()
_builtins = ['Greys_r'  , 'Greys'  , 'Reds'     , 'Reds_r' , 'Blues'  ,
             'Blues_r'  , 'Greens' , 'Greens_r' , 'pink'   , 'pink_r' ,
             'hot'      , 'hot_r'  , 'cool'     , 'cool_r' , 'autumn' ,
             'autumn_r' , 'copper' , 'copper_r']


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
    return _default


def getColourMaps():
    """Returns a list containing the names of all available colour maps."""
    return  _cmaps.keys()


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
                       '{}.cmap'.forma(cmapName))

    # destination file already exists
    if op.exists(destfile):
        raise RuntimeError('Destionation file for colour map {} already '
                           'exists: {}'.format(cmapName, destfile))
        
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


# Load a bunch of matplotlib colour maps
for cmapName in _builtins:
    _cmaps[cmapName] = _ColourMap(cmapName, None, True)

    
# Load all custom colour maps from the colourmaps/*.cmap files.
for cmapFile in glob.glob(op.join(op.dirname(__file__),
                                  'colourmaps',
                                  '*.cmap')):

    try:
        name = op.basename(cmapFile).split('.')[0]        
        registerColourMap(cmapFile, name)
        _cmaps[name].installed = True
        
    except:
        log.warn('Error processing custom colour '
                 'map file: {}'.format(cmapFile))
