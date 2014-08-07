#!/usr/bin/env python
#
# glimage.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import numpy as np

def genVertexData(image, display, xax, yax):
    """
    (Re-)Generates data buffers containing X, Y, and Z coordinates,
    used for indexing into the image. Also generates the geometry
    buffer, which defines the geometry of a single voxel. If a
    sampling rate other than 1 is passed in, the generated index
    buffers will contain a sampling of the full coordinate space
    for the X and Y dimensions, and the vertices in the geometry
    buffer will be scaled accordingly.
    """

    zax        = 3 - xax - yax
    worldRes   = display.worldResolution
    voxelRes   = display.voxelResolution
    transform  = display.transform
    xdim       = image.shape[xax]
    ydim       = image.shape[yax]

    # These values give the min/max x/y values
    # of a bounding box which encapsulates
    # the entire image
    xmin, xmax = image.imageBounds(xax)
    ymin, ymax = image.imageBounds(yax)

    # These values give the length
    # of the image along the x/y axes
    xlen = image.axisLength(xax)
    ylen = image.axisLength(yax)

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

    # the adjusted width/height of our sampled voxels
    xpixdim = (xmax - xmin) / xNumSamples
    ypixdim = (ymax - ymin) / yNumSamples

    log.debug('Generating coordinate buffers for {} '
              '({} resolution {}/{}, num samples {})'.format(
                  image.name, transform, worldRes, voxelRes,
                  xNumSamples * yNumSamples))

    # The location of every displayed
    # voxel in real world space
    worldX = np.linspace(xmin + 0.5 * xpixdim,
                         xmax - 0.5 * xpixdim,
                         xNumSamples)
    worldY = np.linspace(ymin + 0.5 * ypixdim,
                         ymax - 0.5 * ypixdim,
                         yNumSamples)

    worldX, worldY = np.meshgrid(worldX, worldY)

    worldX  = worldX.flatten()
    worldY  = worldY.flatten()
    nVoxels = len(worldX)

    # The geometry of a single
    # voxel, rendered as a quad
    voxelGeom = np.array([[-0.5, -0.5],
                          [-0.5,  0.5],
                          [ 0.5,  0.5],
                          [ 0.5, -0.5]], dtype=np.float32)

    # And scaled appropriately
    voxelGeom[:, 0] *= xpixdim
    voxelGeom[:, 1] *= ypixdim

    worldX = worldX.repeat(4) 
    worldY = worldY.repeat(4)
    worldZ = np.zeros(len(worldX))

    worldCoords = [None] * 3
    texCoords   = [None] * 3

    # The texture coordinates are in the centre of each
    # set of 4 vertices, so allow us to look up the
    # colour for every vertex coordinate
    texCoords[xax] = worldX
    texCoords[yax] = worldY
    texCoords[zax] = worldZ

    # The world coordinates define a bunch of sets
    # of 4 vertices, each rendered as a quad
    worldX = worldX + np.tile(voxelGeom[:, 0], nVoxels)
    worldY = worldY + np.tile(voxelGeom[:, 1], nVoxels)
    
    worldCoords[xax] = worldX
    worldCoords[yax] = worldY
    worldCoords[zax] = worldZ

    worldCoords = np.array(worldCoords, dtype=np.float32).transpose()
    texCoords   = np.array(texCoords,   dtype=np.float32).transpose()

    return worldCoords, texCoords
