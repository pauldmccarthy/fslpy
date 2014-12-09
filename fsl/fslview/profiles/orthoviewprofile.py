#!/usr/bin/env python
#
# orthoviewprofile.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import wx


def register(canvasPanel, imageList, displayCtx):
    return OrthoViewProfile(canvasPanel, imageList, displayCtx)


def deregister(orthoViewProf):
    orthoViewProf.deregister()


class OrthoViewProfile(object):

    def __init__(self, canvasPanel, imageList, displayCtx):
        self._canvasPanel = canvasPanel
        self._imageList   = imageList
        self._displayCtx  = displayCtx

        self._name = '{}_{}'.format(self.__class__.__name__, id(self))

        self.register()

        
    def _onMouseEvent(self, ev):
        """Called on mouse movement and left clicks. The currently
        displayed slices and cursor positions on each of the
        canvases follow mouse clicks and drags.
        """

        if not ev.LeftIsDown():       return
        if len(self._imageList) == 0: return

        orthoPanel = self._canvasPanel
        xcanvas    = orthoPanel._xcanvas
        ycanvas    = orthoPanel._ycanvas
        zcanvas    = orthoPanel._zcanvas

        mx, my  = ev.GetPositionTuple()
        source  = ev.GetEventObject()
        w, h    = source.GetClientSize()

        my = h - my

        xpos, ypos = source.canvasToWorld(mx, my)
        zpos       = source.pos.z

        log.debug('Mouse click on canvas {}: ({}, {} -> {}, {})'.format(
            source.name, mx, my, xpos, ypos))

        if   source == xcanvas: orthoPanel.setPosition(zpos, xpos, ypos)
        elif source == ycanvas: orthoPanel.setPosition(xpos, zpos, ypos)
        elif source == zcanvas: orthoPanel.setPosition(xpos, ypos, zpos)

        self._displayCtx.disableListener('location', self._name)

        if   source == xcanvas:
            self._displayCtx.location.yz = [xpos, ypos]
        elif source == ycanvas:
            self._displayCtx.location.xz = [xpos, ypos]
        elif source == zcanvas:
            self._displayCtx.location.xy = [xpos, ypos]

        self._displayCtx.enableListener('location', self._name)

        
    def register(self):
        self._canvasPanel._xcanvas.Bind(wx.EVT_LEFT_DOWN, self._onMouseEvent)
        self._canvasPanel._ycanvas.Bind(wx.EVT_LEFT_DOWN, self._onMouseEvent)
        self._canvasPanel._zcanvas.Bind(wx.EVT_LEFT_DOWN, self._onMouseEvent)
        self._canvasPanel._xcanvas.Bind(wx.EVT_MOTION,    self._onMouseEvent)
        self._canvasPanel._ycanvas.Bind(wx.EVT_MOTION,    self._onMouseEvent)
        self._canvasPanel._zcanvas.Bind(wx.EVT_MOTION,    self._onMouseEvent)


    def deregister(self):
        self._canvasPanel._xcanvas.Bind(wx.EVT_LEFT_DOWN, None)
        self._canvasPanel._ycanvas.Bind(wx.EVT_LEFT_DOWN, None)
        self._canvasPanel._zcanvas.Bind(wx.EVT_LEFT_DOWN, None)
        self._canvasPanel._xcanvas.Bind(wx.EVT_MOTION,    None)
        self._canvasPanel._ycanvas.Bind(wx.EVT_MOTION,    None)
        self._canvasPanel._zcanvas.Bind(wx.EVT_MOTION,    None)
