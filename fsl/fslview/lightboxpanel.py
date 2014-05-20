#!/usr/bin/env python
#
# lightboxpanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import wx

import numpy                   as np

import fsl.props               as props
import fsl.data.fslimage       as fslimage
import fsl.fslview.slicecanvas as slicecanvas

class LightBoxPanel(wx.ScrolledWindow, props.HasProperties):

    sliceSpacing = props.Double(default=2.0)
    sliceAxis    = props.Choice(('2', '1', '0'),
                                ('z', 'y', 'x'))

    def __init__(self, parent, imageList):

        wx.ScrolledWindow.__init__(self, parent)
        # wx.Panel.__init__(self, parent)

        if not isinstance(imageList, fslimage.ImageList):
            raise TypeError(
                'imageList must be a fsl.data.fslimage.ImageList instance')

        self.sizer     = None
        self.canvases  = []
        self.imageList = imageList

        self._createCanvases()


    def _createCanvases(self):

        if self.sizer is not None:
            self.sizer.Clear(True)

            
        axis      = int(self.sliceAxis)
        imgMin    = self.imageList.minBounds[axis]
        imgMax    = self.imageList.maxBounds[axis]
        step      = self.sliceSpacing
        slicePoss = np.arange(imgMin + step / 2.0, imgMax, step)

        self.sizer    = wx.WrapSizer(wx.HORIZONTAL)
        self.canvases = []

        for i, pos in enumerate(slicePoss):
            
            if i == 0: ctx = None
            else:      ctx = self.canvases[0].context

            canvas = slicecanvas.SliceCanvas(self,
                                             self.imageList,
                                             zax=axis,
                                             context=ctx)
            canvas.zpos = pos
            canvas.SetMinSize((100, 100))

            self.canvases.append(canvas)
            self.sizer.Add(canvas)

        self.SetSizer(self.sizer)
        self.SetScrollbars(1, 1, 1, 1)
        self.Bind(wx.EVT_SIZE, lambda e: self.sizer.Layout())


class LightBoxFrame(wx.Frame):
    """
    Convenience class for displaying a LightBoxPanel in a standalone window.
    """

    def __init__(self, parent, imageList, title=None):
        
        wx.Frame.__init__(self, parent, title=title)
        self.panel = LightBoxPanel(self, imageList)
        self.Layout()


if __name__ == '__main__':

    import sys

    imgs    = map(fslimage.Image, sys.argv[1:])
    imgList = fslimage.ImageList(imgs)
    app     = wx.App()
    oframe  = LightBoxFrame(None, imgList, "Test")
    
    oframe.Show()



    # import wx.lib.inspection
    # wx.lib.inspection.InspectionTool().Show()    
    app.MainLoop()
