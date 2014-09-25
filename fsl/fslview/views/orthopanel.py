#!/usr/bin/env python
#
# orthopanel.py - A wx/OpenGL widget for displaying and interacting with a
# collection of 3D images. 
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""A :mod:`wx`/:mod:`OpenGL` widget for displaying and interacting with a
collection of 3D images (see :class:`~fsl.data.image.ImageList`).

Displays three canvases, each of which shows the same image(s) on a
different orthogonal plane. The displayed location is driven by the
:attr:`fsl.fslview.displaycontext.DisplayContext.location` property.
"""

import logging
log = logging.getLogger(__name__)

import wx
import props

import fsl.fslview.gl.slicecanvas as slicecanvas
import fsl.fslview.viewpanel      as viewpanel
import colourbarpanel 

class OrthoPanel(viewpanel.ViewPanel):

    # Properties which toggle display of each of
    # the three canvases, and the cursors on them.
    showXCanvas = props.Boolean(default=True)
    showYCanvas = props.Boolean(default=True)
    showZCanvas = props.Boolean(default=True)
    showCursor  = props.Boolean(default=True)

    
    posSync = props.Boolean(default=True)
    """Should the position shown in each of the
    :class:`~fsl.fslview.gl.slicecanvas.SliceCanvas` instances 
    be synchronised to the :class:`~fsl.data.image.ImageList.location`
    :attr:`~fsl.data.image.ImageList.location` property?
    """
    

    # How should we lay out each of the three slice panels?
    layout = props.Choice(['Horizontal', 'Vertical', 'Grid'])
    
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

    showColourBar = props.Boolean(default=False)

    colourBarLocation = props.Choice({
        'top'    : 'Top',
        'bottom' : 'Bottom',
        'left'   : 'Left',
        'right'  : 'Right'})
    

    _view = props.HGroup((
        props.VGroup(('layout',
                      'posSync',
                      'showCursor',
                      'showXCanvas',
                      'showYCanvas',
                      'showZCanvas',
                      'showColourBar',
                      props.Widget(
                          'colourBarLocation',
                          visibleWhen=lambda i: i.showColourBar))),
        props.VGroup(('xzoom', 'yzoom', 'zzoom'))
    ))

    _labels = {
        'showCursor'        : 'Show cursor',
        'posSync'           : 'Synchronise location',
        'showXCanvas'       : 'Show X canvas',
        'showYCanvas'       : 'Show Y canvas',
        'showZCanvas'       : 'Show Z canvas',
        'xzoom'             : 'X zoom',
        'yzoom'             : 'Y zoom',
        'zzoom'             : 'Z zoom',
        'showColourBar'     : 'Show/hide colour bar',
        'colourBarLocation' : 'Colour bar location',
        'layout'            : 'Layout'
    }

    @classmethod
    def isGLView(cls):
        """Overrides
        :meth:`~fsl.fslview.views.viewpanel.ViewPanel.isGLView`.

        Returns ``True``.
        """
        return True
        

    def __init__(self,
                 parent,
                 imageList,
                 displayCtx,
                 glContext=None,
                 glVersion=None):
        """
        Creates three SliceCanvas objects, each displaying the images
        in the given image list along a different axis. 
        """

        viewpanel.ViewPanel.__init__(self,
                                     parent,
                                     imageList,
                                     displayCtx)

        self.SetBackgroundColour('black')

        self._canvasPanel = wx.Panel(self)

        self._xcanvas = slicecanvas.WXGLSliceCanvas(self._canvasPanel,
                                                    imageList, zax=0,
                                                    glContext=glContext,
                                                    glVersion=glVersion)

        if glContext is None:
            glContext = self._xcanvas.glContext

        self._glContext = glContext
        self._glVersion = glVersion
        
        self._ycanvas = slicecanvas.WXGLSliceCanvas(self._canvasPanel,
                                                    imageList, zax=1,
                                                    glContext=glContext,
                                                    glVersion=glVersion)
        self._zcanvas = slicecanvas.WXGLSliceCanvas(self._canvasPanel,
                                                    imageList, zax=2,
                                                    glContext=glContext,
                                                    glVersion=glVersion)

        self._colourBar = colourbarpanel.ColourBarPanel(
            self,
            self._imageList,
            self._displayCtx)

        self.addListener('showColourBar',
                         self._name,
                         self._configColourBar)
        self.addListener('colourBarLocation',
                         self._name,
                         self._configColourBar)

        self.addListener('layout', self._name, self._layoutChanged)

        self._configColourBar()
        self._layoutChanged()

        self._xcanvas.Bind(wx.EVT_LEFT_DOWN, self._onMouseEvent)
        self._ycanvas.Bind(wx.EVT_LEFT_DOWN, self._onMouseEvent)
        self._zcanvas.Bind(wx.EVT_LEFT_DOWN, self._onMouseEvent)
        self._xcanvas.Bind(wx.EVT_MOTION,    self._onMouseEvent)
        self._ycanvas.Bind(wx.EVT_MOTION,    self._onMouseEvent)
        self._zcanvas.Bind(wx.EVT_MOTION,    self._onMouseEvent)

        def move(*a):
            if self.posSync:
                self.setPosition(*self._displayCtx.location)

        self.setPosition(*self._displayCtx.location)
        self._displayCtx.addListener('location', self._name, move) 
        
        def onDestroy(ev):
            self._displayCtx.removeListener('location', self._name)
            ev.Skip()

        self.Bind(wx.EVT_WINDOW_DESTROY, onDestroy)
        self.Bind(wx.EVT_SIZE, self._resize)

        self._configShowListeners()
        self._configZoomListeners()


    def _configShowListeners(self):
        """
        Configures listeners on the show* properties, so they can
        be used to toggle visibility of various things.
        """
        def showCursor(*a):
            
            self._xcanvas.showCursor = self.showCursor
            self._ycanvas.showCursor = self.showCursor
            self._zcanvas.showCursor = self.showCursor

        def toggle(canvas, toggle):
            self._canvasSizer.Show(canvas, toggle)
            if self.layout.lower() == 'grid':
                self._configureGridSizes() 
            self._canvasPanel.Layout()            

        self.addListener('showCursor',  self._name, showCursor)
        self.addListener('showXCanvas', self._name,
                         lambda *a: toggle(self._xcanvas, self.showXCanvas))
        self.addListener('showYCanvas', self._name,
                         lambda *a: toggle(self._ycanvas, self.showYCanvas))
        self.addListener('showZCanvas', self._name,
                         lambda *a: toggle(self._zcanvas, self.showZCanvas))

            
    def _configZoomListeners(self):
        """
        Configures listeners on the x/y/zzoom properties so when
        they are changed, the zoom factor on the corresponding canvas
        is changed.
        """
        def xzoom(*a): self._xcanvas.zoom = self.xzoom
        def yzoom(*a): self._ycanvas.zoom = self.yzoom
        def zzoom(*a): self._zcanvas.zoom = self.zzoom
            
        self.addListener('xzoom', self._name, xzoom)
        self.addListener('yzoom', self._name, yzoom)
        self.addListener('zzoom', self._name, zzoom)


    def _configColourBar(self, *a):
        """
        """

        # TODO unbind props on previous colour bar

        if not self.showColourBar:
            
            self._sizer = wx.BoxSizer(wx.HORIZONTAL)
            self._sizer.Add(self._canvasPanel, flag=wx.EXPAND, proportion=1)
            
            self.SetSizer(self._sizer)
            self.Layout()
            return

        if self.colourBarLocation in ('top', 'bottom'):
            self._colourBar.orientation = 'horizontal'
            self._sizer = wx.BoxSizer(wx.VERTICAL)
        else:
            self._colourBar.orientation = 'vertical'
            self._sizer = wx.BoxSizer(wx.HORIZONTAL)

        if self.colourBarLocation in ('top', 'left'):
            self._sizer.Add(self._colourBar,   flag=wx.EXPAND)
            self._sizer.Add(self._canvasPanel, flag=wx.EXPAND, proportion=1)
        else:
            self._sizer.Add(self._canvasPanel, flag=wx.EXPAND, proportion=1)
            self._sizer.Add(self._colourBar,   flag=wx.EXPAND)
                
        self.SetSizer(self._sizer)
        self.Layout()

            
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
        
        width, height = self._canvasPanel.GetClientSize().Get()

        # Generate a list of canvases for
        # which the 'show*Canvas' property is true
        canvases    = [self._xcanvas,     self._ycanvas,     self._zcanvas]
        show        = [self.showXCanvas,  self.showYCanvas,  self.showZCanvas]

        if not any(show): return
            
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

        if   layout == 'horizontal':
            self._canvasSizer = wx.BoxSizer(wx.HORIZONTAL)
        elif layout == 'vertical':
            self._canvasSizer = wx.BoxSizer(wx.VERTICAL)
        elif layout == 'grid':
            self._canvasSizer = wx.WrapSizer(wx.HORIZONTAL) 

        for c in [self._xcanvas, self._ycanvas, self._zcanvas]:
            self._canvasSizer.Add(c, flag=wx.EXPAND, proportion=1)

        self._canvasPanel.SetSizer(self._canvasSizer)

        # for grid layout, we need to
        # manually specify canvas sizes
        if layout == 'grid':
            self._configureGridSizes()

        # the other layouts automatically
        # size the canvases for us
        else:
            self._xcanvas.SetMinSize((-1, -1))
            self._ycanvas.SetMinSize((-1, -1))
            self._zcanvas.SetMinSize((-1, -1))

        self.Layout()
        self._canvasPanel.Layout()

        
    def setPosition(self, xpos, ypos, zpos):
        """
        Sets the currently displayed x/y/z position (in real world
        coordinates).
        """

        self._xcanvas.pos.xyz = [ypos, zpos, xpos]
        self._ycanvas.pos.xyz = [xpos, zpos, ypos]
        self._zcanvas.pos.xyz = [xpos, ypos, zpos]

        if self.xzoom != 1: self._xcanvas.panDisplayToShow(ypos, zpos)
        if self.yzoom != 1: self._ycanvas.panDisplayToShow(xpos, zpos)
        if self.zzoom != 1: self._zcanvas.panDisplayToShow(xpos, ypos)


    def _onMouseEvent(self, ev):
        """
        Called on mouse movement and left clicks. The currently
        displayed slices and cursor positions on each of the
        canvases follow mouse clicks and drags.
        """

        if not ev.LeftIsDown():       return
        if len(self._imageList) == 0: return

        mx, my  = ev.GetPositionTuple()
        source  = ev.GetEventObject()
        w, h    = source.GetClientSize()

        my = h - my

        xpos, ypos = source.canvasToWorld(mx, my)
        zpos       = source.pos.z

        log.debug('Mouse click on canvas {}: ({}, {} -> {}, {})'.format(
            source.name, mx, my, xpos, ypos))

        if   source == self._xcanvas: self.setPosition(zpos, xpos, ypos)
        elif source == self._ycanvas: self.setPosition(xpos, zpos, ypos)
        elif source == self._zcanvas: self.setPosition(xpos, ypos, zpos)

        if self.posSync:
            if   source == self._xcanvas:
                self._displayCtx.location.yz = [xpos, ypos]
            elif source == self._ycanvas:
                self._displayCtx.location.xz = [xpos, ypos]
            elif source == self._zcanvas:
                self._displayCtx.location.xy = [xpos, ypos]
 
            
class OrthoFrame(wx.Frame):
    """
    Convenience class for displaying an OrthoPanel in a standalone window.
    """

    def __init__(self, parent, imageList, displayCtx, title=None):
        
        wx.Frame.__init__(self, parent, title=title)
        self.panel = OrthoPanel(self, imageList, displayCtx)
        self.Layout()


class OrthoDialog(wx.Dialog):
    """
    Convenience class for displaying an OrthoPanel in a (possibly modal)
    dialog window.
    """

    def __init__(self, parent, imageList, displayCtx, title=None, style=None):

        if style is None: style =  wx.DEFAULT_DIALOG_STYLE
        else:             style |= wx.DEFAULT_DIALOG_STYLE
        
        wx.Dialog.__init__(self, parent, title=title, style=style)
        self.panel = OrthoPanel(self, imageList, displayCtx)
        self.Layout()
