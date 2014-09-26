#!/usr/bin/env python
#
# lightboxpanel.py - A panel which contains a LightBoxCanvas, for displaying
# multiple slices from a collection of images.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines the :class:`LightBoxPanel, a panel which contains a
:class:`~fsl.fslview.gl.LightBoxCanvas`, for displaying multiple slices from a
collection of images.
"""

import logging
log = logging.getLogger(__name__)

import wx

import props

import fsl.fslview.gl.wxgllightboxcanvas as lightboxcanvas
import fsl.fslview.viewpanel             as viewpanel

class LightBoxPanel(viewpanel.ViewPanel):
    """Convenience Panel which contains a 
    :class:`~fsl.fslview.gl.LightBoxCanvas` and a scrollbar, and sets up
    mouse-scrolling behaviour.
    """

    
    sliceSpacing = lightboxcanvas.LightBoxCanvas.sliceSpacing
    """See :attr:`fsl.fslview.gl.lightboxcanvas.LightBoxCanvas.sliceSpacing`.
    """

    
    ncols = lightboxcanvas.LightBoxCanvas.ncols
    """See :attr:`fsl.fslview.gl.lightboxcanvas.LightBoxCanvas.ncols`."""

    
    nrows = lightboxcanvas.LightBoxCanvas.nrows
    """See :attr:`fsl.fslview.gl.lightboxcanvas.LightBoxCanvas.nrows`."""

    
    topRow = lightboxcanvas.LightBoxCanvas.topRow
    """See :attr:`fsl.fslview.gl.lightboxcanvas.LightBoxCanvas.topRow`.""" 

    
    zrange = lightboxcanvas.LightBoxCanvas.zrange
    """See :attr:`fsl.fslview.gl.lightboxcanvas.LightBoxCanvas.zrange`."""

    
    showCursor = lightboxcanvas.LightBoxCanvas.showCursor
    """See :attr:`fsl.fslview.gl.slicecanvas.SliceCanvas.showCursor`."""

    
    zax = lightboxcanvas.LightBoxCanvas.zax
    """See :attr:`fsl.fslview.gl.slicecanvas.SliceCanvas.zax`."""

    
    posSync = props.Boolean(default=True)
    """If False, the cursor position shown in the
    :class:`fsl.fslview.gl.lightboxcanvas.LightBoxCanvas` instance, which
    is contained in this :class:`LightBoxPanel` (the
    :attr:`~fsl.fslview.gl.slicecanvas.SliceCanvas.pos` property) will not
    be synchronised to the :class:`~fsl.data.image.ImageList.location`
    :attr:`~fsl.data.image.ImageList.location` property.
    """ 

    
    _labels = {
        'zrange'       : 'Slice range',
        'posSync'      : 'Synchronise position',
        'sliceSpacing' : 'Slice spacing',
        'ncols'        : 'Number of columns',
        'nrows'        : 'Number of rows',
        'topRow'       : 'Top row',
        'showCursor'   : 'Show cursor',
        'zax'          : 'Z axis'}
    """Property labels to be used for GUI displays."""

    
    _view = props.VGroup(('showCursor',
                          'posSync',
                          'zrange',
                          'sliceSpacing',
                          'ncols',
                          'nrows',
                          'topRow',
                          'zax'))
    """Layout to be used for GUI displays."""


    @classmethod
    def isGLView(cls):
        """Overrides
        :meth:`~fsl.fslview.views.viewpanel.ViewPanel.isGLView`.

        Returns ``True``.
        """
        return True


    def __init__(self,
                 parent,
                 imageList,
                 displayCtx,
                 glContext=None,
                 glVersion=None):
        """
        """

        viewpanel.ViewPanel.__init__(self, parent, imageList, displayCtx)

        self._scrollbar = wx.ScrollBar(self, style=wx.SB_VERTICAL)
        self._canvas = lightboxcanvas.LightBoxCanvas(self,
                                                     imageList,
                                                     glContext=glContext,
                                                     glVersion=glVersion)

        self._glContext = self._canvas.glContext
        self._glVersion = glVersion

        self.bindProps('sliceSpacing', self._canvas)
        self.bindProps('ncols',        self._canvas)
        self.bindProps('nrows',        self._canvas)
        self.bindProps('topRow',       self._canvas)
        self.bindProps('zrange',       self._canvas)
        self.bindProps('showCursor',   self._canvas)
        self.bindProps('zax',          self._canvas)

        self._sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self._sizer)

        self._sizer.Add(self._canvas,    flag=wx.EXPAND, proportion=1)

        self._canvas.Bind(wx.EVT_LEFT_DOWN,  self._onMouseEvent)
        self._canvas.Bind(wx.EVT_MOTION,     self._onMouseEvent) 

        def move(*a):
            if not self.posSync: return
            xpos = self._displayCtx.location.getPos(self._canvas.xax)
            ypos = self._displayCtx.location.getPos(self._canvas.yax)
            zpos = self._displayCtx.location.getPos(self._canvas.zax)
            self._canvas.pos.xyz = (xpos, ypos, zpos)

        self._canvas.pos.xyz = self._displayCtx.location
        self._displayCtx.addListener('location', self._name, move)

        def onDestroy(ev):
            self._displayCtx.removeListener('location', self._name)
            ev.Skip()

        self.Bind(wx.EVT_WINDOW_DESTROY, onDestroy)

        self.Layout()

        
    def _onMouseEvent(self, ev):

        if not ev.LeftIsDown():       return
        if len(self._imageList) == 0: return

        mx, my  = ev.GetPositionTuple()
        w, h    = self._canvas.GetClientSize()

        my = h - my

        clickPos = self._canvas.canvasToWorld(mx, my)

        if clickPos is None:
            return

        xpos, ypos, zpos = clickPos

        log.debug('Mouse click on {}: '
                  '({}, {} -> {: 5.2f}, {: 5.2f}, {: 5.2f})'.format(
                      self._canvas.name, mx, my, *clickPos))

        cpos = [clickPos[self._canvas.xax],
                clickPos[self._canvas.yax],
                clickPos[self._canvas.zax]]

        self._canvas.pos.xyz = cpos
        
        if self.posSync:
            self._displayCtx.location.xyz = clickPos
