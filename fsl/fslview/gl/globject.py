#!/usr/bin/env python
#
# globject.py - Mapping between fsl.data.image types and
# OpenGL representations.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""
GL Objects must have the following methods:
  - __init__(self, image, display)
  - init(   self, xax, yax)
  - ready(self)
  - setAxes(self, xax, yax)
  - destroy(self)
  - draw(self, zpos, xform=None)
"""

import logging
log = logging.getLogger(__name__)

import numpy                       as np

import fsl.fslview.gl.glimage      as glimage
import fsl.fslview.gl.glcircle     as glcircle
import fsl.fslview.gl.gltensorline as gltensorline


_objectmap = {
    'volume' : glimage     .GLImage,
    'circle' : glcircle    .GLCircle,
    'tensor' : gltensorline.GLTensorLine
}

def createGLObject(image, display):

    ctr = _objectmap.get(display.imageType, None)

    if ctr is not None: return ctr(image, display)
    else:               return None


def calculateSamplePoints(image, display, xax, yax):
    """Calculates a uniform grid of points, in real world space along the x-y
    plane (as specified by the xax/yax indices), at which the given image
    should be sampled for display purposes.

    This function returns a tuple containing:

     - a numpy array of shape `(N, 3)`, containing the coordinates of the centre
       of every sampling point in real worl space.

     - the horizontal distance (along xax) between adjacent points

     - the vertical distance (along yax) between adjacent points

    :arg image:   The :class:`~fsl.data.image.Image` object to
                  generate vertex and texture coordinates for.

    :arg display: A :class:`~fsl.fslview.displaycontext.ImageDisplay`
                  object which defines how the image is to be
                  rendered.

    :arg xax:     The world space axis which corresponds to the
                  horizontal screen axis (0, 1, or 2).

    :arg yax:     The world space axis which corresponds to the
                  vertical screen axis (0, 1, or 2).

    """

    worldRes   = display.worldResolution
    voxelRes   = display.voxelResolution
    transform  = display.transform

    # These values give the min/max x/y values
    # of a bounding box which encapsulates
    # the entire image
    xmin, xmax = image.imageBounds(xax)
    ymin, ymax = image.imageBounds(yax)

    # The width/height of a displayed voxel.
    # If we are displaying in real world space,
    # we use the world display resolution
    if transform in ('affine'):

        xpixdim = worldRes
        ypixdim = worldRes

    # But if we're just displaying the data (the
    # transform is 'id' or 'pixdim'), we display
    # it in the resolution of said data.
    else:
        xpixdim = image.pixdim[xax] * voxelRes
        ypixdim = image.pixdim[yax] * voxelRes

    # Number of samples across each dimension,
    # given the current sample rate
    xNumSamples = np.floor((xmax - xmin) / xpixdim)
    yNumSamples = np.floor((ymax - ymin) / ypixdim)

    # the adjusted width/height of our sample points
    xpixdim = (xmax - xmin) / xNumSamples
    ypixdim = (ymax - ymin) / yNumSamples

    log.debug('Generating coordinate buffers for {} '
              '({} resolution {}/{}, num samples {})'.format(
                  image.name, transform, worldRes, voxelRes,
                  xNumSamples * yNumSamples))

    # The location of every displayed
    # point in real world space
    worldX = np.linspace(xmin + 0.5 * xpixdim,
                         xmax - 0.5 * xpixdim,
                         xNumSamples)
    worldY = np.linspace(ymin + 0.5 * ypixdim,
                         ymax - 0.5 * ypixdim,
                         yNumSamples)

    worldX, worldY = np.meshgrid(worldX, worldY)
    
    coords = np.zeros((worldX.size, 3))
    coords[:, xax] = worldX.flatten()
    coords[:, yax] = worldY.flatten()

    return coords, xpixdim, ypixdim
