#!/usr/bin/env python
#
# glimage_funcs.py - Functions used by the fsl.fslview.gl.glimage.GLImage class
#                    to render 3D images in an OpenGL 1.4 compatible manner.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Provides functions which are used by the
:class:`~fsl.fslview.gl.glimage.GLImage` class to render 3D images in an
OpenGL 1.4 compatible manner. (i.e. using immediate mode rendering).

The functions in this module make use of functions in the
:mod:`fsl.fslview.gl.glimage` module to actually generate the vertex and
texture information necessary to render an image.

This module provides the following functions:

 - :func:`init`: Does nothing - no initialisation is necessary for OpenGL 1.4.

 - :func:`genVertexData`: Generates and returns vertex and texture coordinates
   for rendering a single 2D slice of a 3D image.

 - :func:`genImageData`: Prepares and returns the 3D image data to be
   rendered.

 - :func:`genColourMap`: Configures a `matplotlib.colors.Colormap` instance
   for generating voxel colours from image data.

 - :func:`draw`: Draws the image using OpenGL.

 - :func:`destroy`: Deletes the texture handle for the colour map texture.
"""

import logging
log = logging.getLogger(__name__)

import numpy               as np
import scipy.ndimage       as ndi
import OpenGL.GL           as gl

import fsl.utils.transform as transform


def init(glimg, xax, yax):
    """No initialisation is necessary for OpenGL 1.4."""
    pass

    
def destroy(glimg):
    """Deletes the colour map texture handle."""
    gl.glDeleteTextures(1, glimg.colourTexture)

    
def genVertexData(glimg):
    """Generates vertex and texture coordinates required to render
    the image. See :func:`fsl.fslview.gl.glimage.genVertexData`.
    """
    
    worldCoords, texCoords, indices = glimg.genVertexData()

    return worldCoords, texCoords, indices, indices.shape[0]

        
def genImageData(glimg):
    """Retrieves the image data which is to be rendered."""

    image   = glimg.image
    display = glimg.display
    volume  = display.volume

    if len(image.shape) > 3: imageData = image.data[:, :, :, volume]
    else:                    imageData = image.data

    return imageData

        
def genColourMap(glimg, display, colourResolution):
    """Generates a colour map which is used to generate colours
    for each rendered voxel.
    """

    dmin = display.displayRange[0]
    dmax = display.displayRange[1]
    cmap = display.cmap
    
    def applyCmap(data):
        
        rgba = cmap((data - dmin) / (dmax - dmin), alpha=display.alpha)
        
        if display.clipLow:  rgba[data < dmin, 3] = 0.0
        if display.clipHigh: rgba[data > dmax, 3] = 0.0
        return np.array(rgba, dtype=np.float32)

    return applyCmap


def draw(glimg, zpos, xform=None):
    """Draws a slice of the image at the given Z location using immediate
    mode rendering.
    """

    display = glimg.display
    
    # Don't draw the slice if this
    # image display is disabled
    if not display.enabled: return

    worldCoords = glimg.worldCoords
    texCoords   = glimg.texCoords
    indices     = glimg.indices
    
    worldCoords[:, glimg.zax] = zpos
    texCoords[  :, glimg.zax] = zpos
    
    # Transform world texture coordinates to (floating
    # point) voxel coordinates.  The texCoords coordinates
    # are at the centre of every rendered voxel. If
    # interpolation is disabled, we use said texture
    # coordinates to determine the colour of each voxel.
    # But if interpolation is enabled, we'll use the
    # vertex coordinates, which are located at voxel
    # corners, so the rendered voxel colour is smoothed
    # throughout the voxel.
    if display.interpolation == 'none':
        voxCoords = transform.transform(texCoords,   display.displayToVoxMat) 
    else:
        voxCoords = transform.transform(worldCoords, display.displayToVoxMat)
        
    imageData = glimg.imageData
    colourMap = glimg.colourMap

    if   display.interpolation == 'spline': order = 3
    elif display.interpolation == 'linear': order = 1
    else:                                   order = 0

    # Be lenient on voxel coordinate boundaries -
    # any voxcoords which are within 0.5 of the min/max
    # voxel boundaries are clamped to said boundaries
    for ax in range(3):
        voxCoords[(voxCoords[:, ax] >= -0.5) & (voxCoords[:, ax] < 0), ax] = 0
        voxCoords[(voxCoords[:, ax] >  imageData.shape[ax] - 1) &
                  (voxCoords[:, ax] <= imageData.shape[ax] - 0.5),
                  ax] = imageData.shape[ax] - 1 

    # Remove vertices which are out of bounds. Not necessary
    # if we're displaying in ID or pixdim space.
    # 
    # TODO We could also peek in the transform matrix values
    # to see if any shearing/rotation has been applied - if
    # not, this bounds check is also unnecessary in world
    # ('affine') space.
    outOfBounds = []
    if display.transform == 'affine':
        outOfBounds = [None] * 3
        for ax in range(3):

            # Mark coordinates which are
            # outside of the image space
            outOfBounds[ax] = ((voxCoords[:, ax] < 0) |
                               (voxCoords[:, ax] >= imageData.shape[ax]))

        outOfBounds = (outOfBounds[0]) | (outOfBounds[1]) | (outOfBounds[2])

    # Interpolate image data at floating
    # point voxel coordinates
    #
    # TODO This is *the* rendering bottleneck.
    # If this can be made faster in any way,
    # do it.
    imageData = ndi.map_coordinates(imageData,
                                    voxCoords.T,
                                    order=order,
                                    prefilter=False)

    # Prepare world coordinates
    # and vertex colours
    colours = colourMap(imageData)
    colours[outOfBounds, 3] = 0.0

    worldCoords = worldCoords.ravel('C')
    colours     = colours    .ravel('C')

    if xform is not None: 
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glMultMatrixf(xform)

    # Select the shade model based on
    # whether interpolation is enabled/disabled
    if display.interpolation == 'none': gl.glShadeModel(gl.GL_FLAT)
    else:                               gl.glShadeModel(gl.GL_SMOOTH)
        

    gl.glEnableClientState(gl.GL_COLOR_ARRAY)
    gl.glEnableClientState(gl.GL_VERTEX_ARRAY)

    gl.glVertexPointer(3, gl.GL_FLOAT, 0, worldCoords)
    gl.glColorPointer( 4, gl.GL_FLOAT, 0, colours)

    gl.glDrawElements(gl.GL_TRIANGLE_STRIP,
                      len(indices),
                      gl.GL_UNSIGNED_INT,
                      indices)

    gl.glDisableClientState(gl.GL_COLOR_ARRAY)
    gl.glDisableClientState(gl.GL_VERTEX_ARRAY)

    if xform is not None:
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPopMatrix()
