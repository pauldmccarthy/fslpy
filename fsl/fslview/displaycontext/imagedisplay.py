#!/usr/bin/env python
#
# imagedisplay.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import numpy as np

import props

import fsl.data.strings           as strings
import fsl.utils.transform        as transform
import fsl.fslview.colourmaps     as fslcm
import fsl.fslview.displaycontext as displayctx


class ImageDisplay(displayctx.Display):
    """A class which describes how an :class:`~fsl.data.image.Image` should
    be displayed.

    This class doesn't have much functionality - it is up to things which
    actually display an :class:`~fsl.data.image.Image` to adhere to the
    properties stored in the associated :class:`ImageDisplay` object.
    """

    
    displayRange = props.Bounds(
        ndims=1,
        editLimits=True,
        labels=[strings.choices['ImageDisplay.displayRange.min'],
                strings.choices['ImageDisplay.displayRange.max']])
    """Image values which map to the minimum and maximum colour map colours."""

    
    clipLow  = props.Boolean(default=False)
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

        
    def is4DImage(self):
        """Returns ``True`` if this image is 4D, ``False`` otherwise.
        """
        return self.image.is4DImage()

    
    _tooltips = {
        'name'          : 'The name of this image',
        'enabled'       : 'Enable/disable this image',
        'alpha'         : 'Opacity, between 0.0 (transparent) '
                          'and 1.0 (opaque)',
        'displayRange'  : 'Minimum/maximum display values',
        'clipLow'       : 'Do not show image values which are '
                          'lower than the display range',
        'clipHigh'      : 'Do not show image values which are '
                          'higher than the display range', 
        'interpolation' : 'Interpolate between voxel values at '
                          'each displayed real world location',
        'resolution'    : 'Data resolution in voxels',
        'volume'        : 'Volume number (for 4D images)',
        'syncVolume'    : 'Synchronise to global volume number',
        'transform'     : 'The transformation matrix which specifies the '
                          'conversion from voxel coordinates to a real '
                          'world location',
        'imageType'     : 'the type of data contained in the image',
        'cmap'          : 'Colour map'}

    
    _propHelp = _tooltips


    _cliProps = ['alpha',
                 'displayRange',
                 'clipLow',
                 'clipHigh',
                 'resolution',
                 'transform',
                 'interpolation',
                 'imageType',
                 'cmap',
                 'name',
                 'volume']

    _shortArgs = {
        'alpha'         : 'alpha',
        'displayRange'  : 'dr',
        'clipLow'       : 'cl',
        'clipHigh'      : 'ch',
        'interpolation' : 'interp',
        'resolution'    : 'vr',
        'transform'     : 'trans',
        'imageType'     : 'it',
        'cmap'          : 'cmap',
        'name'          : 'name',
        'volume'        : 'vol'}


    def __init__(self, image, parent=None):
        """Create an :class:`ImageDisplay` for the specified image.

        :arg image: A :class:`~fsl.data.image.Image` object.

        :arg parent: 
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

        self.resolution = min(image.pixdim[:3])
        self.setConstraint('resolution',   'minval', self.resolution)

        displayctx.Display.__init__(self, image, parent)

        
    def getDisplayBounds(self):
        """Calculates and returns the min/max values of a 3D bounding box,
        in the display coordinate system, which is big enough to contain
        the image associated with this :class:`ImageDisplay` instance.

        The coordinate system in which the bounding box is defined is
        determined by the current value of the :attr:`transform` property.

        A tuple containing two values is returned, with the first value
        a sequence of three low bounds, and the second value a sequence
        of three high bounds.
        """
        return transform.axisBounds(self.image.shape[:3], self.voxToDisplayMat)
    
        
    def _transformChanged(self, *a):
        """Called when the :attr:`transform` property is changed.

        Generates transformation matrices for transforming between voxel and
        display coordinate space.

        If :attr:`transform` is set to ``affine``, the :attr:`interpolation`
        property is changed to ``spline. Otherwise, it is set to ``none``.
        """

        # Store references to the previous display related
        # transformation matrices (see comments in __init__)
        self._oldVoxToDisplayMat   = self.voxToDisplayMat
        self._oldDisplayToVoxMat   = self.displayToVoxMat
        self._oldWorldToDisplayMat = self.worldToDisplayMat
        self._oldDisplayToWorldMat = self.displayToWorldMat

        # The transform property defines the way
        # in which image voxel coordinates map
        # to the display coordinate system
        if self.transform == 'id':
            pixdim          = [1.0, 1.0, 1.0]
            voxToDisplayMat = np.eye(4)
            
        elif self.transform == 'pixdim':
            pixdim          = self.image.pixdim
            voxToDisplayMat = np.diag([pixdim[0], pixdim[1], pixdim[2], 1.0])
            
        elif self.transform == 'affine':
            voxToDisplayMat = self.voxToWorldMat

        # for pixdim/identity transformations, we want the world
        # location (0, 0, 0) to map to voxel location (0, 0, 0)
        if self.transform in ('id', 'pixdim'):
            for i in range(3):
                voxToDisplayMat[3, i] =  pixdim[i] * 0.5

        # Transformation matrices for moving between the voxel
        # coordinate system and the display coordinate system
        self.voxToDisplayMat = np.array(voxToDisplayMat, dtype=np.float32)
        self.displayToVoxMat = transform.invert(self.voxToDisplayMat)

        # Matrices for moving between the display coordinate
        # system, and the image world coordinate system
        self.displayToWorldMat = transform.concat(self.displayToVoxMat,
                                                  self.voxToWorldMat)
        self.worldToDisplayMat = transform.invert(self.displayToWorldMat)

        # When transform is changed to 'affine', enable interpolation
        # and, when changed to 'pixdim' or 'id', disable interpolation
        if self.transform == 'affine': self.interpolation = 'spline'
        else:                          self.interpolation = 'none'
