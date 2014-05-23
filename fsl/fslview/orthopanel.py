#!/usr/bin/env python
#
# orthopanel.py - A wx/OpenGL widget for displaying and interacting with a
# collection of 3D images. Displays three canvases, each of which shows the
# same image(s) on a different orthogonal plane.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import wx

import fsl.props               as props
import fsl.data.fslimage       as fslimage
import fsl.fslview.slicecanvas as slicecanvas


class OrthoPanel(wx.Panel, props.HasProperties):

    showXCanvas = props.Boolean(default=True)
    showYCanvas = props.Boolean(default=True)
    showZCanvas = props.Boolean(default=True)
    showCursor  = props.Boolean(default=True)

    xpos  = props.Double(clamped=True)
    ypos  = props.Double(clamped=True)
    zpos  = props.Double(clamped=True)

    xCanvasZoom = props.Double(minval=1.0,
                               maxval=20.0, 
                               default=1.0,
                               clamped=True)
    yCanvasZoom = props.Double(minval=1.0,
                               maxval=20.0, 
                               default=1.0,
                               clamped=True)
    zCanvasZoom = props.Double(minval=1.0,
                               maxval=20.0, 
                               default=1.0,
                               clamped=True)
        
    def __init__(self, parent, imageList):
        """
        Creates three SliceCanvas objects, each displaying the images
        in the given image list along a different axis.
        """

        if not isinstance(imageList, fslimage.ImageList):
            raise TypeError(
                'imageList must be a fsl.data.fslimage.ImageList instance')

        self.imageList = imageList
        self.name      = 'OrthoPanel_{}'.format(id(self))

        wx.Panel.__init__(self, parent)
        self.SetMinSize((300, 100))

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

        xmin = imageList.minBounds[0]
        xmax = imageList.maxBounds[0]
        ymin = imageList.minBounds[1]
        ymax = imageList.maxBounds[1] 
        zmin = imageList.minBounds[2]
        zmax = imageList.maxBounds[2]

        self.xpos = xmin + abs(xmax - xmin) / 2.0
        self.ypos = ymin + abs(ymax - ymin) / 2.0
        self.zpos = zmin + abs(zmax - zmin) / 2.0
        
        self.imageList.addListener(lambda il: self._updateImageBounds())
        self._updateImageBounds()

        self._configShowListeners()
        self._configZoomListeners()


    def _configShowListeners(self):
        def showCursor(ctx, value, valid):
            self.xcanvas.showCursor = value
            self.ycanvas.showCursor = value
            self.zcanvas.showCursor = value

        def showXCanvas(ctx, value, valid):
            self.sizer.Show(self.xcanvas, value)
            self.Layout()
        def showYCanvas(ctx, value, valid):
            self.sizer.Show(self.ycanvas, value)
            self.Layout()
        def showZCanvas(ctx, value, valid):
            self.sizer.Show(self.zcanvas, value)
            self.Layout() 

        self.addListener('showCursor',  self.name, showCursor)
        self.addListener('showXCanvas', self.name, showXCanvas)
        self.addListener('showYCanvas', self.name, showYCanvas)
        self.addListener('showZCanvas', self.name, showZCanvas)

            
    def _configZoomListeners(self):


        def xzoom(ctx, value, valid):
            value = 1.0 / value
            xlen = value * abs(self.imageList.maxBounds[1] -
                               self.imageList.minBounds[1])
            ylen = value * abs(self.imageList.maxBounds[2] -
                               self.imageList.minBounds[2])

            if value == 1:
                xcentre = self.imageList.minBounds[1] + 0.5 * xlen
                ycentre = self.imageList.minBounds[2] + 0.5 * ylen
            else:
                xcentre = self.ypos
                ycentre = self.zpos

            self.xcanvas.xmin = xcentre - 0.5 * xlen
            self.xcanvas.xmax = xcentre + 0.5 * xlen
            self.xcanvas.ymin = ycentre - 0.5 * ylen
            self.xcanvas.ymax = ycentre + 0.5 * ylen 

        self.addListener('xCanvasZoom', self.name, xzoom)

        
    def _updateImageBounds(self):
        """
        """
        
        xmin = self.imageList.minBounds[0]
        xmax = self.imageList.maxBounds[0]
        ymin = self.imageList.minBounds[1]
        ymax = self.imageList.maxBounds[1]
        zmin = self.imageList.minBounds[2]
        zmax = self.imageList.maxBounds[2]

        self.setConstraint('xpos', 'minval', xmin)
        self.setConstraint('xpos', 'maxval', xmax)
        self.setConstraint('ypos', 'minval', ymin)
        self.setConstraint('ypos', 'maxval', ymax)
        self.setConstraint('zpos', 'minval', zmin)
        self.setConstraint('zpos', 'maxval', zmax)
        
        # reset the cursor and min/max values in
        # case the old values were out of bounds
        self.xpos = self.xpos
        self.ypos = self.ypos
        self.zpos = self.zpos


    def _shiftCanvas(self, canvas, xax, yax, newx, newy):

        if newx >= canvas.xmin and \
           newx <= canvas.xmax and \
           newy >= canvas.ymin and \
           newy <= canvas.ymax:
            return

        xshift = 0
        yshift = 0

        imgxmin = self.imageList.minBounds[xax]
        imgxmax = self.imageList.maxBounds[xax]
        imgymin = self.imageList.minBounds[yax]
        imgymax = self.imageList.maxBounds[yax] 

        if   newx < canvas.xmin: xshift = newx - canvas.xmin
        elif newx > canvas.xmax: xshift = newx - canvas.xmax
        if   newy < canvas.ymin: yshift = newy - canvas.ymin 
        elif newy > canvas.ymax: yshift = newy - canvas.ymax 
            
        newxmin = canvas.xmin + xshift 
        newxmax = canvas.xmax + xshift
        newymin = canvas.ymin + xshift 
        newymax = canvas.ymax + xshift 

        if   newxmin < imgxmin: xshift = newxmin - imgxmin 
        elif newxmax > imgxmax: xshift = newxmax - imgxmax
        
        if   newymin < imgymin: yshift = newymin - imgymin
        elif newymax > imgymax: yshift = newymax - imgymax 

        if xshift != 0:
            print 'xshift {}'.format(xshift)
            canvas.xmin = canvas.xmin + xshift
            canvas.xmax = canvas.xmax + xshift
        if yshift != 0:
            print 'yshift {}'.format(yshift)
            canvas.ymin = canvas.ymin + yshift
            canvas.ymax = canvas.ymax + yshift


    def _setCanvasPosition(self, ev):
        """
        Called on mouse movement and left clicks. The currently
        displayed slices and cursor positions on each of the
        canvases follow mouse clicks and drags, and an
        EVT_LOCATION_EVENT is emitted when the cursor position
        changes.
        """

        if not ev.LeftIsDown():      return
        if len(self.imageList) == 0: return

        mx, my  = ev.GetPositionTuple()
        source  = ev.GetEventObject()
        w, h    = source.GetClientSize()

        my = h - my

        xpos = source.canvasToWorldX(mx)
        ypos = source.canvasToWorldY(my)

        if source == self.xcanvas:
            self.ypos         = xpos
            self.zpos         = ypos
            
            self.xcanvas.xpos = xpos
            self.xcanvas.ypos = ypos
            
            self.ycanvas.ypos = ypos
            self.ycanvas.zpos = xpos

            self.zcanvas.ypos = xpos
            self.zcanvas.zpos = ypos

            if self.yCanvasZoom != 1:
                self._shiftCanvas(self.ycanvas, 0, 2, self.ycanvas.xpos, ypos)

            if self.zCanvasZoom != 1:
                self._shiftCanvas(self.zcanvas, 0, 1, self.zcanvas.xpos, xpos)
                                 
        elif source == self.ycanvas:
            self.xpos         = xpos
            self.zpos         = ypos
            
            self.ycanvas.xpos = xpos
            self.ycanvas.ypos = ypos

            self.xcanvas.ypos = ypos
            self.xcanvas.zpos = xpos

            self.zcanvas.xpos = xpos
            self.zcanvas.zpos = ypos

            if self.xCanvasZoom != 1:
                self._shiftCanvas(self.xcanvas, 1, 2, self.xcanvas.xpos, ypos)

            if self.zCanvasZoom != 1:
                self._shiftCanvas(self.zcanvas, 0, 1, xpos, self.zcanvas.ypos)
            
        elif source == self.zcanvas:
            self.xpos         = xpos
            self.ypos         = ypos
            
            self.zcanvas.xpos = xpos
            self.zcanvas.ypos = ypos

            self.xcanvas.xpos = ypos
            self.xcanvas.zpos = xpos

            self.ycanvas.xpos = xpos
            self.ycanvas.zpos = ypos

            if self.xCanvasZoom != 1:
                self._shiftCanvas(self.xcanvas, 1, 2, ypos, self.xcanvas.ypos)

            if self.yCanvasZoom != 1:
                self._shiftCanvas(self.ycanvas, 0, 2, xpos, self.ycanvas.ypos)

            
class OrthoFrame(wx.Frame):
    """
    Convenience class for displaying an OrthoPanel in a standalone window.
    """

    def __init__(self, parent, imageList, title=None):
        
        wx.Frame.__init__(self, parent, title=title)
        self.panel = OrthoPanel(self, imageList)
        self.Layout()


class OrthoDialog(wx.Dialog):
    """
    Convenience class for displaying an OrthoPanel in a (possibly modal)
    dialog window.
    """

    def __init__(self, parent, imageList, title=None):
        
        wx.Dialog.__init__(self, parent, title=title)
        self.panel = OrthoPanel(self, imageList)
        self.Layout()
