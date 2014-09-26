#!/usr/bin/env python
#
# lightboxcanvas_draw.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import OpenGL.GL as gl

import fsl.fslview.gl.gl21.lightboxcanvas_draw as gl21_draw

def draw(canvas):
    """Draws the currently visible slices to the canvas."""

    startSlice   = canvas.ncols * canvas.topRow
    endSlice     = startSlice + canvas.nrows * canvas.ncols

    if endSlice > canvas._nslices:
        endSlice = canvas._nslices

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

        try: globj = image.getAttribute(canvas.name)
        except KeyError:
            continue

        if (globj is None) or (not globj.ready()):
            continue 
        
        log.debug('Drawing {} slices ({} - {}) for image {}'.format(
            endSlice - startSlice, startSlice, endSlice, i))
        
        for zi in range(startSlice, endSlice):
            globj.draw(canvas._sliceLocs[ i][zi],
                       canvas._transforms[i][zi])
            
    gl.glDisable(gl.GL_TEXTURE_1D)

    if canvas.showCursor:
        gl21_draw.drawCursor(canvas)
