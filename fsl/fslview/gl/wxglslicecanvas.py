#!/usr/bin/env python
#
# wxglslicecanvas.py - A SliceCanvas which is rendered using a
# wx.glcanvas.GLCanvas panel.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The :class:`WXGLSliceCanvas` class both is a
:class:`~fsl.fslview.gl.slicecanvas.SliceCanvas` and a
:class:`wx.glcanvas.GLCanvas` panel.

It is the main class used for on-screen orthographic rendering of 3D image
data (although most of the functionality is provided by the
:class:`~fsl.fslview.gl.slicecanvas.SliceCanvas` class).
"""

import logging
log = logging.getLogger(__name__)

import wx
import wx.glcanvas    as wxgl

import slicecanvas    as slicecanvas
import fsl.fslview.gl as fslgl

class WXGLSliceCanvas(slicecanvas.SliceCanvas,
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

        wxgl.GLCanvas          .__init__(self, parent)
        slicecanvas.SliceCanvas.__init__(self, imageList, displayCtx, zax)
        fslgl.WXGLCanvasTarget .__init__(self)
        
        # the image list is probably going to outlive
        # this SliceCanvas object, so we do the right
        # thing and remove our listeners when we die
        def onDestroy(ev):
            ev.Skip()

            if ev.GetEventObject() is not self:
                return

            self.removeListener('zax',            self.name)
            self.removeListener('pos',            self.name)
            self.removeListener('displayBounds',  self.name)
            self.removeListener('showCursor',     self.name)
            self.removeListener('invertX',        self.name)
            self.removeListener('invertY',        self.name)
            self.removeListener('zoom',           self.name)
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
