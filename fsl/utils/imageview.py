#!/usr/bin/env python
#
# imgshow.py - A wx/OpenGL widget for displaying and interacting with a 3D
# image. Displays three canvases, each of which shows a slice of the image
# along each dimension.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import wx

import fsl.utils.slicecanvas as slicecanvas


class ImageView(wx.Panel):

    def __init__(self, parent, image, *args, **kwargs):

        wx.Panel.__init__(self, parent, *args, **kwargs)
        self.SetMinSize((300,100))

        self.shape = image.shape

        self.xcanvas = slicecanvas.SliceCanvas(self, image, zax=2)
        self.ycanvas = slicecanvas.SliceCanvas(self, image, zax=1, master=self.xcanvas)
        self.zcanvas = slicecanvas.SliceCanvas(self, image, zax=0, master=self.xcanvas)

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.SetSizer(self.sizer)

        self.sizer.Add(self.xcanvas, flag=wx.EXPAND, proportion=1)
        self.sizer.Add(self.ycanvas, flag=wx.EXPAND, proportion=1)
        self.sizer.Add(self.zcanvas, flag=wx.EXPAND, proportion=1)

        self.Layout()

        self.xcanvas.Bind(wx.EVT_LEFT_DOWN, self.setCanvasPosition)
        self.ycanvas.Bind(wx.EVT_LEFT_DOWN, self.setCanvasPosition)
        self.zcanvas.Bind(wx.EVT_LEFT_DOWN, self.setCanvasPosition)
        self.xcanvas.Bind(wx.EVT_MOTION,    self.setCanvasPosition)
        self.ycanvas.Bind(wx.EVT_MOTION,    self.setCanvasPosition)
        self.zcanvas.Bind(wx.EVT_MOTION,    self.setCanvasPosition)


    def setCanvasPosition(self, ev):

        if not ev.LeftIsDown(): return

        mx,my  = ev.GetPositionTuple()
        source = ev.GetEventObject()
        w,h = source.GetClientSize()

        my = h - my

        x = self.xcanvas.zpos
        y = self.ycanvas.zpos
        z = self.zcanvas.zpos

        if source == self.xcanvas:

            mx = mx * self.shape[1] / float(w)
            my = my * self.shape[2] / float(h)
            y,z = mx,my

        elif source == self.ycanvas:
            mx = mx * self.shape[0] / float(w)
            my = my * self.shape[2] / float(h)
            x,z = mx,my

        elif source == self.zcanvas:
            mx = mx * self.shape[0] / float(w)
            my = my * self.shape[1] / float(h)
            x,y = mx,my

        x = int(x)
        y = int(y)
        z = int(z)

        self.xcanvas.xpos = y
        self.xcanvas.ypos = z
        self.ycanvas.xpos = x
        self.ycanvas.ypos = z
        self.zcanvas.xpos = x
        self.zcanvas.ypos = y

        self.xcanvas.zpos = x
        self.ycanvas.zpos = y
        self.zcanvas.zpos = z

        self.xcanvas.Refresh()
        self.ycanvas.Refresh()
        self.zcanvas.Refresh()


if __name__ == '__main__':

    import sys
    import nibabel as nb

    if len(sys.argv) != 2:
        print 'usage: imageview.py filename'
        sys.exit(1)

    app    = wx.App()
    image  = nb.load(sys.argv[1])

    frame  = wx.Frame(
        None,
        title=sys.argv[1])

    panel = ImageView(frame, image.get_data())

    frame.Layout()
    frame.Show()

    app.MainLoop()
