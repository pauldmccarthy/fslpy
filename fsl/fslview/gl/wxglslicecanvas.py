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
import wx.glcanvas as wxgl
import slicecanvas as sc

class WXGLSliceCanvas(wxgl.GLCanvas, sc.SliceCanvas):
    """A :class:`wx.glcanvas.GLCanvas` and a
    :class:`~fsl.fslview.gl.slicecanvas.SliceCanvas`, for on-screen
    interactive 2D slice rendering from a collection of 3D images.
    """

    def __init__(self,
                 parent,
                 imageList,
                 zax=0,
                 glContext=None,
                 glVersion=None):
        """Configures a few event handlers for cleaning up property
        listeners when the canvas is destroyed, and for redrawing on
        paint/resize events.
        """

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

        
    def _initGL(self):
        """Calls the :meth:`~fsl.fslview.gl.slicecanvas.SliceCanvas._initGL`
        method, but ensures that it is done asynchronously.
        """
        wx.CallAfter(sc.SliceCanvas._initGL, self)

        
    def _getSize(self):
        """Returns the current canvas size. """
        return self.GetClientSize().Get()

        
    def _makeGLContext(self):
        """Creates and returns a :class:`wx.glcanvas.GLContext` object."""
        return wxgl.GLContext(self)

        
    def _setGLContext(self):
        """Configures the GL context for drawing to this canvas."""
        self.glContext.SetCurrent(self)

        
    def _refresh(self):
        """Triggers a redraw via the :mod:`wx` `Refresh` method."""
        self.Refresh()

        
    def _postDraw(self):
        """Called after the scene has been rendered. Swaps the front/back
        buffers. 
        """
        self.SwapBuffers()
