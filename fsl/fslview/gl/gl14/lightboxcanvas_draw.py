#!/usr/bin/env python
#
# lightboxcanvas_draw.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import OpenGL.GL as gl

import fsl.fslview.gl                          as fslgl
import fsl.fslview.gl.gl21.lightboxcanvas_draw as gl21_draw


def drawScene(canvas, ev=None):
    """Draws the currently visible slices to the canvas."""

    # No scrollbar -> draw all the slices 
    if canvas._scrollbar is None:
        startSlice = 0
        endSlice   = canvas._nslices

    # Scrollbar -> draw a selection of slices
    else:
        rowsOnScreen = canvas._scrollbar.GetPageSize()
        startRow     = canvas._scrollbar.GetThumbPosition()
        
        startSlice   = canvas.ncols * startRow
        endSlice     = startSlice + rowsOnScreen * canvas.ncols

        if endSlice > canvas._nslices:
            endSlice = canvas._nslices

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

    # Draw all the slices for all the images.
    for i, image in enumerate(canvas.imageList):
        
        log.debug('Drawing {} slices ({} - {}) for image {}'.format(
            endSlice - startSlice, startSlice, endSlice, i))
        
        for zi in range(startSlice, endSlice):
            fslgl.slicecanvas_draw.drawSlice(canvas,
                                             image,
                                             canvas._sliceIdxs[ i][zi],
                                             canvas._transforms[i][zi])
            
    gl.glDisable(gl.GL_TEXTURE_1D)

    if canvas.showCursor:
        gl21_draw.drawCursor(canvas)

    canvas.SwapBuffers()
