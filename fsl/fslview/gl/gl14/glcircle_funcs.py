#!/usr/bin/env python
#
# glcircle_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import scipy.ndimage       as ndi
import OpenGL.GL           as gl

import fsl.utils.transform as transform
    
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
    
    worldCoords[:, glimg.zax] = zpos
    texCoords[  :, glimg.zax] = zpos
    
    # Transform world texture coordinates
    # to (floating point) voxel coordinates
    voxCoords     = transform.transform(texCoords, display.displayToVoxMat)
    imageData     = glimg.imageData
    texCoordXform = glimg.texCoordXform
    colourTexture = glimg.colourTexture
    nVertices     = glimg.nVertices

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
        nVertices   = worldCoords.shape[0]

    # Interpolate image data at floating
    # point voxel coordinates
    imageData = ndi.map_coordinates(imageData,
                                    voxCoords.transpose(),
                                    order=order,
                                    prefilter=False)

    # Prepare world coordinates and image data
    # (which are used as texture coordinates
    # on the colour map) for copy to GPU
    worldCoords = worldCoords.ravel('C')
    imageData   = imageData  .ravel('C')
    
    gl.glEnable(gl.GL_TEXTURE_1D) 

    if xform is not None: 
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glMultMatrixf(xform)

    gl.glBindTexture(gl.GL_TEXTURE_1D, colourTexture)
    gl.glTexEnvf(gl.GL_TEXTURE_ENV, gl.GL_TEXTURE_ENV_MODE, gl.GL_REPLACE)

    gl.glMatrixMode(gl.GL_TEXTURE)
    gl.glPushMatrix()
    gl.glMultMatrixf(texCoordXform)

    gl.glEnableClientState(gl.GL_TEXTURE_COORD_ARRAY)
    gl.glEnableClientState(gl.GL_VERTEX_ARRAY)

    gl.glVertexPointer(  3, gl.GL_FLOAT, 0, worldCoords)
    gl.glTexCoordPointer(1, gl.GL_FLOAT, 0, imageData)

    gl.glDrawArrays(gl.GL_TRIANGLES,
                    0,
                    nVertices)

    gl.glDisableClientState(gl.GL_TEXTURE_COORD_ARRAY)
    gl.glDisableClientState(gl.GL_VERTEX_ARRAY)

    if xform is not None:
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPopMatrix()

    gl.glMatrixMode(gl.GL_TEXTURE)
    gl.glPopMatrix()

    gl.glDisable(gl.GL_TEXTURE_1D)
