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

    cmap   = props.ColourMap()
    vrange = props.Bounds(ndims=1)
    label  = props.String()
    orient = props.Choice({
        'horizontal' : 'Horizontal',
        'vertical'   : 'Vertical'})

    
    def _getSize(      self): raise NotImplementedError()
    def _makeGLContext(self): raise NotImplementedError()
    def _setGLContext( self): raise NotImplementedError()
    def _refresh(      self): raise NotImplementedError()
    def _postDraw(     self): raise NotImplementedError()


    def __init__(self,
                 glContext=None,
                 glVersion=None):

        if glContext is None: self.glContext = self._makeGLContext()
        else:                 self.glContext = glContext

        self.glVersion = glVersion 
        self._glReady  = False
        self._tex      = None
        self._name     = '{}_{}'.format(self.__class__.__name__, id(self)) 

        def _update(*a):
            self._createColourBarTexture()
            self._refresh()

        for prop in ('cmap', 'vrange', 'label', 'orient'):
            self.addListener(prop, self._name, _update)
            

    def _initGL(self):
        self._setGLContext()
        fslgl.bootstrap(self.glVersion)
        self._createColourBarTexture()
        self._glReady = True


    def _createColourBarTexture(self):

        w, h = self._getSize()

        if w == 0 or h == 0:
            if self.orient == 'horizontal': w, h = 600, 200
            else:                           w, h = 200, 600
        
        bitmap = cbarbmp.colourBarBitmap(
            self.cmap,
            self.vrange.xlo,
            self.vrange.xhi,
            w, h,
            self.label,
            self.orient,
            'bottom')
        bitmap = np.flipud(bitmap)

        if self._tex is None:
            self._tex = gl.glGenTextures(1)

        print 'Updating colour bar texture ' \
            '({}) to {} ({:0.2f} - {:0.2f})'.format(
                self._tex, self.cmap.name, self.vrange.xlo, self.vrange.xhi)

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


    def draw(self, ev):
        if not self._glReady:
            self._initGL()
            return

        self._setGLContext()
        
        width, height = self.GetClientSize().Get()

        # viewport
        gl.glViewport(0, 0, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(-0.1, 1.1, -0.1, 1.1, -1.0, 1.0)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()

        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glShadeModel(gl.GL_FLAT)

        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)
        gl.glPixelStorei(gl.GL_PACK_ALIGNMENT,   1)
        
        gl.glEnable(gl.GL_TEXTURE_2D)
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
 
class WXGLColourBarCanvas(ColourBarCanvas, wxgl.GLCanvas):
    def __init__(self, parent, glContext, glVersion):
        wxgl.GLCanvas.__init__(self, parent)
        ColourBarCanvas.__init__(self, glContext, glVersion)

        def onsize(*a):
            self._createColourBarTexture()
            self.Refresh() 

        self.Bind(wx.EVT_PAINT, self.draw)
        self.Bind(wx.EVT_SIZE, onsize)

    def _initGL(self):
        wx.CallAfter(ColourBarCanvas._initGL, self)

    def _getSize(      self): return self.GetClientSize().Get()
    def _makeGLContext(self): return wxgl.GLContext(self)
    def _setGLContext( self): return self.glContext.SetCurrent(self)
    def _refresh(      self): self.Refresh()
    def _postDraw(     self): self.SwapBuffers()
