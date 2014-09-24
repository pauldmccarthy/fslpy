#!/usr/bin/env python
#
# screengrab.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)


import wx

import fsl.fslview.action as action

def _saveToFile(bitmap, filename):
    img = bitmap.ConvertToImage()
    img.SaveFile(filename, wx.BITMAP_TYPE_PNG)

def _copyToClipboard(bitmap):
    bmpObj = wx.BitmapDataObject(bitmap)

    with wx.Clipboard.Get() as cb:
        cb.SetData(bmpObj)
        cb.Flush()

def screengrab(wxObj, filename=None):
    """
    """
    rect     = wxObj.GetRect()
    dcScreen = wx.ScreenDC()
    bmp      = wx.EmptyBitmap(rect.width, rect.height)
    memDC    = wx.MemoryDC()

    memDC.SelectObject(bmp)
    memDC.Blit(0, 0, rect.width, rect.height, dcScreen, rect.x, rect.y)
    memDC.SelectObject(wx.NullBitmap)

    if filename is None: _copyToClipboard(bmp)
    else:                _saveToFile(     bmp, filename)



class ScreenGrabAction(action.Action):

    def doAction(self, activeViewPanel):
        print 'ScreenGrab!!!'
        if activeViewPanel is None:
            return
