#!/usr/bin/env python
#
# fslview.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import sys

import wx

import fsl.fslview.slicecanvas    as slicecanvas
import fsl.fslview.orthopanel     as orthopanel
import fsl.fslview.imagelistpanel as imagelistpanel

import fsl.data.fslimage as fslimage


class FslViewPanel(wx.Panel):

    def __init__(self, parent, imageList):
        
        wx.Panel.__init__(self, parent)
        self.imageList = imageList

        self.orthoPanel = orthopanel    .OrthoPanel(    self, imageList)
        self.listPanel  = imagelistpanel.ImageListPanel(self, imageList)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        self.sizer.Add(self.orthoPanel, flag=wx.EXPAND, proportion=1)
        self.sizer.Add(self.listPanel,  flag=wx.EXPAND)

        self.Layout()


FSL_TOOLNAME = 'fslview'


if __name__ == '__main__':

    app       = wx.App()
    images    = map(fslimage.Image, sys.argv[1:])
    imageList = fslimage.ImageList(images)
    
    frame     = wx.Frame(None, title='fslview')
    panel     = FslViewPanel(frame, imageList)

    frame.Show()
    app.MainLoop()
