#!/usr/bin/env python
#
# volumeopts.py - Defines the VolumeOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines the :class:`VolumeOpts` class, which contains
display options for rendering :class:`~fsl.fslview.gl.glvolume.GLVolume`
instances.
"""

import logging

import numpy as np

import props

import fsl.data.strings       as strings
import fsl.fslview.colourmaps as fslcm

import display as fsldisplay


log = logging.getLogger(__name__)


# TODO Define a super/mixin class which
# has a displayRange and colour map. This
# will allow other bits of code which
# need display range/cmap options to
# test for their presence without having
# to explicitly test against the VolumeOpts
# class (and other future *Opts classes
# which have a display range/cmap).


class VolumeOpts(fsldisplay.DisplayOpts):
    """A class which describes how an :class:`~fsl.data.image.Image` should
    be displayed.

    This class doesn't have much functionality - it is up to things which
    actually display an :class:`~fsl.data.image.Image` to adhere to the
    properties stored in the associated :class:`ImageDisplay` object.
    """

    
    displayRange = props.Bounds(
        ndims=1,
        labels=[strings.choices['VolumeOpts.displayRange.min'],
                strings.choices['VolumeOpts.displayRange.max']])
    """Image values which map to the minimum and maximum colour map colours."""

    
    clipLow  = props.Boolean(default=True)
    """If ``True``, don't display voxel values which are lower than
    the :attr:`displayRange`.
    """

    
    clipHigh = props.Boolean(default=False)
    """If ``True``, don't display voxel values which are higher than
    the :attr:`displayRange`.
    """ 

    
    cmap = props.ColourMap(default=fslcm.getDefault(),
                           cmapNames=fslcm.getColourMaps())
    """The colour map, a :class:`matplotlib.colors.Colourmap` instance."""

    
    _tooltips = {
        'name'          : 'The name of this image',
        'enabled'       : 'Enable/disable this image',
        'alpha'         : 'Opacity, between 0.0 (transparent) '
                          'and 100.0 (opaque)',
        'displayRange'  : 'Minimum/maximum display values',
        'clipLow'       : 'Do not show image values which are '
                          'lower than the display range',
        'clipHigh'      : 'Do not show image values which are '
                          'higher than the display range', 
        'interpolation' : 'Interpolate between voxel values at '
                          'each displayed real world location',
        'resolution'    : 'Data resolution in voxels',
        'volume'        : 'Volume number (for 4D images)',
        'transform'     : 'The transformation matrix which specifies the '
                          'conversion from voxel coordinates to a real '
                          'world location',
        'imageType'     : 'the type of data contained in the image',
        'cmap'          : 'Colour map'}

    
    _propHelp = _tooltips


    def __init__(self, image, display, imageList, displayCtx, parent=None):
        """Create an :class:`ImageDisplay` for the specified image.

        See the :class:`~fsl.fslview.displaycontext.display.DisplayOpts`
        documentation for more details. 
        """

        # Attributes controlling image display. Only
        # determine the real min/max for small images -
        # if it's memory mapped, we have no idea how big
        # it may be! So we calculate the min/max of a
        # sample (either a slice or an image, depending
        # on whether the image is 3D or 4D)
        if np.prod(image.shape) > 2 ** 30:
            sample = image.data[..., image.shape[-1] / 2]
            self.dataMin = float(sample.min())
            self.dataMax = float(sample.max())
        else:
            self.dataMin = float(image.data.min())
            self.dataMax = float(image.data.max())

        dRangeLen    = abs(self.dataMax - self.dataMin)
        dMinDistance = dRangeLen / 10000.0

        self.displayRange.setMin(0, self.dataMin - 0.5 * dRangeLen)
        self.displayRange.setMax(0, self.dataMax + 0.5 * dRangeLen)
        self.displayRange.setRange(0, self.dataMin, self.dataMax)
        self.setConstraint('displayRange', 'minDistance', dMinDistance)

        fsldisplay.DisplayOpts.__init__(self,
                                        image,
                                        display,
                                        imageList,
                                        displayCtx,
                                        parent) 
