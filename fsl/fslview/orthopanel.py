#!/usr/bin/env python
#
# orthopanel.py - A wx/OpenGL widget for displaying and interacting with a
# collection of 3D images. Displays three canvases, each of which shows the
# same image(s) on a different orthogonal plane.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import sys

if True:
    import logging
    logging.basicConfig(
        format='%(levelname)8s '\
               '%(filename)20s '\
               '%(lineno)4d: '\
               '%(funcName)s - '\
               '%(message)s',
        level=logging.DEBUG)

import wx
import wx.lib.newevent as wxevent

import fsl.props               as props
import fsl.data.fslimage       as fslimage
import fsl.fslview.slicecanvas as slicecanvas

# The OrthoPanel emits a LocationEvent whenever the 'cursor' location
# changes. It contains three attributes, x, y, and z, corresponding to
# the current cursort location in the image space.
LocationEvent, EVT_LOCATION_EVENT = wxevent.NewEvent()

class OrthoPanel(wx.Panel):

    def __init__(self, parent, imageList):
        """
        Creates three SliceCanvas objects, each displaying the images
        in the given image list along a different axis.
        """

        if not isinstance(imageList, fslimage.ImageList):
            raise TypeError(
                'imageList must be a fsl.data.fslimage.ImageList instance')

        self.imageList = imageList

        wx.Panel.__init__(self, parent)
        self.SetMinSize((300,100))

        self.xcanvas = slicecanvas.SliceCanvas(self, imageList, zax=0)
        self.ycanvas = slicecanvas.SliceCanvas(self, imageList, zax=1,
                                               context=self.xcanvas.context)
        self.zcanvas = slicecanvas.SliceCanvas(self, imageList, zax=2,
                                               context=self.xcanvas.context)

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)

        self.sizer.Add(self.xcanvas, flag=wx.EXPAND, proportion=1)
        self.sizer.Add(self.ycanvas, flag=wx.EXPAND, proportion=1)
        self.sizer.Add(self.zcanvas, flag=wx.EXPAND, proportion=1)

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
        canvases follow mouse clicks and drags, and an
        EVT_LOCATION_EVENT is emitted when the cursor position
        changes.
        """

        if not ev.LeftIsDown(): return

        mx,my  = ev.GetPositionTuple()
        source = ev.GetEventObject()
        w,h = source.GetClientSize()

        my = h - my

        x = self.xcanvas.zpos
        y = self.ycanvas.zpos
        z = self.zcanvas.zpos

        mx = mx * (source.xmax - source.xmin) / float(w)
        my = my * (source.ymax - source.ymin) / float(h)

        if   source == self.xcanvas: y,z = mx,my
        elif source == self.ycanvas: x,z = mx,my
        elif source == self.zcanvas: x,y = mx,my

        self.setLocation(x,y,z)

        evt = LocationEvent(x=x,y=y,z=z)
        wx.PostEvent(self, evt)


class OrthoFrame(wx.Frame):
    """
    Convenience class for displaying an OrthoPanel in a standalone window.
    """

    def __init__(self, parent, imageList, title=None):
        
        wx.Frame.__init__(self, parent, title=title)
        self.panel = OrthoPanel(self, imageList)
        self.Layout()


def main():
    """
    Test program, displays the image specified on the command line.
    """

    if len(sys.argv) != 2:
        print 'usage: orthopanel.py filename'
        sys.exit(1)

    app       = wx.App()
    image     = fslimage.Image(sys.argv[1])
    imageList = fslimage.ImageList([image])
    
    frame  = OrthoFrame(None, imageList, title=sys.argv[1])
    frame.Show()

    app.MainLoop()

    
if __name__ == '__main__':
    main()
