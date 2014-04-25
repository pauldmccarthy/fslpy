#!/usr/bin/env python
#
# fslview.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import wx

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


def fslviewArguments(parser):
    parser.add_argument('image', help='Image file to view', nargs='*')


def loadImages(args):
    imageList = fslimage.ImageList(map(fslimage.Image, args.image))
    return imageList

    
def interface(parent, imageList):
    panel = FslViewPanel(parent, imageList)
    return panel
    

FSL_TOOLNAME  = 'FSLView'
FSL_INTERFACE = interface
FSL_CONTEXT   = loadImages
FSL_ARGUMENTS = fslviewArguments
