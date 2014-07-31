#!/usr/bin/env python
#
# ligntboxcanavs_draw.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import OpenGL.GL as gl
import numpy     as np
import wx

import fsl.fslview.gl as fslgl


def drawCursor(canvas):
    """Draws a cursor at the current canvas position (the
    :attr:`~fsl.fslview.gl.SliceCanvas.pos` property).
    """
    
    sliceno = int(np.floor((canvas.pos.z - canvas.zrange.xlo) /
                           canvas.sliceSpacing))
    xlen    = canvas.imageList.bounds.getLen(canvas.xax)
    ylen    = canvas.imageList.bounds.getLen(canvas.yax)
    xmin    = canvas.imageList.bounds.getLo( canvas.xax)
    ymin    = canvas.imageList.bounds.getLo( canvas.yax)
    row     = canvas._nrows - int(np.floor(sliceno / canvas.ncols)) - 1
    col     = int(np.floor(sliceno % canvas.ncols)) 

    xpos, ypos = canvas.worldToCanvas(*canvas.pos.xyz)

    xverts = np.zeros((2, 3))
    yverts = np.zeros((2, 3)) 

    xverts[:, canvas.xax] = xpos
    xverts[0, canvas.yax] = ymin + (row)     * ylen
    xverts[1, canvas.yax] = ymin + (row + 1) * ylen
    xverts[:, canvas.zax] = canvas.pos.z + 1

    yverts[:, canvas.yax] = ypos
    yverts[0, canvas.xax] = xmin + (col)     * xlen
    yverts[1, canvas.xax] = xmin + (col + 1) * xlen
    yverts[:, canvas.zax] = canvas.pos.z + 1

    gl.glBegin(gl.GL_LINES)
    gl.glColor3f(0, 1, 0)
    gl.glVertex3f(*xverts[0])
    gl.glVertex3f(*xverts[1])
    gl.glVertex3f(*yverts[0])
    gl.glVertex3f(*yverts[1])
    gl.glEnd() 

    
def drawScene(canvas, ev=None):
    """Draws the currently visible slices to the canvas."""

    # shaders have not been initialised.
    if not hasattr(canvas, 'shaders'):
        wx.CallAfter(lambda : fslgl.slicecanvas_draw.initGL(canvas))
        return 

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

    # load the shaders
    gl.glUseProgram(canvas.shaders)

    # enable transparency
    gl.glEnable(gl.GL_BLEND)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

    # disable interpolation
    gl.glShadeModel(gl.GL_FLAT)

    # Draw all the slices for all the images.
    for i, image in enumerate(canvas.imageList):
        
        log.debug('Drawing {} slices ({} - {}) for image {}'.format(
            endSlice - startSlice, startSlice, endSlice, i))
        
        for zi in range(startSlice, endSlice):
            fslgl.slicecanvas_draw.drawSlice(canvas,
                                             image,
                                             canvas._sliceIdxs[ i][zi],
                                             canvas._transforms[i][zi])
            
    gl.glUseProgram(0) 

    if canvas.showCursor:
        drawCursor(canvas)

    canvas.SwapBuffers()
