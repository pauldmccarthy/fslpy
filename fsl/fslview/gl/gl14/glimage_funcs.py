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

 - :func:`genColourTexture`: Configures an OpenGL 1D texture with a colour map,
   used for colouring the image data.

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

        
def genColourTexture(glimg):
    """Generates the colour texture used to colour image voxels. See
    :func:`fsl.fslview.gl.glimage.genVertexData`.
    """

    texCoordXform = glimg.genColourTexture()
    return texCoordXform 

    
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
    
    # Transform world texture coordinates
    # to (floating point) voxel coordinates
    voxCoords     = transform.transform(texCoords, display.displayToVoxMat) 
    imageData     = glimg.imageData
    texCoordXform = glimg.texCoordXform
    colourTexture = glimg.colourTexture

    if   display.interpolation == 'spline': order = 3
    elif display.interpolation == 'linear': order = 1
    else:                                   order = 0

    # Remove vertices which are out of bounds
    outOfBounds = [None] * 3
    for ax in range(3):

        # Be lenient on voxel coordinate boundaries
        voxCoords[(voxCoords[:, ax] >= -0.5) & (voxCoords[:, ax] < 0), ax] = 0
        voxCoords[(voxCoords[:, ax] >  imageData.shape[ax] - 1) &
                  (voxCoords[:, ax] <= imageData.shape[ax] - 0.5),
                  ax] = imageData.shape[ax] - 1

        # But remove anything which is clearly
        # outside of the image space
        outOfBounds[ax] = ((voxCoords[:, ax] < 0) |
                           (voxCoords[:, ax] >= imageData.shape[ax]))

    outOfBounds = (outOfBounds[0]) | (outOfBounds[1]) | (outOfBounds[2])
    if outOfBounds.any():
        voxCoords   = voxCoords[  ~outOfBounds, :]
        worldCoords = worldCoords[~outOfBounds, :]
        indices     = np.delete(indices, indices == np.where(outOfBounds)[0])

    # Interpolate image data at floating
    # point voxel coordinates
    imageData = ndi.map_coordinates(imageData,
                                    voxCoords.transpose(),
                                    order=order,
                                    prefilter=False)

    # Prepare world coordinates and image data
    # (which are used as texture coordinates
    # on the colour map) for copy to GPU
    worldCoords   = worldCoords  .ravel('C')
    imageData     = np.array(imageData, dtype=np.float32)    .ravel('C')
    texCoordXform = texCoordXform.ravel('C')

    if xform is not None: 
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glMultMatrixf(xform)

    gl.glShadeModel(gl.GL_FLAT)

    gl.glEnable(gl.GL_TEXTURE_1D) 
    gl.glBindTexture(gl.GL_TEXTURE_1D, colourTexture)
    gl.glTexEnvf(gl.GL_TEXTURE_ENV, gl.GL_TEXTURE_ENV_MODE, gl.GL_REPLACE)

    gl.glMatrixMode(gl.GL_TEXTURE)
    gl.glPushMatrix()
    gl.glMultMatrixf(texCoordXform)

    gl.glEnableClientState(gl.GL_TEXTURE_COORD_ARRAY)
    gl.glEnableClientState(gl.GL_VERTEX_ARRAY)

    gl.glVertexPointer(  3, gl.GL_FLOAT, 0, worldCoords)
    gl.glTexCoordPointer(1, gl.GL_FLOAT, 0, imageData)

    gl.glDrawElements(gl.GL_TRIANGLE_STRIP,
                      len(indices),
                      gl.GL_UNSIGNED_INT,
                      indices)

    gl.glDisableClientState(gl.GL_TEXTURE_COORD_ARRAY)
    gl.glDisableClientState(gl.GL_VERTEX_ARRAY)

    if xform is not None:
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPopMatrix()

    gl.glMatrixMode(gl.GL_TEXTURE)
    gl.glPopMatrix()

    gl.glBindTexture(gl.GL_TEXTURE_1D, 0)
    gl.glDisable(gl.GL_TEXTURE_1D)
