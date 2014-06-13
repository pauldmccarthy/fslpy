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

    # Properties which toggle display of each of
    # the three canvases, and the cursors on them.
    showXCanvas = props.Boolean(default=True)
    showYCanvas = props.Boolean(default=True)
    showZCanvas = props.Boolean(default=True)
    showCursor  = props.Boolean(default=True)

    # How should we lay out each of the three slice panels?
    layout = props.Choice(['Horizontal', 'Vertical', 'Grid'])

    # Property which sets the current displayed
    # position (in real world coordinates)
    pos = props.Point(ndims=3, labels=('X', 'Y', 'Z'))

    # Properties which set the current zoom
    # factor on each of the canvases
    xzoom = props.Real(minval=1.0,
                       maxval=10.0, 
                       default=1.0,
                       clamped=True)
    yzoom = props.Real(minval=1.0,
                       maxval=10.0, 
                       default=1.0,
                       clamped=True)
    zzoom = props.Real(minval=1.0,
                       maxval=10.0, 
                       default=1.0,
                       clamped=True)

    _view = props.HGroup((
        props.VGroup(('layout',
                      'showCursor',
                      'showXCanvas',
                      'showYCanvas',
                      'showZCanvas')),
        'pos',
        props.VGroup(('xzoom', 'yzoom', 'zzoom'))
    ))

    _labels = {
        'showCursor'  : 'Show cursor',
        'showXCanvas' : 'Show X canvas',
        'showYCanvas' : 'Show Y canvas',
        'showZCanvas' : 'Show Z canvas',
        'xzoom'       : 'X zoom',
        'yzoom'       : 'Y zoom',
        'zzoom'       : 'Z zoom',
        'pos'         : 'Position',
        'layout'      : 'Layout'
    }


    def __init__(self, parent, imageList, glContext=None):
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

        self.SetMinSize((600, 200))

        self.xcanvas = slicecanvas.SliceCanvas(self, imageList, zax=0,
                                               glContext=glContext)

        if glContext is None:
            glContext = self.xcanvas.glContext
        
        self.ycanvas = slicecanvas.SliceCanvas(self, imageList, zax=1,
                                               glContext=glContext)
        self.zcanvas = slicecanvas.SliceCanvas(self, imageList, zax=2,
                                               glContext=glContext)

        self.addListener('layout', self.name, self._layoutChanged)
        self._layoutChanged()

        self.xcanvas.Bind(wx.EVT_LEFT_DOWN, self._onMouseEvent)
        self.ycanvas.Bind(wx.EVT_LEFT_DOWN, self._onMouseEvent)
        self.zcanvas.Bind(wx.EVT_LEFT_DOWN, self._onMouseEvent)
        self.xcanvas.Bind(wx.EVT_MOTION,    self._onMouseEvent)
        self.ycanvas.Bind(wx.EVT_MOTION,    self._onMouseEvent)
        self.zcanvas.Bind(wx.EVT_MOTION,    self._onMouseEvent)

        bounds = imageList.bounds

        self.pos.xyz = [bounds.xlo + bounds.xlen / 2.0,
                        bounds.ylo + bounds.ylen / 2.0,
                        bounds.zlo + bounds.zlen / 2.0]
        
        self.imageList.addListener(
            'bounds',
            self.name,
            self._updateImageBounds)
        self._updateImageBounds()

        def onDestroy(ev):
            self.imageList.removeListener('bounds', self.name)
            ev.Skip()

        self.Bind(wx.EVT_WINDOW_DESTROY, onDestroy)
        self.Bind(wx.EVT_SIZE, self._resize)

        self._configPosListeners()
        self._configShowListeners()
        self._configZoomListeners()


    def _configPosListeners(self):
        """
        Configures listeners on the pos property - when it
        is changed, the displayed position is changed.
        """

        def move(*a): self.setPosition(*self.pos.xyz)
        self.addListener('pos', self.name, move)


    def _configShowListeners(self):
        """
        Configures listeners on the show* properties, so they can
        be used to toggle visibility of various things.
        """
        def showCursor(*a):
            
            self.xcanvas.showCursor = self.showCursor
            self.ycanvas.showCursor = self.showCursor
            self.zcanvas.showCursor = self.showCursor

        def toggle(canvas, toggle):
            self.sizer.Show(canvas, toggle)
            if self.layout.lower() == 'grid':
                self._configureGridSizes() 
            self.Layout()            

        self.addListener('showCursor', self.name, showCursor)
        self.addListener('showXCanvas',
                         self.name,
                         lambda *a: toggle(self.xcanvas, self.showXCanvas))
        self.addListener('showYCanvas', self.name,
                         lambda *a: toggle(self.ycanvas, self.showYCanvas))
        self.addListener('showZCanvas', self.name,
                         lambda *a: toggle(self.zcanvas, self.showZCanvas))

            
    def _configZoomListeners(self):
        """
        Configures listeners on the x/y/zzoom properties so when
        they are changed, the zoom factor on the corresponding canvas
        is changed.
        """
        def xzoom(*a): self.xcanvas.zoom = self.xzoom
        def yzoom(*a): self.ycanvas.zoom = self.yzoom
        def zzoom(*a): self.zcanvas.zoom = self.zzoom
            
        self.addListener('xzoom', self.name, xzoom)
        self.addListener('yzoom', self.name, yzoom)
        self.addListener('zzoom', self.name, zzoom)


    def _resize(self, ev):
        """
        Called whenever the panel is resized. Makes sure that the canvases
        are laid out nicely.
        """
        
        # allow default resize event handler to run
        ev.Skip()
        self._configureGridSizes()
        self.Layout()

        
    def _configureGridSizes(self):
        """
        If the 'Grid' layout has been selected, we have to manually specify
        sizes for each canvas, as the wx.WrapSizer doesn't know how big
        they should be. This is not a problem for wx.BoxSizers, as they
        just fill the available space, and give each canvas an equal share.
        """

        # Box sizers behave nicely. WrapSizer does not.
        if self.layout.lower() != 'grid': return
        
        width, height = self.GetClientSize().Get()

        # Generate a list of canvases for
        # which the 'show*Canvas' property is true
        canvases    = [self.xcanvas,     self.ycanvas,     self.zcanvas]
        show        = [self.showXCanvas, self.showYCanvas, self.showZCanvas]
        canvases, _ = zip(*filter(lambda (c, s): s, zip(canvases, show)))

        if len(canvases) == 1:
            canvases[0].SetMinSize((width, height))
        elif len(canvases) == 2:
            canvases[0].SetMinSize((width / 2, height))
            canvases[1].SetMinSize((width / 2, height))
        elif len(canvases) == 3:
            canvases[0].SetMinSize((width / 2, height / 2))
            canvases[1].SetMinSize((width / 2, height / 2))
            canvases[2].SetMinSize((width / 2, height / 2))

        
    def _layoutChanged(self, *a):
        """
        Called when the layout property changes. Updates the orthopanel layout
        accordingly.
        """

        layout = self.layout.lower()

        if   layout == 'horizontal': self.sizer = wx.BoxSizer( wx.HORIZONTAL)
        elif layout == 'vertical':   self.sizer = wx.BoxSizer( wx.VERTICAL)
        elif layout == 'grid':       self.sizer = wx.WrapSizer(wx.HORIZONTAL) 

        self.sizer.Add(self.xcanvas, flag=wx.EXPAND, proportion=1)
        self.sizer.Add(self.ycanvas, flag=wx.EXPAND, proportion=1)
        self.sizer.Add(self.zcanvas, flag=wx.EXPAND, proportion=1)

        self.SetSizer(self.sizer) 

        # for grid layout, we need to
        # manually specify canvas sizes
        if layout == 'grid':
            self._configureGridSizes()

        # the other layouts automatically
        # size the canvases for us
        else:
            self.xcanvas.SetMinSize((-1, -1))
            self.ycanvas.SetMinSize((-1, -1))
            self.zcanvas.SetMinSize((-1, -1))

        self.Layout()

        
    def _updateImageBounds(self, *a):
        """
        Called when the list of displayed images changes. Updates the
        minimum/maximum bounds on the x/y/zpos properties.
        """
        bounds = self.imageList.bounds

        self.pos.setMin(0, bounds.xlo)
        self.pos.setMax(0, bounds.xhi)
        self.pos.setMin(1, bounds.ylo)
        self.pos.setMax(1, bounds.yhi)
        self.pos.setMin(2, bounds.zlo)
        self.pos.setMax(2, bounds.zhi)
        
        # reset the cursor and min/max values in
        # case the old values were out of bounds
        self.pos.xyz = self.pos.xyz


    def _shiftCanvas(self, canvas, newx, newy):
        """
        Called when the position has changed, and zooming is enabled on
        the given canvas. Updates the display bounds on the canvas so that
        the current position is within them.
        """
        dispBounds = canvas.displayBounds

        if newx >= dispBounds.xlo and \
           newx <= dispBounds.xhi and \
           newy >= dispBounds.ylo and \
           newy <= dispBounds.yhi:
            return

        xax = canvas.xax
        yax = canvas.yax

        xshift = 0
        yshift = 0

        imgxmin = self.imageList.bounds.getLo(xax)
        imgxmax = self.imageList.bounds.getHi(xax)
        imgymin = self.imageList.bounds.getLo(yax)
        imgymax = self.imageList.bounds.getHi(yax)

        if   newx < dispBounds.xlo: xshift = newx - dispBounds.xlo
        elif newx > dispBounds.xhi: xshift = newx - dispBounds.xhi
        if   newy < dispBounds.ylo: yshift = newy - dispBounds.ylo 
        elif newy > dispBounds.yhi: yshift = newy - dispBounds.yhi 
            
        newxmin = dispBounds.xlo + xshift 
        newxmax = dispBounds.xhi + xshift
        newymin = dispBounds.ylo + yshift 
        newymax = dispBounds.yhi + yshift 

        if newxmin < imgxmin:
            newxmin = imgxmin
            newxmax = imgxmin + dispBounds.xlen
        elif newxmax > imgxmax:
            newxmax = imgxmax
            newxmin = imgxmax - dispBounds.xlen
        
        if newymin < imgymin:
            newymin = imgymin
            newymax = imgymin + dispBounds.ylen
        elif newymax > imgymax:
            newymax = imgymax
            newymin = imgymax - dispBounds.ylen

        dispBounds.all = [newxmin, newxmax, newymin, newymax]

        
    def setPosition(self, xpos, ypos, zpos):
        """
        Sets the currently displayed x/y/z position (in real world
        coordinates).
        """

        self.pos.xyz = [xpos, ypos, zpos]

        self.xcanvas.pos.xyz = [ypos, zpos, xpos]
        self.ycanvas.pos.xyz = [xpos, zpos, ypos]
        self.zcanvas.pos.xyz = [xpos, ypos, zpos]

        if self.xzoom != 1: self._shiftCanvas(self.xcanvas, ypos, zpos)
        if self.yzoom != 1: self._shiftCanvas(self.ycanvas, xpos, zpos)
        if self.zzoom != 1: self._shiftCanvas(self.zcanvas, xpos, ypos)


    def _onMouseEvent(self, ev):
        """
        Called on mouse movement and left clicks. The currently
        displayed slices and cursor positions on each of the
        canvases follow mouse clicks and drags.
        """

        if not ev.LeftIsDown():      return
        if len(self.imageList) == 0: return

        mx, my  = ev.GetPositionTuple()
        source  = ev.GetEventObject()
        w, h    = source.GetClientSize()

        my = h - my

        xpos = source.canvasToWorldX(mx)
        ypos = source.canvasToWorldY(my)

        if   source == self.xcanvas: self.setPosition(self.pos.x, xpos, ypos)
        elif source == self.ycanvas: self.setPosition(xpos, self.pos.y, ypos)
        elif source == self.zcanvas: self.setPosition(xpos, ypos, self.pos.z)
 
            
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

    def __init__(self, parent, imageList, title=None, style=None):

        if style is None: style =  wx.DEFAULT_DIALOG_STYLE
        else:             style |= wx.DEFAULT_DIALOG_STYLE
        
        wx.Dialog.__init__(self, parent, title=title, style=style)
        self.panel = OrthoPanel(self, imageList)
        self.Layout()
