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

import itertools           as it
import numpy               as np
import fsl.utils.transform as transform


def createGLObject(image, display):

    import fsl.fslview.gl.glimage      as glimage
    import fsl.fslview.gl.glcircle     as glcircle
    import fsl.fslview.gl.gltensorline as gltensorline

    _objectmap = {
        'volume' : glimage     .GLImage,
        'circle' : glcircle    .GLCircle,
        'tensor' : gltensorline.GLTensorLine
    } 

    ctr = _objectmap.get(display.imageType, None)

    if ctr is not None: return ctr(image, display)
    else:               return None


def calculateSamplePoints(image, display, xax, yax):
    """Calculates a uniform grid of points, in real world space along the x-y
    plane (as specified by the xax/yax indices), at which the given image
    should be sampled for display purposes.

    This function returns a tuple containing:

     - a numpy array of shape `(N, 3)`, containing the coordinates of the
       centre of every sampling point in real world space.

     - the horizontal distance (along xax) between adjacent points

     - the vertical distance (along yax) between adjacent points

     - The number of samples along the horizontal axis (xax)

     - The number of samples along the vertical axis (yax)

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

    worldRes       = display.worldResolution
    voxelRes       = display.voxelResolution
    transformCode  = display.transform
    transformMat   = display.voxToDisplayMat

    # These values give the min/max x/y values
    # of a bounding box which encapsulates
    # the entire image
    xmin, xmax = transform.axisBounds(image.shape, transformMat, xax)
    ymin, ymax = transform.axisBounds(image.shape, transformMat, yax)

    # The width/height of a displayed voxel.
    # If we are displaying in real world space,
    # we use the world display resolution
    if transformCode == 'affine':

        xpixdim = worldRes
        ypixdim = worldRes

    # But if we're just displaying the data (the
    # transform is 'id' or 'pixdim'), we display
    # it in the resolution of said data.
    elif transformCode == 'pixdim':
        xpixdim = image.pixdim[xax] * voxelRes
        ypixdim = image.pixdim[yax] * voxelRes
        
    elif transformCode == 'id':
        xpixdim = 1.0 * voxelRes
        ypixdim = 1.0 * voxelRes

    # Number of samples across each dimension,
    # given the current sample rate
    xNumSamples = np.floor((xmax - xmin) / xpixdim)
    yNumSamples = np.floor((ymax - ymin) / ypixdim)

    # the adjusted width/height of our sample points
    xpixdim = (xmax - xmin) / xNumSamples
    ypixdim = (ymax - ymin) / yNumSamples

    log.debug('Generating coordinate buffers for {} '
              '({} resolution {}/{}, num samples {})'.format(
                  image.name, transformCode, worldRes, voxelRes,
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

    return coords, xpixdim, ypixdim, xNumSamples, yNumSamples


def samplePointsToTriangleStrip(coords,
                                xpixdim,
                                ypixdim,
                                xlen,
                                ylen,
                                xax,
                                yax):
    """Given a regular 2D grid of points at which an image is to be
    sampled, converts those points into an OpenGL vertextriangle
    strip.
    """

    coords = coords.reshape(ylen, xlen, 3)

    xlen = int(xlen)
    ylen = int(ylen)

    # Duplicate every row - each voxel
    # is defined by two vertices 
    coords = coords.repeat(2, 0)

    texCoords   = np.array(coords)
    worldCoords = np.array(coords)

    # Add an extra column at the end
    # of the world coordinates
    worldCoords = np.append(worldCoords, worldCoords[:, -1:, :], 1)
    worldCoords[:, -1, xax] += xpixdim

    # Add an extra column at the start
    # of the texture coordinates
    texCoords = np.append(texCoords[:, :1, :], texCoords, 1)

    # Move the x/y world coordinates to the
    # sampling point corners (the texture
    # coordinates remain in the voxel centres)
    worldCoords[   :, :, xax] -= 0.5 * xpixdim
    worldCoords[ ::2, :, yax] -= 0.5 * ypixdim
    worldCoords[1::2, :, yax] += 0.5 * ypixdim 

    vertsPerRow  = 2 * (xlen + 1) 
    dVertsPerRow = 2 * (xlen + 1) + 2
    nindices     = ylen * dVertsPerRow - 2

    indices = np.zeros(nindices, dtype=np.uint32)

    for yi, xi in it.product(range(ylen), range(xlen + 1)):
        
        ii = yi * dVertsPerRow + 2 * xi
        vi = yi *  vertsPerRow + xi
        
        indices[ii]     = vi
        indices[ii + 1] = vi + xlen + 1

        # add degenerate vertices at the end
        # every row (but not needed for last
        # row)
        if xi == xlen and yi < ylen - 1:
            indices[ii + 2] = vi + xlen + 1
            indices[ii + 3] = (yi + 1) * vertsPerRow

    worldCoords = worldCoords.reshape((xlen + 1) * (2 * ylen), 3)
    texCoords   = texCoords  .reshape((xlen + 1) * (2 * ylen), 3)

    return worldCoords, texCoords, indices
