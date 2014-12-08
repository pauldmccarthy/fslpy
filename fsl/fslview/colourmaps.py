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
matplotlib colour maps are also made available.

This module provides two attributes:

  - :data:`default`:   The name of the colour map to be used for new images.

  - :data:`cmapNames`: A list of all colour maps which should be used for
                       rendering images.

And one function:

 - :func:`registerColourMap`: Given a text file containing RGB values,
                              loads the data and registers it  with
                              :mod:`matplotlib`.
"""

import os.path as op
import glob
import copy

import numpy             as np
import matplotlib.colors as colors
import matplotlib.cm     as mplcm

import logging
log = logging.getLogger(__name__)


_default   =  'Greys_r'
_cmapNames = ['Greys_r',
              'Greys',
              'Reds',
              'Reds_r',
              'Blues',
              'Blues_r',
              'Greens',
              'Greens_r',
              'pink',
              'pink_r',
              'hot',
              'hot_r',
              'cool',
              'cool_r', 
              'autumn',
              'autumn_r',
              'copper',
              'copper_r']

def getDefault():
    return _default

def getColourMaps():
    return  copy.copy(_cmapNames)


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
    _cmapNames.append(name)


# Load all custom colour maps from the colourmaps/*.cmap files.
for cmapFile in glob.glob(op.join(op.dirname(__file__),
                                  'colourmaps',
                                  '*.cmap')):

    try:
        registerColourMap(cmapFile)
        
    except:
        log.warn('Error processing custom colour '
                 'map file: {}'.format(cmapFile))
