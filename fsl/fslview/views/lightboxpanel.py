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
import canvaspanel

class LightBoxPanel(canvaspanel.CanvasPanel):
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

    
    zax = lightboxcanvas.LightBoxCanvas.zax
    """See :attr:`fsl.fslview.gl.slicecanvas.SliceCanvas.zax`."""

    
    _labels = dict(lightboxcanvas.LightBoxCanvas._labels.items() +
                   canvaspanel   .CanvasPanel   ._labels.items())
    """Property labels to be used for GUI displays."""

    
    _view = props.VGroup(('showCursor',
                          'posSync',
                          'zrange',
                          'sliceSpacing',
                          'ncols',
                          'nrows',
                          'topRow',
                          'zax',
                          'showColourBar',
                          'colourBarLocation'))
    """Layout to be used for GUI displays."""


    def __init__(self,
                 parent,
                 imageList,
                 displayCtx,
                 glContext=None,
                 glVersion=None):
        """
        """

        canvaspanel.CanvasPanel.__init__(self,
                                         parent,
                                         imageList,
                                         displayCtx,
                                         glContext,
                                         glVersion)

        # self._scrollbar = wx.ScrollBar(self, style=wx.SB_VERTICAL)
        self._lbCanvas  = lightboxcanvas.LightBoxCanvas(self.getCanvasPanel(),
                                                        imageList,
                                                        glContext=glContext,
                                                        glVersion=glVersion)

        self._glContext = self._lbCanvas.glContext
        self._glVersion = glVersion

        self.bindProps('sliceSpacing', self._lbCanvas)
        self.bindProps('ncols',        self._lbCanvas)
        self.bindProps('nrows',        self._lbCanvas)
        self.bindProps('topRow',       self._lbCanvas)
        self.bindProps('zrange',       self._lbCanvas)
        self.bindProps('showCursor',   self._lbCanvas)
        self.bindProps('zax',          self._lbCanvas)

        self._canvasSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.getCanvasPanel().SetSizer(self._canvasSizer)

        self._canvasSizer.Add(self._lbCanvas, flag=wx.EXPAND, proportion=1)

        self._lbCanvas.Bind(wx.EVT_LEFT_DOWN,  self._onMouseEvent)
        self._lbCanvas.Bind(wx.EVT_MOTION,     self._onMouseEvent) 

        def move(*a):
            if not self.posSync: return
            xpos = self._displayCtx.location.getPos(self._lbCanvas.xax)
            ypos = self._displayCtx.location.getPos(self._lbCanvas.yax)
            zpos = self._displayCtx.location.getPos(self._lbCanvas.zax)
            self._lbCanvas.pos.xyz = (xpos, ypos, zpos)

        self._lbCanvas.pos.xyz = self._displayCtx.location
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
        w, h    = self._lbCanvas.GetClientSize()

        my = h - my

        clickPos = self._lbCanvas.canvasToWorld(mx, my)

        if clickPos is None:
            return

        xpos, ypos, zpos = clickPos

        log.debug('Mouse click on {}: '
                  '({}, {} -> {: 5.2f}, {: 5.2f}, {: 5.2f})'.format(
                      self._lbCanvas.name, mx, my, *clickPos))

        cpos = [clickPos[self._lbCanvas.xax],
                clickPos[self._lbCanvas.yax],
                clickPos[self._lbCanvas.zax]]

        self._lbCanvas.pos.xyz = cpos
        
        if self.posSync:
            self._displayCtx.location.xyz = clickPos
