#!/usr/bin/env python
#
# imagepanel.py - A panel for displaying a wx.Image.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ImagePanel` class, for displaying a
:class:`wx.Image`.
"""

import logging
log = logging.getLogger(__name__)

import wx

class ImagePanel(wx.Panel):
    """A :class:`wx.Panel` which may be used to display a resizeable
    :class:`wx.Image`. The image is scaled to the size of the panel.
    """

    def __init__(self, parent, image=None):

        wx.Panel.__init__(self, parent)

        self.Bind(wx.EVT_PAINT, self.Draw)
        self.Bind(wx.EVT_SIZE,  self._onSize)


    def SetImage(self, image):
        self._image = image
        self.Refresh()

        
    def _onSize(self, ev):
        self.Refresh()
        ev.Skip()
        
        
    def Draw(self, ev=None):
        
        self.ClearBackground()

        if self.image is None:
            return

        if ev is None: dc = wx.ClientDC(self)
        else:          dc = wx.PaintDC( self)
        
        width, height = dc.GetSize().Get()

        if width == 0 or height == 0:
            return

        bitmap = wx.BitmapFromImage(self.image.Scale(width, height))
        
        dc.DrawBitmap(bitmap, 0, 0, False)
