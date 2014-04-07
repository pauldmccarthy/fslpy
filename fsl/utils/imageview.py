#!/usr/bin/env python
#
# imgshow.py - A wx/OpenGL widget for displaying and interacting with a 3D
# image.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import                wx
import wx.glcanvas as wxgl
import OpenGL.GL   as gl

import fsl.utils.slicecanvas as slicecanvas


# Events. We can add custom events to Wx, which will then manage
# all of the listener registration/callback stuff for us.
WX_IMAGE_LOCATION = 1


class ImageView(wx.Panel):

    def __init__(self, parent, image, *args, **kwargs):

        self.image = image
        wx.Panel.__init__(self, parent, *args, **kwargs)

        self.SetMinSize((300,100))

        self.xcanvas = slicecanvas.SliceCanvas(self, image, axis=0)
        self.ycanvas = slicecanvas.SliceCanvas(self, image, axis=1)
        self.zcanvas = slicecanvas.SliceCanvas(self, image, axis=2)

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

        x = self.xcanvas.index
        y = self.ycanvas.index
        z = self.zcanvas.index

        if source == self.xcanvas:

            mx = mx * self.image.shape[1] / float(w)
            my = my * self.image.shape[2] / float(h)
            y,z = mx,my

        elif source == self.ycanvas:
            mx = mx * self.image.shape[0] / float(w)
            my = my * self.image.shape[2] / float(h)
            x,z = mx,my

        elif source == self.zcanvas:
            mx = mx * self.image.shape[0] / float(w)
            my = my * self.image.shape[1] / float(h)
            x,y = mx,my

        x = int(x)
        y = int(y)
        z = int(z)

        self.xcanvas.horizPos = y
        self.xcanvas.vertPos  = z
        self.ycanvas.horizPos = x
        self.ycanvas.vertPos  = z
        self.zcanvas.horizPos = x
        self.zcanvas.vertPos  = y

        self.xcanvas.index = x
        self.ycanvas.index = y
        self.zcanvas.index = z

        self.xcanvas.Refresh()
        self.ycanvas.Refresh()
        self.zcanvas.Refresh()
