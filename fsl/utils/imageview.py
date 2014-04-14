#!/usr/bin/env python
#
# imgshow.py - A wx/OpenGL widget for displaying and interacting with a 3D
# image. Displays three canvases, each of which shows a slice of the image
# along each dimension.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import wx
import wx.lib.newevent as wxevent

import fsl.utils.slicecanvas as slicecanvas

LocationEvent, EVT_LOCATION_EVENT = wxevent.NewEvent()

class ImageView(wx.Panel):

    def __init__(self, parent, image, *args, **kwargs):
        """
        Creates three SliceCanvas objects, each displaying a
        different axis of the given 3D numpy image.
        """

        wx.Panel.__init__(self, parent, *args, **kwargs)
        self.SetMinSize((300,100))

        self.shape = image.shape

        self.xcanvas = slicecanvas.SliceCanvas(self, image, zax=2)
        self.ycanvas = slicecanvas.SliceCanvas(self, image, zax=1,
                                               master=self.xcanvas)
        self.zcanvas = slicecanvas.SliceCanvas(self, image, zax=0,
                                               master=self.xcanvas)

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

        self.setLocation(x,y,z)

        evt = LocationEvent(x=x,y=y,z=z)
        wx.PostEvent(self, evt)


class ImageFrame(wx.Frame):
    """
    Convenience class for displaying an image in a standalone window.
    """

    def __init__(self, parent, image, title=None):
        wx.Frame.__init__(self, parent, title=title)

        self.image = image
        self.panel = ImageView(self, image)
        self.Layout()


if __name__ == '__main__':

    import sys
    import nibabel as nb

    if len(sys.argv) != 2:
        print 'usage: imageview.py filename'
        sys.exit(1)

    app    = wx.App()
    image  = nb.load(sys.argv[1])

    frame  = ImageFrame(
        None,
        image.get_data(),
        title=sys.argv[1])
    frame.Show()

    app.MainLoop()
