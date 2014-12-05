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

import numpy as np

import props

import fsl.utils.layout                  as fsllayout
import fsl.fslview.gl.wxgllightboxcanvas as lightboxcanvas
import canvaspanel

class LightBoxPanel(canvaspanel.CanvasPanel):
    """Convenience Panel which contains a 
    :class:`~fsl.fslview.gl.LightBoxCanvas` and a scrollbar, and sets up
    mouse-scrolling behaviour.
    """

    nrows          = lightboxcanvas.LightBoxCanvas.nrows
    ncols          = lightboxcanvas.LightBoxCanvas.ncols
    topRow         = lightboxcanvas.LightBoxCanvas.topRow
    sliceSpacing   = lightboxcanvas.LightBoxCanvas.sliceSpacing
    zrange         = lightboxcanvas.LightBoxCanvas.zrange
    zax            = lightboxcanvas.LightBoxCanvas.zax
    showGridLines  = lightboxcanvas.LightBoxCanvas.showGridLines
    highlightSlice = lightboxcanvas.LightBoxCanvas.highlightSlice 

    zoom = props.Percentage(minval=10, maxval=500.0, default=350.0)
    """A property which allows the user to 'zoom' into the lightbox view. Is
    actually a proxy for the
    :attr:`~fsl.fslview.gl.lightboxcanvas.LightBoxCanvas.ncols`, with the
    zoom range (10, 500) linearly mapping to number of columns (30, 1).
    """



    
    _labels = dict(lightboxcanvas.LightBoxCanvas._labels.items() +
                   canvaspanel   .CanvasPanel   ._labels.items())
    """Property labels to be used for GUI displays."""


    def __init__(self,
                 parent,
                 imageList,
                 displayCtx):
        """
        """

        canvaspanel.CanvasPanel.__init__(self,
                                         parent,
                                         imageList,
                                         displayCtx)

        self._scrollbar = wx.ScrollBar(
            self.getCanvasPanel(),
            style=wx.SB_VERTICAL)
        
        self._lbCanvas  = lightboxcanvas.LightBoxCanvas(
            self.getCanvasPanel(),
            imageList,
            displayCtx)

        # My properties are the canvas properties
        self.bindProps('zax',            self._lbCanvas)
        self.bindProps('nrows',          self._lbCanvas)
        self.bindProps('ncols',          self._lbCanvas)
        self.bindProps('topRow',         self._lbCanvas)
        self.bindProps('sliceSpacing',   self._lbCanvas)
        self.bindProps('zrange',         self._lbCanvas)
        self.bindProps('showCursor',     self._lbCanvas)
        self.bindProps('showGridLines',  self._lbCanvas)
        self.bindProps('highlightSlice', self._lbCanvas)

        self._canvasSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.getCanvasPanel().SetSizer(self._canvasSizer)

        self._canvasSizer.Add(self._lbCanvas,  flag=wx.EXPAND, proportion=1)
        self._canvasSizer.Add(self._scrollbar, flag=wx.EXPAND)

        # Change the display context location on mouse clicks/drags,
        # and change the displayed row on mouse wheel movement
        self._lbCanvas.Bind(wx.EVT_LEFT_DOWN,  self._onMouseEvent)
        self._lbCanvas.Bind(wx.EVT_MOTION,     self._onMouseEvent)
        self._lbCanvas.Bind(wx.EVT_MOUSEWHEEL, self._onMouseWheel) 

        # When the display context location changes,
        # make sure the location is shown on the canvas
        self._lbCanvas.pos.xyz = self._displayCtx.location
        self._displayCtx.addListener('location',
                                     self._name,
                                     self._onLocationChange)

        # And remove that listener when
        # this panel is destroyed
        def onDestroy(ev):
            self._displayCtx.removeListener('location', self._name)
            ev.Skip()

        self.Bind(wx.EVT_WINDOW_DESTROY, onDestroy)

        self._onLightBoxChange()
        self._onZoom()

        # When any lightbox properties change,
        # make sure the scrollbar is updated
        self.addListener('ncols',        self._name, self._ncolsChanged)
        self.addListener('nrows',        self._name, self._onLightBoxChange)
        self.addListener('topRow',       self._name, self._onLightBoxChange)
        self.addListener('sliceSpacing', self._name, self._onLightBoxChange)
        self.addListener('zrange',       self._name, self._onLightBoxChange)
        self.addListener('zax',          self._name, self._onLightBoxChange)
        self.addListener('zoom',         self._name, self._onZoom)

        # When the scrollbar is moved,
        # update the canvas display
        self._scrollbar.Bind(wx.EVT_SCROLL, self._onScroll)

        self.Bind(wx.EVT_SIZE, self._onResize)

        self.Layout()

        
    def _onZoom(self, *a):
        """Called when the :attr:`zoom` property changes. Updates the
        number of columns on the lightbox canvas.
        """
        normZoom = 1.0 - (self.zoom - 10) / 490.0
        self._lbCanvas.ncols = int(1 + np.round(normZoom * 29))


    def _onResize(self, ev=None):
        """Called when the panel is resized. Automatically adjusts the
        number of lightbox rows to the maximum displayable number (given
        that the number of columns is fixed).
        """
        if ev is not None: ev.Skip()

        # Lay this panel out, so the
        # canvas panel size is up to date
        self.Layout()

        width,   height   = self._lbCanvas .GetClientSize().Get()
        sbWidth, sbHeight = self._scrollbar.GetClientSize().Get()

        width = width - sbWidth

        xlen = self._displayCtx.bounds.getLen(self._lbCanvas.xax)
        ylen = self._displayCtx.bounds.getLen(self._lbCanvas.yax)

        sliceWidth  = width / float(self._lbCanvas.ncols)
        sliceHeight = fsllayout.calcPixHeight(xlen, ylen, sliceWidth)

        self._lbCanvas.nrows = int(height / sliceHeight)


    def _onLocationChange(self, *a):
        """Called when the display context location changes.

        Updates the canvas location.
        """
        
        xpos = self._displayCtx.location.getPos(self._lbCanvas.xax)
        ypos = self._displayCtx.location.getPos(self._lbCanvas.yax)
        zpos = self._displayCtx.location.getPos(self._lbCanvas.zax)
        self._lbCanvas.pos.xyz = (xpos, ypos, zpos)


    def _ncolsChanged(self, *a):
        """Called when the lightbox canvas ``ncols`` property changes.
        Calculates the number of rows to display, and updates the
        scrollbar.
        """
        self._onResize()
        self._onLightBoxChange()


    def _onLightBoxChange(self, *a):
        """Called when any lightbox display properties change.

        Updates the scrollbar to reflect the change.
        """
        self._scrollbar.SetScrollbar(self._lbCanvas.topRow,
                                     self._lbCanvas.nrows,
                                     self._lbCanvas.getTotalRows(),
                                     self._lbCanvas.nrows,
                                     True)

        
    def _onScroll(self, *a):
        """Called when the scrollbar is moved.

        Updates the top row displayed on the canvas.
        """
        self._lbCanvas.topRow = self._scrollbar.GetThumbPosition()


    def _onMouseWheel(self, ev):
        """Called when the mouse wheel is moved.

        Updates the top row displayed on the canvas.
        """
        wheelDir = ev.GetWheelRotation()

        if   wheelDir > 0: wheelDir = -1
        elif wheelDir < 0: wheelDir =  1

        self._lbCanvas.topRow += wheelDir

        
    def _onMouseEvent(self, ev):
        """Called when the mouse is clicked or dragged on the canvas.

        Updates the canvas and display context location.
        """

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
        
        self._displayCtx.location.xyz = clickPos
