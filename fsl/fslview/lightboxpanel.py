#!/usr/bin/env python
#
# lightboxpanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import wx

import props
import fsl.fslview.lightboxcanvas as lightboxcanvas

class LightBoxPanel(wx.Panel, props.HasProperties):
    """
    Convenience Panel which contains a a LightBoxCanvas and a scrollbar,
    and sets up mouse-scrolling behaviour.
    """

    def __init__(self, parent, *args, **kwargs):
        """
        Accepts the same parameters as the LightBoxCanvas constructor,
        although if you pass in a scrollbar, it will be ignored.
        """

        wx.Panel.__init__(self, parent)
        self.name = 'LightBoxPanel_{}'.format(id(self))

        self.scrollbar = wx.ScrollBar(self, style=wx.SB_VERTICAL)
        
        kwargs['scrollbar'] = self.scrollbar
        
        self.canvas = lightboxcanvas.LightBoxCanvas(self, *args, **kwargs)

        self.imageList = self.canvas.imageList

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)

        self.sizer.Add(self.canvas,    flag=wx.EXPAND, proportion=1)
        self.sizer.Add(self.scrollbar, flag=wx.EXPAND)

        self.canvas.Bind(wx.EVT_LEFT_DOWN, self.onMouseEvent)
        self.canvas.Bind(wx.EVT_MOTION,    self.onMouseEvent) 

        self.Bind(wx.EVT_MOUSEWHEEL, self.onMouseScroll)

        def move(*a):
            xpos = self.imageList.location.getPos(self.canvas.xax)
            ypos = self.imageList.location.getPos(self.canvas.yax)
            zpos = self.imageList.location.getPos(self.canvas.zax)
            self.canvas.pos.xyz = (xpos, ypos, zpos)

        self.imageList.addListener('location', self.name, move)

        def onDestroy(ev):
            self.imageList.removeListener('location', self.name)
            ev.Skip()

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
                      self.canvas.name, mx, my, xpos, ypos, zpos))

        self.imageList.location.xyz = xpos, ypos, zpos
        
            
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
