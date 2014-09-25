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
    screenDC         = wx.ScreenDC()
    screenX, screenY = screenDC.Size
    screenbmp        = wx.EmptyBitmap(screenX, screenY)
    memDC            = wx.MemoryDC(screenbmp)

    # Create a bitmap of the entire screen
    memDC.Blit(0, 0, screenX, screenY, screenDC, 0, 0)
    memDC.SelectObject(wx.NullBitmap)

    # extract the relevant portion from that bitmap
    bbox       = wxObj.GetRect()
    offx, offy = wxObj.GetParent().ClientToScreen(wx.Point(bbox.x, bbox.y))

    bmp = screenbmp.GetSubBitmap(wx.Rect(offx, offy, bbox.width, bbox.height))

    if filename is None: _copyToClipboard(bmp)
    else:                _saveToFile(     bmp, filename)



class ScreenGrabAction(action.Action):

    def doAction(self, activeViewPanel):

        if activeViewPanel is None:
            return

        app = wx.GetApp()

        if app is None:
            raise RuntimeError('A wx.App has not been created')

        dlg = wx.FileDialog(app.GetTopWindow(),
                            message='Save screenshot',
                            style=wx.FD_SAVE)

        if dlg.ShowModal() != wx.ID_OK: return

        filename = dlg.GetPath()

        dlg.Destroy()
        wx.Yield()
        wx.CallAfter(lambda: screengrab(activeViewPanel, filename))
