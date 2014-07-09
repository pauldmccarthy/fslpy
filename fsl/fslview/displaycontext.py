#!/usr/bin/env python
#
# displaycontext.py - Classes which define how images should be displayed.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import numpy         as np
import matplotlib.cm as mplcm

import props
import fsl.data.image as fslimage


class ImageDisplay(props.HasProperties):
    """A class which describes how an :class:`~fsl.data.image.Image`  should
    be displayed.

    This class doesn't have any functionality - it is up to things which
    actually display an :class:`~fsl.data.image.Image` to adhere to the
    properties stored in the associated :class:`ImageDisplay` object.
    """

    
    enabled = props.Boolean(default=True)
    """Should this image be displayed at all?"""

    
    alpha = props.Real(minval=0.0, maxval=1.0, default=1.0)
    """Transparency - 1.0 is fully opaque, and 0.0 is fully transparent."""

    
    displayRange = props.Bounds(ndims=1, editLimits=True,
                                labels=['Min.', 'Max.'])
    """Image values which map to the minimum and maximum colour map colours."""

    
    samplingRate = props.Int(minval=1, maxval=16, default=1, clamped=True)
    """Only display every Nth voxel (a performance tweak)."""

    
    rangeClip = props.Boolean(default=False)
    """If ``True``, don't display voxel values which are beyond the
    :attr:`displayRange`.
    """

    
    cmap = props.ColourMap(default=mplcm.Greys_r)
    """The colour map, a :class:`matplotlib.colors.Colourmap` instance."""

    
    volume = props.Int(minval=0, maxval=0, default=0, clamped=True)
    """If a 4D image, the current volume to display."""


    transform = fslimage.Image.transform
    """How the image is transformed from voxel to real world coordinates.
    This property is bound to the :attr:`~fsl.data.image.Image.transform`
    property of the image associated with this :class:`ImageDisplay`.
    """

    
    name = fslimage.Image.name
    """The image name.  This property is bound to the
    :attr:`~fsl.data.image.Image.name` property.
    """

    
    def is4DImage(self):
        """Returns ``True`` if this image is 4D, ``False`` otherwise.
        """
        return self.image.is4DImage()

        
    _view = props.VGroup(('name',
                          'enabled',
                          'displayRange',
                          'alpha',
                          'rangeClip',
                          'samplingRate',
                          'transform',
                          'cmap'))
    _labels = {
        'name'         : 'Image name',
        'enabled'      : 'Enabled',
        'displayRange' : 'Display range',
        'alpha'        : 'Opacity',
        'rangeClip'    : 'Clipping',
        'samplingRate' : 'Sampling rate',
        'transform'    : 'Image transform',
        'cmap'         : 'Colour map'}

    _tooltips = {
        'name'         : 'The name of this image',
        'enabled'      : 'Enable/disable this image',
        'alpha'        : 'Opacity, between 0.0 (transparent) and 1.0 (opaque)',
        'displayRange' : 'Minimum/maximum display values',
        'rangeClip'    : 'Do not show areas of the image which lie '
                         'outside of the display range',
        'samplingRate' : 'Draw every Nth voxel',
        'transform'    : 'The transformation matrix which specifies the '
                         'conversion from voxel coordinates to a real world '
                         'location',
        'cmap'         : 'Colour map'}

    _propHelp = _tooltips


    def __init__(self, image):
        """Create an :class:`ImageDisplay` for the specified image.

        :arg image: A :class:`~fsl.data.image.Image` object.
        """

        self.image = image

        # bind self.transform and self.name to 
        # image.transform/image.name, so changes
        # in one are propagated to the other
        self.bindProps('transform', image)
        self.bindProps('name',      image)

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

        dRangeLen = abs(self.dataMax - self.dataMin)

        self.displayRange.setMin(0, self.dataMin - 0.5 * dRangeLen)
        self.displayRange.setMax(0, self.dataMax + 0.5 * dRangeLen)
        self.displayRange.setRange(0, self.dataMin, self.dataMax)

        # is this a 4D volume?
        if image.is4DImage():
            self.setConstraint('volume', 'maxval', image.shape[3] - 1)


class DisplayContext(props.HasProperties):

    pass
