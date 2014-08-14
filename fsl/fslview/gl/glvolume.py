#!/usr/bin/env python
#
# glvolume.py - OpenGL vertex/texture creation for 3D volume rendering.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import numpy as np

import OpenGL.GL as gl


def genVertexData(image, display, xax, yax):
    """Generates vertex coordinates (for rendering voxels) and
    texture coordinates (for colouring voxels) in world space.

    Generates X/Y vertex coordinates, in the world space of the
    given image, which define a set of pixels for displaying the
    image at an arbitrary position along the world Z dimension.
    Each pixel is defined by four vertices, which are rendered
    as an OpenGL quad primitive.

    For every set of four vertices, a single vertex is also
    created, located in the centre of the four quad vertices. This
    centre vertex is used to look up the appropriate image value,
    which is then used to colour the quad.

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

    zax        = 3 - xax - yax
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


def genColourTexture(image,
                     display,
                     texture,
                     colourResolution=256,
                     xform=None):
    """Generates a RGBA colour texture which is used to colour voxels.

    :arg image:            The :class:`~fsl.data.image.Image` object to
                           generate vertex and texture coordinates for.

    :arg display:          A
                           :class:`~fsl.fslview.displaycontext.ImageDisplay`
                           object which defines how the image is
                           to be rendered.

    :arg texture:          A handle to an already-created OpenGL
                           1-dimensional texture (i.e. the result
                           of a call to `gl.glGenTextures(1)`).

    :arg colourResolution: Size of the texture, total number of unique
                           colours in the colour map.

    :xform:                
    """

    imin = display.displayRange[0]
    imax = display.displayRange[1]

    # This transformation is used to transform voxel values
    # from their native range to the range [0.0, 1.0], which
    # is required for texture colour lookup. Values below
    # or above the current display range will be mapped
    # to texture coordinate values less than 0.0 or greater
    # than 1.0 respectively.
    texCoordXform = np.identity(4, dtype=np.float32)
    texCoordXform[0, 0] = 1.0 / (imax - imin)
    texCoordXform[0, 3] = -imin * texCoordXform[0, 0]
    texCoordXform = texCoordXform.transpose()

    if xform is not None:
        texCoordXform = np.dot(xform, texCoordXform)

    log.debug('Generating colour buffer for '
              'image {} (map: {}; resolution: {})'.format(
                  image.name,
                  display.cmap.name,
                  colourResolution))

    # Create [self.colourResolution] rgb values,
    # spanning the entire range of the image
    # colour map
    colourRange     = np.linspace(0.0, 1.0, colourResolution)
    colourmap       = display.cmap(colourRange)
    colourmap[:, 3] = display.alpha

    # Make out-of-range values transparent
    # if clipping is enabled 
    if display.clipLow:  colourmap[ 0, 3] = 0.0
    if display.clipHigh: colourmap[-1, 3] = 0.0 

    # The colour data is stored on
    # the GPU as 8 bit rgba tuples
    colourmap = np.floor(colourmap * 255)
    colourmap = np.array(colourmap, dtype=np.uint8)
    colourmap = colourmap.ravel(order='C')

    # GL texture creation stuff
    gl.glBindTexture(gl.GL_TEXTURE_1D, texture)
    gl.glTexParameteri(gl.GL_TEXTURE_1D,
                       gl.GL_TEXTURE_MAG_FILTER,
                       gl.GL_NEAREST)
    gl.glTexParameteri(gl.GL_TEXTURE_1D,
                       gl.GL_TEXTURE_MIN_FILTER,
                       gl.GL_NEAREST)

    gl.glTexParameteri(gl.GL_TEXTURE_1D,
                       gl.GL_TEXTURE_WRAP_S,
                       gl.GL_CLAMP_TO_EDGE)

    gl.glTexImage1D(gl.GL_TEXTURE_1D,
                    0,
                    gl.GL_RGBA8,
                    colourResolution,
                    0,
                    gl.GL_RGBA,
                    gl.GL_UNSIGNED_BYTE,
                    colourmap)

    return texCoordXform
