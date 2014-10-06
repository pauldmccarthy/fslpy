#!/usr/bin/env python
#
# wxgllightboxcanvas.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import wx
import wx.glcanvas    as wxgl

import lightboxcanvas as lightboxcanvas
import fsl.fslview.gl as fslgl

class WXGLLightBoxCanvas(wxgl.GLCanvas, lightboxcanvas.LightBoxCanvas):
    """A :class:`wx.glcanvas.GLCanvas` and a
    :class:`~fsl.fslview.gl.slicecanvas.SliceCanvas`, for on-screen
    interactive 2D slice rendering from a collection of 3D images.
    """

    def __init__(self, parent, imageList, zax=0):
        """Configures a few event handlers for cleaning up property
        listeners when the canvas is destroyed, and for redrawing on
        paint/resize events.
        """

        wxgl.GLCanvas                .__init__(self, parent)
        lightboxcanvas.LightBoxCanvas.__init__(self, imageList, zax) 
        
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

        
    def _getSize(self):
        """Returns the current canvas size. """
        return self.GetClientSize().Get()

        
    def _setGLContext(self):
        """Configures the GL context for drawing to this canvas."""
        fslgl.getWXGLContext().SetCurrent(self)

        
    def _refresh(self):
        """Triggers a redraw via the :mod:`wx` `Refresh` method."""
        self.Refresh()

        
    def _postDraw(self):
        """Called after the scene has been rendered. Swaps the front/back
        buffers. 
        """
        self.SwapBuffers()

LightBoxCanvas = WXGLLightBoxCanvas
