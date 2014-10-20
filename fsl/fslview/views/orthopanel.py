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

import fsl.fslview.gl                 as fslgl
import fsl.fslview.gl.wxglslicecanvas as slicecanvas
import canvaspanel

class OrthoPanel(canvaspanel.CanvasPanel):

    
    showXCanvas = props.Boolean(default=True)
    """Toggles display of the X canvas."""

    
    showYCanvas = props.Boolean(default=True)
    """Toggles display of the Y canvas."""

    
    showZCanvas = props.Boolean(default=True)
    """Toggles display of the Z canvas."""


    invertX_X   = props.Boolean(default=False)
    invertX_Y   = props.Boolean(default=False)
    invertY_X   = props.Boolean(default=False)
    invertY_Y   = props.Boolean(default=False)
    invertZ_X   = props.Boolean(default=False)
    invertZ_Y   = props.Boolean(default=False)

    showLabels = props.Boolean(default=True)
    """If ``True``, labels showing anatomical orientation are displayed on
    each of the canvases.
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


    _view = props.HGroup((
        props.VGroup(('layout',
                      'posSync',
                      'showCursor',
                      'showLabels', 
                      'showXCanvas',
                      'showYCanvas',
                      'showZCanvas',
                      'showColourBar',
                      props.HGroup(('invertX_X', 'invertX_Y')),
                      props.HGroup(('invertY_X', 'invertY_Y')),
                      props.HGroup(('invertZ_X', 'invertZ_Y')),
                      props.Widget('colourBarLocation',
                                   visibleWhen=lambda i: i.showColourBar),
                      props.Widget('colourBarLabelSide',
                                   visibleWhen=lambda i: i.showColourBar))),
        props.VGroup(('xzoom', 'yzoom', 'zzoom'))
    ))

    _labels = dict({
        'showXCanvas'       : 'Show X canvas',
        'showYCanvas'       : 'Show Y canvas',
        'showZCanvas'       : 'Show Z canvas',
        'xzoom'             : 'X zoom',
        'yzoom'             : 'Y zoom',
        'zzoom'             : 'Z zoom',
        'layout'            : 'Layout'
    }.items() + canvaspanel.CanvasPanel._labels.items())


    def __init__(self,
                 parent,
                 imageList,
                 displayCtx):
        """
        Creates three SliceCanvas objects, each displaying the images
        in the given image list along a different axis. 
        """

        canvaspanel.CanvasPanel.__init__(self,
                                         parent,
                                         imageList,
                                         displayCtx)

        self.SetBackgroundColour('black')

        # Container panels for each canvas
        self._xCanvasPanel = wx.Panel(self.getCanvasPanel())
        self._yCanvasPanel = wx.Panel(self.getCanvasPanel())
        self._zCanvasPanel = wx.Panel(self.getCanvasPanel())

        # The canvases themselves - each one displays a
        # slice along each of the three world axes
        self._xcanvas = slicecanvas.WXGLSliceCanvas(self._xCanvasPanel,
                                                    imageList, zax=0)
        self._ycanvas = slicecanvas.WXGLSliceCanvas(self._yCanvasPanel,
                                                    imageList, zax=1)
        self._zcanvas = slicecanvas.WXGLSliceCanvas(self._zCanvasPanel,
                                                    imageList, zax=2)

        
        # Labels to show anatomical orientation
        self._xLeftLabel   = wx.StaticText(self._xCanvasPanel)
        self._xRightLabel  = wx.StaticText(self._xCanvasPanel)
        self._xTopLabel    = wx.StaticText(self._xCanvasPanel)
        self._xBottomLabel = wx.StaticText(self._xCanvasPanel)
        self._yLeftLabel   = wx.StaticText(self._yCanvasPanel)
        self._yRightLabel  = wx.StaticText(self._yCanvasPanel)
        self._yTopLabel    = wx.StaticText(self._yCanvasPanel)
        self._yBottomLabel = wx.StaticText(self._yCanvasPanel)
        self._zLeftLabel   = wx.StaticText(self._zCanvasPanel)
        self._zRightLabel  = wx.StaticText(self._zCanvasPanel)
        self._zTopLabel    = wx.StaticText(self._zCanvasPanel)
        self._zBottomLabel = wx.StaticText(self._zCanvasPanel)

        self._xLeftLabel  .SetForegroundColour('white')
        self._xRightLabel .SetForegroundColour('white')
        self._xTopLabel   .SetForegroundColour('white')
        self._xBottomLabel.SetForegroundColour('white')
        self._yLeftLabel  .SetForegroundColour('white')
        self._yRightLabel .SetForegroundColour('white')
        self._yTopLabel   .SetForegroundColour('white')
        self._yBottomLabel.SetForegroundColour('white')
        self._zLeftLabel  .SetForegroundColour('white')
        self._zRightLabel .SetForegroundColour('white')
        self._zTopLabel   .SetForegroundColour('white')
        self._zBottomLabel.SetForegroundColour('white') 

        # Each canvas and its labels are laid out in
        # a 9*9 grid, with the canvas in the middle,
        # and taking up most of the space
        self._xCanvasSizer = wx.FlexGridSizer(3, 3, 0, 0)
        self._yCanvasSizer = wx.FlexGridSizer(3, 3, 0, 0)
        self._zCanvasSizer = wx.FlexGridSizer(3, 3, 0, 0)

        self._xCanvasPanel.SetSizer(self._xCanvasSizer)
        self._yCanvasPanel.SetSizer(self._yCanvasSizer)
        self._zCanvasPanel.SetSizer(self._zCanvasSizer)
        
        self._xCanvasSizer.AddGrowableRow(1, 1)
        self._xCanvasSizer.AddGrowableCol(1, 1)
        self._yCanvasSizer.AddGrowableRow(1, 1)
        self._yCanvasSizer.AddGrowableCol(1, 1)
        self._zCanvasSizer.AddGrowableRow(1, 1)
        self._zCanvasSizer.AddGrowableCol(1, 1)

        labelFlag = wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_CENTRE_HORIZONTAL

        self._xCanvasSizer.AddStretchSpacer()
        self._xCanvasSizer.Add(self._xTopLabel,    flag=labelFlag)
        self._xCanvasSizer.AddStretchSpacer()
        self._xCanvasSizer.Add(self._xLeftLabel,   flag=labelFlag)
        self._xCanvasSizer.Add(self._xcanvas,      flag=wx.EXPAND)
        self._xCanvasSizer.Add(self._xRightLabel,  flag=labelFlag)
        self._xCanvasSizer.AddStretchSpacer()
        self._xCanvasSizer.Add(self._xBottomLabel, flag=labelFlag)
        self._xCanvasSizer.AddStretchSpacer()
        
        self._yCanvasSizer.AddStretchSpacer()
        self._yCanvasSizer.Add(self._yTopLabel,    flag=labelFlag)
        self._yCanvasSizer.AddStretchSpacer()
        self._yCanvasSizer.Add(self._yLeftLabel,   flag=labelFlag)
        self._yCanvasSizer.Add(self._ycanvas,      flag=wx.EXPAND)
        self._yCanvasSizer.Add(self._yRightLabel,  flag=labelFlag)
        self._yCanvasSizer.AddStretchSpacer()
        self._yCanvasSizer.Add(self._yBottomLabel, flag=labelFlag)
        self._yCanvasSizer.AddStretchSpacer()
        
        self._zCanvasSizer.AddStretchSpacer()
        self._zCanvasSizer.Add(self._zTopLabel,    flag=labelFlag)
        self._zCanvasSizer.AddStretchSpacer()
        self._zCanvasSizer.Add(self._zLeftLabel,   flag=labelFlag)
        self._zCanvasSizer.Add(self._zcanvas,      flag=wx.EXPAND)
        self._zCanvasSizer.Add(self._zRightLabel,  flag=labelFlag)
        self._zCanvasSizer.AddStretchSpacer()
        self._zCanvasSizer.Add(self._zBottomLabel, flag=labelFlag)
        self._zCanvasSizer.AddStretchSpacer() 
        
        self.bindProps('showCursor', self._xcanvas)
        self.bindProps('showCursor', self._ycanvas)
        self.bindProps('showCursor', self._zcanvas)
        self.bindProps('xzoom',      self._xcanvas, 'zoom')
        self.bindProps('yzoom',      self._ycanvas, 'zoom')
        self.bindProps('zzoom',      self._zcanvas, 'zoom')

        self.bindProps('invertX_X', self._xcanvas, 'invertX')
        self.bindProps('invertX_Y', self._xcanvas, 'invertY')
        self.bindProps('invertY_X', self._ycanvas, 'invertX')
        self.bindProps('invertY_Y', self._ycanvas, 'invertY')
        self.bindProps('invertZ_X', self._zcanvas, 'invertX')
        self.bindProps('invertZ_Y', self._zcanvas, 'invertY') 

        llName = '{}_layout'.format(self._name)
        
        self.addListener('layout',            llName, self._layoutChanged)
        self.addListener('showColourBar',     llName, self._layoutChanged)
        self.addListener('colourBarLocation', llName, self._layoutChanged)
        self.addListener('showLabels',        llName, self._toggleLabels)

        self._layoutChanged()
        self._toggleLabels()

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

        def toggle(canvas, toggle):
            self._canvasSizer.Show(canvas, toggle)
            if self.layout.lower() == 'grid':
                self._configureGridSizes() 
            self.getCanvasPanel().Layout()            

        self.addListener('showXCanvas', self._name,
                         lambda *a: toggle(self._xCanvasPanel,
                                           self.showXCanvas))
        self.addListener('showYCanvas', self._name,
                         lambda *a: toggle(self._yCanvasPanel,
                                           self.showYCanvas))
        self.addListener('showZCanvas', self._name,
                         lambda *a: toggle(self._zCanvasPanel,
                                           self.showZCanvas))

            
    def _resize(self, ev):
        """
        Called whenever the panel is resized. Makes sure that the canvases
        are laid out nicely.
        """
        
        # allow default resize event handler to run
        ev.Skip()
        self._configureGridSizes()
        self.Layout()


    def _toggleLabels(self, *a):
        """Shows/hides labels depicting anatomical orientation on each canvas.
        """
        if self.showLabels: show = True
        else:               show = False

        self._xLeftLabel  .Show(show)
        self._xRightLabel .Show(show) 
        self._xTopLabel   .Show(show)
        self._xBottomLabel.Show(show)
        self._yLeftLabel  .Show(show)
        self._yRightLabel .Show(show) 
        self._yTopLabel   .Show(show)
        self._yBottomLabel.Show(show)
        self._zLeftLabel  .Show(show)
        self._zRightLabel .Show(show) 
        self._zTopLabel   .Show(show)
        self._zBottomLabel.Show(show)

        self._xLeftLabel  .SetLabel('?')
        self._xRightLabel .SetLabel('?')
        self._xTopLabel   .SetLabel('?')
        self._xBottomLabel.SetLabel('?')
        self._yLeftLabel  .SetLabel('?')
        self._yRightLabel .SetLabel('?')
        self._yTopLabel   .SetLabel('?')
        self._yBottomLabel.SetLabel('?')
        self._zLeftLabel  .SetLabel('?')
        self._zRightLabel .SetLabel('?')
        self._zTopLabel   .SetLabel('?')
        self._zBottomLabel.SetLabel('?')

        self._xCanvasPanel.Layout()
        self._yCanvasPanel.Layout()
        self._zCanvasPanel.Layout()

        
    def _configureGridSizes(self):
        """
        If the 'Grid' layout has been selected, we have to manually specify
        sizes for each canvas, as the wx.WrapSizer doesn't know how big
        they should be. This is not a problem for wx.BoxSizers, as they
        just fill the available space, and give each canvas an equal share.
        """

        # Box sizers behave nicely. WrapSizer does not.
        if self.layout.lower() != 'grid': return
        
        width, height = self.getCanvasPanel().GetClientSize().Get()

        # Generate a list of canvases for
        # which the 'show*Canvas' property is true
        canvases = [self._xCanvasPanel, self._yCanvasPanel, self._zCanvasPanel]
        show     = [self.showXCanvas,   self.showYCanvas,   self.showZCanvas]

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

        canvases = [self._xCanvasPanel, self._yCanvasPanel, self._zCanvasPanel]

        if   layout == 'horizontal':
            self._canvasSizer = wx.BoxSizer(wx.HORIZONTAL)
        elif layout == 'vertical':
            self._canvasSizer = wx.BoxSizer(wx.VERTICAL)
        elif layout == 'grid':
            self._canvasSizer = wx.WrapSizer(wx.HORIZONTAL)
            canvases = [self._yCanvasPanel,
                        self._xCanvasPanel,
                        self._zCanvasPanel]

        for c in canvases:
            self._canvasSizer.Add(c, flag=wx.EXPAND, proportion=1)

        self.getCanvasPanel().SetSizer(self._canvasSizer)

        # for grid layout, we need to
        # manually specify canvas sizes
        if layout == 'grid':
            self._configureGridSizes()

        # the other layouts automatically
        # size the canvases for us
        else:
            self._xCanvasPanel.SetMinSize((-1, -1))
            self._yCanvasPanel.SetMinSize((-1, -1))
            self._zCanvasPanel.SetMinSize((-1, -1))

        self.Layout()
        self.getCanvasPanel().Layout()


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

        fslgl.getWXGLContext() 
        fslgl.bootstrap()
        
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

        fslgl.getWXGLContext()
        fslgl.bootstrap()
        
        self.panel = OrthoPanel(self, imageList, displayCtx)
        self.Layout()
