#!/usr/bin/env python
#
# slicecanvas_draw.py - Render slices from a collection of images in an OpenGL
#                       1.4 compatible manner.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Render slices from a collection of images in an OpenGL 1.4 compatible
 manner, using immediate mode rendering. 

.. note:: This module is extremely tightly coupled to the
:class:`~fsl.fslview.gl.slicecanvas.SliceCanvas` class, to the
:class:`~fsl.fslview.gl.glimage.GLImage` class, and to the
:mod:`~fsl.fslview.gl.glimage.gl14.glimage_funcs` module.

This module provides two functions:

  - :func:`drawScene` draws slices from all of the images in an
    :class:`~fsl.data.image.ImageList` to a
    :class:`~fsl.fslview.gl.slicecanvas.SliceCanvas` display.

  - :func:`drawSlice` (used by :func:`drawScene`) draws slices from one image
    to the :class:`~fsl.fslview.gl.slicecanvas.SliceCanvas`.
"""

import logging
log = logging.getLogger(__name__)

import scipy.ndimage as ndi
import OpenGL.GL     as gl

def drawSlice(canvas, image, zpos, xform=None):
    """Draws the specified slice from the specified image onto the specified
    canvas.

    :arg image:   The :class:`~fsl.data.image.Image` object to draw.
    
    :arg zpos:    World Z position of slice to be drawn.
    
    :arg xform:   A 4*4 transformation matrix to be applied to the slice
                  data (or ``None`` to use the
                  :class:`~fsl.data.image.Image` ``voxToWorldMat``
                  matrix).
    """

    # The GL data is stored as an attribute of the image,
    # and is created in the SliceCanvas._imageListChanged
    # method when images are added to the image. If there's
    # no data here, ignore it; hopefully by the time the
    # image is to be drawn again, it will have been created.
    try:    glimg = image.getAttribute(canvas.name)
    except: return
    
    display = image.getAttribute('display')
    
    # Don't draw the slice if this
    # image display is disabled
    if not display.enabled: return

    worldCoords = glimg.worldCoords
    texCoords   = glimg.texCoords
    
    worldCoords[:, canvas.zax] = zpos
    texCoords[  :, canvas.zax] = zpos
    
    # Transform world texture coordinates
    # to (floating point) voxel coordinates
    voxCoords     = image.worldToVox(texCoords)
    imageData     = glimg.imageData
    texCoordXform = glimg.texCoordXform
    colourTexture = glimg.colourTexture
    nVertices     = glimg.nVertices

    if display.interpolation: order = 1
    else:                     order = 0

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

    gl.glDrawArrays(gl.GL_QUADS, 0, nVertices)

    gl.glDisableClientState(gl.GL_TEXTURE_COORD_ARRAY)
    gl.glDisableClientState(gl.GL_VERTEX_ARRAY)

    if xform is not None:
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPopMatrix()

    gl.glMatrixMode(gl.GL_TEXTURE)
    gl.glPopMatrix()
    
    
def drawScene(canvas):
    """Draws the currently selected slice (as specified by the ``z``
    value of the :attr:`pos` property) to the canvas."""

    canvas.glContext.SetCurrent(canvas)

    canvas._setViewport()

    # clear the canvas
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    # enable transparency
    gl.glEnable(gl.GL_BLEND)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

    # disable interpolation
    gl.glShadeModel(gl.GL_FLAT)

    gl.glEnable(gl.GL_TEXTURE_1D)

    for image in canvas.imageList:

        log.debug('Drawing {} slice for image {}'.format(
            canvas.zax, image.name))

        drawSlice(canvas, image, canvas.pos.z)

    gl.glDisable(gl.GL_TEXTURE_1D)
