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
import fsl.fslview.gl.lightboxcanvas as lightboxcanvas

class LightBoxPanel(wx.Panel, props.HasProperties):
    """Convenience Panel which contains a 
    :class:`~fsl.fslview.gl.LightBoxCanvas` and a scrollbar, and sets up
    mouse-scrolling behaviour.
    """

    
    sliceSpacing = lightboxcanvas.LightBoxCanvas.sliceSpacing
    """See :attr:`fsl.fslview.gl.lightboxcanvas.LightBoxCanvas.sliceSpacing`.
    """

    
    ncols = lightboxcanvas.LightBoxCanvas.ncols
    """See :attr:`fsl.fslview.gl.lightboxcanvas.LightBoxCanvas.ncols`."""

    
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
        'showCursor'   : 'Show cursor',
        'zax'          : 'Z axis'}
    """Property labels to be used for GUI displays."""

    
    _view = props.VGroup(('showCursor',
                          'posSync',
                          'zrange',
                          'sliceSpacing',
                          'ncols',
                          'zax'))
    """Layout to be used for GUI displays.""" 


    def __init__(self, parent, imageList, displayCtx, glContext=None):
        """
        """

        wx.Panel.__init__(self, parent)
        props.HasProperties.__init__(self)

        self.imageList  = imageList
        self.displayCtx = displayCtx 
        self.name       = 'LightBoxPanel_{}'.format(id(self))

        self.scrollbar = wx.ScrollBar(self, style=wx.SB_VERTICAL)
        self.canvas = lightboxcanvas.LightBoxCanvas(self,
                                                    imageList,
                                                    glContext=glContext,
                                                    scrollbar=self.scrollbar)

        self.bindProps('sliceSpacing', self.canvas)
        self.bindProps('ncols',        self.canvas)
        self.bindProps('zrange',       self.canvas)
        self.bindProps('showCursor',   self.canvas)
        self.bindProps('zax',          self.canvas)

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)

        self.sizer.Add(self.canvas,    flag=wx.EXPAND, proportion=1)
        self.sizer.Add(self.scrollbar, flag=wx.EXPAND)

        self.canvas.Bind(wx.EVT_LEFT_DOWN, self.onMouseEvent)
        self.canvas.Bind(wx.EVT_MOTION,    self.onMouseEvent) 

        self.Bind(wx.EVT_MOUSEWHEEL, self.onMouseScroll)

        def move(*a):
            if not self.posSync: return
            xpos = self.displayCtx.location.getPos(self.canvas.xax)
            ypos = self.displayCtx.location.getPos(self.canvas.yax)
            zpos = self.displayCtx.location.getPos(self.canvas.zax)
            self.canvas.pos.xyz = (xpos, ypos, zpos)

        self.displayCtx.addListener('location', self.name, move)

        def onDestroy(ev):
            self.displayCtx.removeListener('location', self.name)
            ev.Skip()

        self.Bind(wx.EVT_WINDOW_DESTROY, onDestroy)

        self.Layout()

        
    def onMouseEvent(self, ev):

        if not ev.LeftIsDown():      return
        if len(self.imageList) == 0: return

        mx, my  = ev.GetPositionTuple()
        w, h    = self.canvas.GetClientSize()

        my = h - my

        clickPos = self.canvas.canvasToWorld(mx, my)

        if clickPos is None:
            return

        xpos, ypos, zpos = clickPos

        log.debug('Mouse click on {}: '
                  '({}, {} -> {: 5.2f}, {: 5.2f}, {: 5.2f})'.format(
                      self.canvas.name, mx, my, *clickPos))

        cpos = [clickPos[self.canvas.xax],
                clickPos[self.canvas.yax],
                clickPos[self.canvas.zax]]

        self.canvas.pos.xyz = cpos
        
        if self.posSync:
            self.displayCtx.location.xyz = clickPos
        
            
    def onMouseScroll(self, ev):

        wheelDir = ev.GetWheelRotation()

        if   wheelDir > 0: wheelDir = -1
        elif wheelDir < 0: wheelDir =  1

        curPos       = self.scrollbar.GetThumbPosition()
        newPos       = curPos + wheelDir
        sbRange      = self.scrollbar.GetRange()
        rowsOnScreen = self.scrollbar.GetPageSize()

        if self.scrollbar.GetPageSize() >= self.scrollbar.GetRange():
            return
        if newPos < 0 or newPos + rowsOnScreen > sbRange:
            return

        self.scrollbar.SetThumbPosition(curPos + wheelDir)
        self.canvas._updateDisplayBounds()
        self.canvas.Refresh()
