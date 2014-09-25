#!/usr/bin/env python
#
# wxglslicecanvas.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import wx
import wx.glcanvas as wxgl
import slicecanvas as sc

class WXGLSliceCanvas(wxgl.GLCanvas, sc.SliceCanvas):

    def __init__(self,
                 parent,
                 imageList,
                 zax=0,
                 glContext=None,
                 glVersion=None):

        wxgl.GLCanvas .__init__(self, parent)
        sc.SliceCanvas.__init__(self, imageList, zax, glContext, glVersion) 
        
        # the image list is probably going to outlive
        # this SliceCanvas object, so we do the right
        # thing and remove our listeners when we die
        def onDestroy(ev):
            self.imageList.removeListener('images', self.name)
            self.imageList.removeListener('bounds', self.name)
            for image in self.imageList:
                disp = image.getAttribute('display')
                disp.removeListener('imageType',       self.name)
                disp.removeListener('enabled',         self.name)
                disp.removeListener('transform',       self.name)
                disp.removeListener('interpolation',   self.name)
                disp.removeListener('alpha',           self.name)
                disp.removeListener('displayRange',    self.name)
                disp.removeListener('clipLow',         self.name)
                disp.removeListener('clipHigh',        self.name)
                disp.removeListener('worldResolution', self.name)
                disp.removeListener('voxelResolution', self.name)
                disp.removeListener('cmap',            self.name)
                disp.removeListener('volume',          self.name)
            ev.Skip()

        self.Bind(wx.EVT_WINDOW_DESTROY, onDestroy)

        # When the canvas is resized, we have to update
        # the display bounds to preserve the aspect ratio
        def onResize(ev):
            self._updateDisplayBounds()
            ev.Skip()
        self.Bind(wx.EVT_SIZE, onResize)

        # All the work is done
        # by the draw method.
        self.Bind(wx.EVT_PAINT, self.draw)

    def _initGL(       self): wx.CallAfter(sc.SliceCanvas._initGL, self)
    def _getSize(      self): return self.GetClientSize().Get()
    def _makeGLContext(self): return wxgl.GLContext(self)
    def _setGLContext( self): self.glContext.SetCurrent(self)
    def _refresh(      self): self.Refresh()
