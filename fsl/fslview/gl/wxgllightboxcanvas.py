#!/usr/bin/env python
#
# wxgllightboxcanvas.py - A wx.glcanvas.GLCanvas LightBoxCanvas.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`WXGLLightBoxCanvas`, which is both a
:class:`~fsl.fslview.gl.lightboxcanvas.LightBoxCanvas`, and a 
:class:`wx.glcanvas.GLCanvas`. 
"""

import logging
log = logging.getLogger(__name__)

import wx
import wx.glcanvas    as wxgl

import lightboxcanvas as lightboxcanvas
import fsl.fslview.gl as fslgl

class WXGLLightBoxCanvas(lightboxcanvas.LightBoxCanvas,
                         wxgl.GLCanvas,
                         fslgl.WXGLCanvasTarget):
    """A :class:`wx.glcanvas.GLCanvas` and a
    :class:`~fsl.fslview.gl.slicecanvas.SliceCanvas`, for on-screen
    interactive 2D slice rendering from a collection of 3D images.
    """

    def __init__(self, parent, imageList, displayCtx, zax=0):
        """Configures a few event handlers for cleaning up property
        listeners when the canvas is destroyed, and for redrawing on
        paint/resize events.
        """

        wxgl.GLCanvas                .__init__(self, parent)
        lightboxcanvas.LightBoxCanvas.__init__(self,
                                               imageList,
                                               displayCtx,
                                               zax)
        fslgl.WXGLCanvasTarget       .__init__(self)
        
        # the image list is probably going to outlive
        # this SliceCanvas object, so we do the right
        # thing and remove our listeners when we die
        def onDestroy(ev):
            ev.Skip()

            if ev.GetEventObject() is not self:
                return

            self.removeListener('zax',            self.name)
            self.removeListener('pos',            self.name)
            self.removeListener('pos',
                                '{}_zPosChanged'.format(self.name))
            self.removeListener('displayBounds',  self.name)
            self.removeListener('showCursor',     self.name)
            self.removeListener('invertX',        self.name)
            self.removeListener('invertY',        self.name)
            self.removeListener('zoom',           self.name)
            self.removeListener('sliceSpacing',   self.name)
            self.removeListener('ncols',          self.name)
            self.removeListener('nrows',          self.name)
            self.removeListener('zrange',         self.name)
            self.removeListener('showGridLines',  self.name)
            self.removeListener('highlightSlice', self.name)
            self.removeListener('topRow',         self.name)
            self.removeListener('twoStageRender', self.name)

            self.imageList .removeListener('images',     self.name)
            self.displayCtx.removeListener('bounds',     self.name)
            self.displayCtx.removeListener('imageOrder', self.name)
            for image in self.imageList:
                
                disp = self.displayCtx.getDisplayProperties(image)
                opts = disp.getDisplayOpts()
                
                image.removeListener('data',          self.name)
                disp .removeListener('imageType',     self.name)
                disp .removeListener('enabled',       self.name)
                disp .removeListener('transform',     self.name)
                disp .removeListener('softwareMode',  self.name)
                disp .removeListener('interpolation', self.name)
                disp .removeListener('alpha',         self.name)
                disp .removeListener('brightness',    self.name)
                disp .removeListener('contrast',      self.name)
                disp .removeListener('resolution',    self.name)
                disp .removeListener('volume',        self.name)
                opts .removeGlobalListener(           self.name)

        self.Bind(wx.EVT_WINDOW_DESTROY, onDestroy)

        # When the canvas is resized, we have to update
        # the display bounds to preserve the aspect ratio
        def onResize(ev):
            self._updateDisplayBounds()
            ev.Skip()
        self.Bind(wx.EVT_SIZE, onResize)

# A convenient alias
LightBoxCanvas = WXGLLightBoxCanvas
