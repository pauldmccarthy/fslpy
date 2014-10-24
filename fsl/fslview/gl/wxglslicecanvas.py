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
            self.imageList .removeListener('images', self.name)
            self.displayCtx.removeListener('bounds', self.name)
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
