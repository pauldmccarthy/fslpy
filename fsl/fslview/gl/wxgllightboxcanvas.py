#!/usr/bin/env python
#
# wxgllightboxcanvas.py - A wx.glcanvas.GLCanvas LightBoxCanvas.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`WXGLLightBoxCanvas`, which is both a
:class:`.LightBoxCanvas`, and a :class:`wx.glcanvas.GLCanvas`.
"""

import logging

import wx
import wx.glcanvas              as wxgl

import lightboxcanvas           as lightboxcanvas
import fsl.fslview.gl           as fslgl
import fsl.fslview.gl.resources as glresources


log = logging.getLogger(__name__)


class WXGLLightBoxCanvas(lightboxcanvas.LightBoxCanvas,
                         wxgl.GLCanvas,
                         fslgl.WXGLCanvasTarget):
    """A :class:`wx.glcanvas.GLCanvas` and a :class:`.SliceCanvas`, for 
    on-screen interactive 2D slice rendering from a collection of 3D
    overlays.
    """

    def __init__(self, parent, overlayList, displayCtx, zax=0):
        """Configures a few event handlers for cleaning up property
        listeners when the canvas is destroyed, and for redrawing on
        paint/resize events.
        """

        wxgl.GLCanvas                .__init__(self, parent)
        lightboxcanvas.LightBoxCanvas.__init__(self,
                                               overlayList,
                                               displayCtx,
                                               zax)
        fslgl.WXGLCanvasTarget       .__init__(self)
        
        # the overlay list is probably going to outlive
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
            self.removeListener('renderMode',     self.name)

            self.overlayList.removeListener('overlays',     self.name)
            self.displayCtx .removeListener('bounds',       self.name)
            self.displayCtx .removeListener('overlayOrder', self.name)
            
            for overlay in self.overlayList:
                
                disp  = self.displayCtx.getDisplay(overlay)
                globj = self._glObjects[overlay]

                disp.removeListener('overlayType',   self.name)
                disp.removeListener('enabled',       self.name)
                disp.removeListener('softwareMode',  self.name)

                globj.destroy()

                rt, rtName = self._prerenderTextures.get(overlay, (None, None))

                if rt is not None:
                    glresources.delete(rtName)

            if self._offscreenRenderTexture is not None:
                self._offscreenRenderTexture.destroy()

        self.Bind(wx.EVT_WINDOW_DESTROY, onDestroy)

        # When the canvas is resized, we have to update
        # the display bounds to preserve the aspect ratio
        def onResize(ev):
            self._updateDisplayBounds()
            ev.Skip()
        self.Bind(wx.EVT_SIZE, onResize)

# A convenient alias
LightBoxCanvas = WXGLLightBoxCanvas
