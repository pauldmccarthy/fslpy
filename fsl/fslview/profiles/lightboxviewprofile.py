#!/usr/bin/env python
#
# lightboxviewprofile.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)


import wx


def register(canvasPanel, imageList, displayCtx):
    return LightBoxViewProfile(canvasPanel, imageList, displayCtx)


def deregister(lightBoxViewProf):
    lightBoxViewProf.deregister()


class LightBoxViewProfile(object):
    def __init__(self, canvasPanel, imageList, displayCtx):
        self._canvasPanel = canvasPanel
        self._imageList   = imageList
        self._displayCtx  = displayCtx
        self._name        = '{}_{}'.format(self.__class__.__name__, id(self))
        
        self.register()


    def register(self):

        canvas = self._canvasPanel.getCanvas()

        canvas.Bind(wx.EVT_LEFT_DOWN,  self._onMouseEvent)
        canvas.Bind(wx.EVT_MOTION,     self._onMouseEvent)
        canvas.Bind(wx.EVT_MOUSEWHEEL, self._onMouseWheel) 


    def deregister(self):

        canvas = self._canvasPanel.getCanvas()

        canvas.Bind(wx.EVT_LEFT_DOWN,  None)
        canvas.Bind(wx.EVT_MOTION,     None)
        canvas.Bind(wx.EVT_MOUSEWHEEL, None)
        

    def _onMouseWheel(self, ev):
        """Called when the mouse wheel is moved.

        Updates the top row displayed on the canvas.
        """
        wheelDir = ev.GetWheelRotation()

        if   wheelDir > 0: wheelDir = -1
        elif wheelDir < 0: wheelDir =  1

        self._canvasPanel.getCanvas().topRow += wheelDir

        
    def _onMouseEvent(self, ev):
        """Called when the mouse is clicked or dragged on the canvas.

        Updates the canvas and display context location.
        """

        if not ev.LeftIsDown():       return
        if len(self._imageList) == 0: return

        canvas = self._canvasPanel.getCanvas()

        mx, my  = ev.GetPositionTuple()
        w, h    = canvas.GetClientSize()

        my = h - my

        clickPos = canvas.canvasToWorld(mx, my)

        if clickPos is None:
            return

        xpos, ypos, zpos = clickPos

        log.debug('Mouse click on {}: '
                  '({}, {} -> {: 5.2f}, {: 5.2f}, {: 5.2f})'.format(
                      canvas.name, mx, my, *clickPos))

        cpos = [clickPos[canvas.xax],
                clickPos[canvas.yax],
                clickPos[canvas.zax]]

        canvas.pos.xyz = cpos
        
        self._displayCtx.location.xyz = clickPos
