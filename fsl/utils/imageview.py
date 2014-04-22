#!/usr/bin/env python
#
# imgshow.py - A wx/OpenGL widget for displaying and interacting with a
# collection of 3D image. Displays three canvases, each of which shows
# a slice of the images along each dimension.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import sys

# import logging
# logging.basicConfig(
#     format='%(levelname)8s '\
#            '%(filename)20s '\
#            '%(lineno)4d: '\
#            '%(funcName)s - '\
#            '%(message)s',
#     level=logging.DEBUG)

import wx
import wx.lib.newevent as wxevent

import fsl.props             as props
import fsl.data.fslimage     as fslimage
import fsl.utils.slicecanvas as slicecanvas

LocationEvent, EVT_LOCATION_EVENT = wxevent.NewEvent()

class ImageView(wx.Panel):

    def __init__(self, parent, imageList, *args, **kwargs):
        """
        Creates three SliceCanvas objects, each displaying a
        different axis of the given 3D numpy image.
        """

        self.imageList = imageList

        wx.Panel.__init__(self, parent, *args, **kwargs)
        self.SetMinSize((300,100))

        self.shape = imageList.images[0].data.shape

        self.canvasPanel = wx.Panel(self)

        self.xcanvas = slicecanvas.SliceCanvas(
            self.canvasPanel, imageList, zax=0)
        self.ycanvas = slicecanvas.SliceCanvas(
            self.canvasPanel, imageList, zax=1, context=self.xcanvas.context)
        self.zcanvas = slicecanvas.SliceCanvas(
            self.canvasPanel, imageList, zax=2, context=self.xcanvas.context)


        self.controlPanel   = wx.Notebook(self)
        for i in range(len(imageList.images)):

            controlPanel = props.buildGUI(self.controlPanel, self.imageList.displays[i])
            self.controlPanel.AddPage(controlPanel, '{}'.format(i))

        self.mainSizer   = wx.BoxSizer(wx.VERTICAL)
        self.canvasSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.SetSizer(self.mainSizer)

        self.mainSizer.Add(self.canvasPanel,  flag=wx.EXPAND, proportion=1)
        self.mainSizer.Add(self.controlPanel, flag=wx.EXPAND)
        
        self.canvasPanel.SetSizer(self.canvasSizer)

        self.canvasSizer.Add(self.xcanvas, flag=wx.EXPAND, proportion=1)
        self.canvasSizer.Add(self.ycanvas, flag=wx.EXPAND, proportion=1)
        self.canvasSizer.Add(self.zcanvas, flag=wx.EXPAND, proportion=1)

        self.canvasPanel.Layout()
        self.Layout()

        self.xcanvas.Bind(wx.EVT_LEFT_DOWN, self._setCanvasPosition)
        self.ycanvas.Bind(wx.EVT_LEFT_DOWN, self._setCanvasPosition)
        self.zcanvas.Bind(wx.EVT_LEFT_DOWN, self._setCanvasPosition)
        self.xcanvas.Bind(wx.EVT_MOTION,    self._setCanvasPosition)
        self.ycanvas.Bind(wx.EVT_MOTION,    self._setCanvasPosition)
        self.zcanvas.Bind(wx.EVT_MOTION,    self._setCanvasPosition)

        
    def setLocation(self, x, y, z):
        """
        Programmatically set the currently displayed location
        on each of the canvases. This does not trigger an
        EVT_LOCATION_EVENT.
        """

        self.xcanvas.xpos = y
        self.xcanvas.ypos = z
        self.xcanvas.zpos = x

        self.ycanvas.xpos = x
        self.ycanvas.ypos = z
        self.ycanvas.zpos = y
        
        self.zcanvas.xpos = x
        self.zcanvas.ypos = y
        self.zcanvas.zpos = z

        self.xcanvas.Refresh()
        self.ycanvas.Refresh()
        self.zcanvas.Refresh()

    def setXLocation(self, x):
        self.setLocation(x, self.ycanvas.zpos, self.zcanvas.zpos)

    def setYLocation(self, y):
        self.setLocation(self.xcanvas.zpos, y, self.zcanvas.zpos)

    def setZLocation(self, z):
        self.setLocation(self.xcanvas.zpos, self.ycanvas.zpos, z)


    def _setCanvasPosition(self, ev):
        """
        Called on mouse movement and left clicks. The currently
        displayed slices and cursor positions on each of the
        canvases follow mouse clicks and drags.
        """

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

        if x < 0: x = 0
        if y < 0: y = 0
        if z < 0: z = 0

        if x >= self.shape[0]: x = self.shape[0]-1
        if y >= self.shape[1]: y = self.shape[1]-1
        if z >= self.shape[2]: z = self.shape[2]-1 

        self.setLocation(x,y,z)

        evt = LocationEvent(x=x,y=y,z=z)
        wx.PostEvent(self, evt)


class ImageFrame(wx.Frame):
    """
    Convenience class for displaying a collection of images in a standalone
    window.
    """

    def __init__(self, parent, imageList, title=None):
        wx.Frame.__init__(self, parent, title=title)

        self.imageList = imageList
        self.panel     = ImageView(self, imageList)
        self.Layout()


if __name__ == '__main__':

    if len(sys.argv) < 2:
        print 'usage: imageview.py filename [filename]'
        sys.exit(1)

    app       = wx.App()
    images    = map(fslimage.Image, sys.argv[1:])
    displays  = map(fslimage.ImageDisplay, images)
    imageList = fslimage.ImageList(images, displays)
    
    frame  = ImageFrame(
        None,
        imageList,
        title=sys.argv[1])
    frame.Show()

    app.MainLoop()
