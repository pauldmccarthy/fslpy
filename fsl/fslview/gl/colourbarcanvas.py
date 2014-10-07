#!/usr/bin/env python
#
# colourbarcanvas.py - Render a colour bar using OpenGL and matplotlib.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ColourBarCanvas`.

The :class:`ColourBarCanvas` contains logic which uses :mod:`matplotlib` to
draw a colour bar (with labels), and then renders said colour bar using
OpenGL.
"""

import logging
log = logging.getLogger(__name__)

import OpenGL.GL         as gl
import numpy             as np


import props

import fsl.fslview.gl                as fslgl
import fsl.utils.colourbarbitmap     as cbarbmp


class ColourBarCanvas(props.HasProperties):

    cmap        = props.ColourMap()
    vrange      = props.Bounds(ndims=1)
    label       = props.String()
    orientation = props.Choice({
        'horizontal' : 'Horizontal',
        'vertical'   : 'Vertical'})

    labelSide   = props.Choice({
        'top-left'     : 'Top / left',
        'bottom-right' : 'Bottom / right'})

    def __init__(self):

        self._glReady  = False
        self._tex      = None
        self._name     = '{}_{}'.format(self.__class__.__name__, id(self)) 

        def _update(*a):
            self._initGL()
            self._refresh()

        for prop in ('cmap', 'vrange', 'label', 'orientation', 'labelSide'):
            self.addListener(prop, self._name, _update)


    def _initGL(self):

        if not self._setGLContext():
            return

        w, h = self._getSize()

        if w == 0 or h == 0:
            if self.orientation == 'horizontal': w, h = 600, 200
            else:                                w, h = 200, 600

        if self.orientation == 'horizontal':
            if  self.labelSide == 'top-left': labelSide = 'top'
            else:                             labelSide = 'bottom'
        else:
            if  self.labelSide == 'top-left': labelSide = 'left'
            else:                             labelSide = 'right' 
        
        bitmap = cbarbmp.colourBarBitmap(
            self.cmap,
            self.vrange.xlo,
            self.vrange.xhi,
            w, h,
            self.label,
            self.orientation,
            labelSide)
        bitmap = np.flipud(bitmap)

        if self._tex is None:
            self._tex = gl.glGenTextures(1)

        gl.glBindTexture(  gl.GL_TEXTURE_2D, self._tex)
        gl.glTexParameteri(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_MAG_FILTER,
                           gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_MIN_FILTER,
                           gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_WRAP_S,
                           gl.GL_CLAMP_TO_BORDER)
        gl.glTexParameteri(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_WRAP_T,
                           gl.GL_CLAMP_TO_BORDER)

        gl.glTexImage2D(gl.GL_TEXTURE_2D,
                        0,
                        gl.GL_RGBA8,
                        w,
                        h,
                        0,
                        gl.GL_RGBA,
                        gl.GL_UNSIGNED_BYTE,
                        bitmap)
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)


    def draw(self, ev=None):
        
        self._setGLContext()
        width, height = self._getSize()

        # viewport
        gl.glViewport(0, 0, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(0, 1, 0, 1, -1, 1)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()

        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glShadeModel(gl.GL_FLAT)

        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)
        gl.glPixelStorei(gl.GL_PACK_ALIGNMENT,   1)

        gl.glActiveTexture(gl.GL_TEXTURE0) 
        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glTexEnvf(gl.GL_TEXTURE_ENV, gl.GL_TEXTURE_ENV_MODE, gl.GL_REPLACE) 
        gl.glBindTexture(gl.GL_TEXTURE_2D, self._tex)

        gl.glBegin(gl.GL_QUADS)
        gl.glTexCoord2f(0, 0)
        gl.glVertex3f(  0, 0, 0)
        gl.glTexCoord2f(0, 1)
        gl.glVertex3f(  0, 1, 0)
        gl.glTexCoord2f(1, 1)
        gl.glVertex3f(  1, 1, 0)
        gl.glTexCoord2f(1, 0)
        gl.glVertex3f(  1, 0, 0)
        gl.glEnd()

        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        gl.glDisable(gl.GL_TEXTURE_2D)

        self._postDraw()


import wx
import wx.glcanvas as wxgl
 
class WXGLColourBarCanvas(ColourBarCanvas,
                          fslgl.WXGLCanvasTarget,
                          wxgl.GLCanvas):
    def __init__(self, parent):
        
        wxgl.GLCanvas         .__init__(self, parent)
        ColourBarCanvas       .__init__(self)
        fslgl.WXGLCanvasTarget.__init__(self)

        def onsize(ev):
            self._initGL()
            self.Refresh()
            ev.Skip()

        self.Bind(wx.EVT_PAINT, self.draw)
        self.Bind(wx.EVT_SIZE, onsize)
