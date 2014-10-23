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

import fsl.data.image                 as fslimage

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
        'showLabels'        : 'Show orientation labels',
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

        # Attach each canvas as an attribute of its parent -
        # see the _configureGridLayout/_configureFlatLayout
        # methods
        self._xCanvasPanel._canvas = self._xcanvas
        self._yCanvasPanel._canvas = self._ycanvas
        self._zCanvasPanel._canvas = self._zcanvas
        
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

        self                 .SetBackgroundColour('black')
        self.getCanvasPanel().SetBackgroundColour('black')
        self._xCanvasPanel   .SetBackgroundColour('black')
        self._yCanvasPanel   .SetBackgroundColour('black')
        self._zCanvasPanel   .SetBackgroundColour('black')
        
        self._xLeftLabel  .SetBackgroundColour('black')
        self._xRightLabel .SetBackgroundColour('black')
        self._xTopLabel   .SetBackgroundColour('black')
        self._xBottomLabel.SetBackgroundColour('black')
        self._yLeftLabel  .SetBackgroundColour('black')
        self._yRightLabel .SetBackgroundColour('black')
        self._yTopLabel   .SetBackgroundColour('black')
        self._yBottomLabel.SetBackgroundColour('black')
        self._zLeftLabel  .SetBackgroundColour('black')
        self._zRightLabel .SetBackgroundColour('black')
        self._zTopLabel   .SetBackgroundColour('black')
        self._zBottomLabel.SetBackgroundColour('black') 
        
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

        # Callbacks for ortho panel layout options
        self.addListener('layout',            self._name, self._layoutChanged)
        self.addListener('showColourBar',     self._name, self._layoutChanged)
        self.addListener('colourBarLocation', self._name, self._layoutChanged)
        self.addListener('showLabels',        self._name, self._refreshLabels)

        # Callbacks for image list/selected image changes
        self._imageList.addListener( 'images',
                                     self._name,
                                     self._imageListChanged)
        self._displayCtx.addListener('selectedImage',
                                     self._name,
                                     self._imageListChanged)

        self._imageListChanged()
        self._layoutChanged()
        self._refreshLabels()

        # Callbacks for mouse events on the three xcanvases
        self._xcanvas.Bind(wx.EVT_LEFT_DOWN, self._onMouseEvent)
        self._ycanvas.Bind(wx.EVT_LEFT_DOWN, self._onMouseEvent)
        self._zcanvas.Bind(wx.EVT_LEFT_DOWN, self._onMouseEvent)
        self._xcanvas.Bind(wx.EVT_MOTION,    self._onMouseEvent)
        self._ycanvas.Bind(wx.EVT_MOTION,    self._onMouseEvent)
        self._zcanvas.Bind(wx.EVT_MOTION,    self._onMouseEvent)

        # Callback for the display context location - when it
        # changes, update the displayed canvas locations
        def move(*a):
            if self.posSync:
                self.setPosition(*self._displayCtx.location)

        self.setPosition(*self._displayCtx.location)
        self._displayCtx.addListener('location', self._name, move) 

        # Callbacks for toggling x/y/z canvas display
        self.addListener('showXCanvas', self._name, self._layoutChanged)
        self.addListener('showYCanvas', self._name, self._layoutChanged)
        self.addListener('showZCanvas', self._name, self._layoutChanged)

        # Do some cleaning up if/when this panel is destroyed
        self.Bind(wx.EVT_WINDOW_DESTROY, self._onDestroy)

        # And finally, call the _resize method to
        # re-layout things when this panel is resized
        self.Bind(wx.EVT_SIZE, self._resize)


    def _imageListChanged(self, *a):
        """Called when the image list or selected image is changed.

        Adds a listener to the currently selected image, to listen
        for changes on its affine transformation matrix.
        """
        
        self._refreshLabels()

        if len(self._imageList) == 0: return

        for i, img in enumerate(self._imageList):

            img.removeListener('transform', self._name)

            # Update anatomy labels when the image
            # transformation matrix changes
            if i == self._displayCtx.selectedImage:
                img.addListener('transform', self._name, self._refreshLabels)


    def _onDestroy(self, ev):
        """Called when this panel is destroyed. 
        
        The display context and image list will probably live longer than
        this OrthoPanel. So when this panel is destroyed, all those
        registered listeners are removed.
        """
        ev.Skip()

        # Do nothing if the destroyed window is not
        # this panel (i.e. it is a child of this panel)
        if ev.GetEventObject() != self: return

        self._displayCtx.removeListener('location',      self._name)
        self._displayCtx.removeListener('selectedImage', self._name)
        self._imageList .removeListener('images',        self._name)

        # The _imageListChanged method adds
        # listeners to individual images,
        # so we have to remove them too
        for img in self._imageList:
            img.removeListener('transform', self._name)
        
            
    def _resize(self, ev):
        """
        Called whenever the panel is resized. Makes sure that the canvases
        are laid out nicely.
        """
        ev.Skip()
        
        # Re-layout the canvases asynchronously as,
        # in some cases, resizes to this panel
        # aren't immediately applied to child panels
        wx.CallAfter(self._layoutChanged)


    def _refreshLabels(self, *a):
        """Shows/hides labels depicting anatomical orientation on each canvas.
        """

        allLabels =  [self._xLeftLabel, self._xRightLabel,
                      self._xTopLabel,  self._xBottomLabel,
                      self._yLeftLabel, self._yRightLabel,
                      self._yTopLabel,  self._yBottomLabel,
                      self._zLeftLabel, self._zRightLabel,
                      self._zTopLabel,  self._zBottomLabel]


        # Are we showing or hiding the labels?
        if self.showLabels: show = True
        else:               show = False

        for lbl in allLabels:
            lbl.Show(show)

        # If we're hiding the labels, do no more
        if not show:
            self._layoutChanged()
            return

        # Default colour is white - if the orientation labels
        # cannot be determined, the background colour will be
        # changed to red
        colour = 'white'

        if len(self._imageList) > 0:
            image = self._imageList[self._displayCtx.selectedImage]

            # The image is being displayed as it is stored on
            # disk - the image.getOrientation method calculates
            # and returns labels for each voxelwise axis.
            if image.transform in ('pixdim', 'id'):
                xorient = image.getVoxelOrientation(0)
                yorient = image.getVoxelOrientation(1)
                zorient = image.getVoxelOrientation(2)

            # The image is being displayed in 'real world' space -
            # the definition of this space may be present in the
            # image meta data
            else:
                xorient = image.getWorldOrientation(0)
                yorient = image.getWorldOrientation(1)
                zorient = image.getWorldOrientation(2)

                
        if fslimage.ORIENT_UNKNOWN in (xorient, yorient, zorient):
            colour = 'red'
 
        # Imported here to avoid circular import issues
        import fsl.fslview.strings as strings 

        xlo = strings.imageAxisLowShortLabels[ xorient]
        ylo = strings.imageAxisLowShortLabels[ yorient]
        zlo = strings.imageAxisLowShortLabels[ zorient]
        xhi = strings.imageAxisHighShortLabels[xorient]
        yhi = strings.imageAxisHighShortLabels[yorient]
        zhi = strings.imageAxisHighShortLabels[zorient]

        for lbl in allLabels:
            lbl.SetForegroundColour(colour)

        self._xLeftLabel  .SetLabel(ylo)
        self._xRightLabel .SetLabel(yhi)
        self._xBottomLabel.SetLabel(zlo)
        self._xTopLabel   .SetLabel(zhi)
        self._yLeftLabel  .SetLabel(xlo)
        self._yRightLabel .SetLabel(xhi)
        self._yBottomLabel.SetLabel(zlo)
        self._yTopLabel   .SetLabel(zhi)
        self._zLeftLabel  .SetLabel(xlo)
        self._zRightLabel .SetLabel(xhi)
        self._zBottomLabel.SetLabel(ylo)
        self._zTopLabel   .SetLabel(yhi)

        self._layoutChanged()

        
    def _configureGridLayout(self, width, height, canvases):
        """
        If the 'Grid' layout has been selected, we have to manually specify
        sizes for each canvas, as the wx.WrapSizer doesn't know how big
        they should be. This is not a problem for wx.BoxSizers, as they
        just fill the available space, and give each canvas an equal share.
        """

        if len(canvases) <= 2:
            self._configureFlatLayout(width, height, canvases, False)
            return

        bounds = self._imageList.bounds

        canvasWidths  = [bounds.getLen(c._canvas.xax) for c in canvases]
        canvasHeights = [bounds.getLen(c._canvas.yax) for c in canvases]
        ttlWidth      = float(canvasWidths[ 0] + canvasWidths[ 1])
        ttlHeight     = float(canvasHeights[0] + canvasHeights[2])

        width, height = self._adjustPixelSize(ttlWidth,
                                              ttlHeight,
                                              width,
                                              height)

        for i, canvas in enumerate(canvases):

            cw = width  * (canvasWidths[ i] / ttlWidth)
            ch = height * (canvasHeights[i] / ttlHeight) 

            cw, ch = self._adjustPixelSize(canvasWidths[ i],
                                           canvasHeights[i],
                                           cw,
                                           ch)
            canvas.SetMinSize((cw, ch))
            canvas.SetMaxSize((cw, ch))

            
    def _configureFlatLayout(self, width, height, canvases, vert=True):
        """Calculates sizes for each displayed canvas such that the aspect
        ratio is maintained across them when laid out vertically
        (``vert=True``) or horizontally (``vert=False``).
        """
        bounds = self._imageList.bounds

        # Get the canvas dimensions in world space
        canvasWidths  = [bounds.getLen(c._canvas.xax) for c in canvases]
        canvasHeights = [bounds.getLen(c._canvas.yax) for c in canvases]

        maxWidth  = float(max(canvasWidths))
        maxHeight = float(max(canvasHeights))
        ttlWidth  = float(sum(canvasWidths))
        ttlHeight = float(sum(canvasHeights))

        for i, canvas in enumerate(canvases):

            # Give each canvas a size, along the major
            # axis, so that its length is proportional
            # to the other canvases
            if vert: cw = width
            else:    cw = width  * (canvasWidths[ i] / ttlWidth)
 
            if vert: ch = height * (canvasHeights[i] / ttlHeight)
            else:    ch = height

            # Scale the canvas along the
            # minor axis in the same manner
            if vert: cw = cw * canvasWidths[ i] / maxWidth
            else:    ch = ch * canvasHeights[i] / maxHeight

            cw, ch = self._adjustPixelSize(canvasWidths[ i],
                                           canvasHeights[i],
                                           cw,
                                           ch)

            canvas.SetMinSize((cw, ch))
            canvas.SetMaxSize((cw, ch))

        
    def _adjustPixelSize(self, wldWidth, wldHeight, pixWidth, pixHeight):
        """Adjusts the pixel width/height for the given canvas such that
        the world space aspect ratio is maintained.
        """        

        pixRatio = float(pixWidth) / pixHeight
        wldRatio = float(wldWidth) / wldHeight

        if   pixRatio > wldRatio:
            pixWidth  = wldWidth  * (pixHeight / wldHeight)
                
        elif pixRatio < wldRatio:
            pixHeight = wldHeight * (pixWidth  / wldWidth)

        return pixWidth, pixHeight

        
    def _layoutChanged(self, *a):
        """Called when the layout property changes, or the canvas layout needs
        to be refreshed. Updates the orthopanel layout accordingly.
        """

        layout        = self.layout.lower()
        width, height = self.getCanvasPanel().GetClientSize().Get()

        if width == 0 or height == 0:
            return

        # The canvases are laid out in a different order
        # for orthographic, or 'grid' layout.  Assuming
        # that world axis X is left<->right, Y is
        # posterior<->anterior, and Z is inferior<->superior,
        # in order to achieve first angle orthographic
        # layout, we're laying out the canvases in the
        # following manner (the letter denotes the depth
        # axis for the respective canvas):
        #
        #    Y  X
        #    Z  -
        #
        # TODO This assumes RAS orientation (which should be 
        # a safe assumption to make when displaying in NIFTI/world
        # coordinates). But we could alternately, automaticaly
        # generate the canvas order from anatomical orientation
        # labels.
        if layout == 'grid':
            canvases = [self._yCanvasPanel,
                        self._xCanvasPanel,
                        self._zCanvasPanel]
            show     = [self.showYCanvas,
                        self.showXCanvas,
                        self.showZCanvas] 
                        

        # For vertical/horizontal
        # layouts, we just go with XYZ
        else:
            canvases = [self._xCanvasPanel,
                        self._yCanvasPanel,
                        self._zCanvasPanel]
            show     = [self.showXCanvas,
                        self.showYCanvas,
                        self.showZCanvas] 

        # Pick out the canvases for which
        # the 'show*Canvas' property is true 

        if any(show): 
            canvases = list(
                zip(*filter(lambda (c, s): s, zip(canvases, show)))[0])
        else:
            canvases = []

        self._xCanvasPanel.Show(self.showXCanvas)
        self._yCanvasPanel.Show(self.showYCanvas)
        self._zCanvasPanel.Show(self.showZCanvas)

        if len(canvases) == 0:
            return

        # Regardless of the layout, we use a
        # FlexGridSizer with varying numbers
        # of rows/columns, depending upon the
        # layout strategy, and the number of
        # visible canvases
        if   layout == 'horizontal':
            nrows = 1
            ncols = len(canvases)
        elif layout == 'vertical':
            nrows = len(canvases)
            ncols = 1
        elif layout == 'grid':
            if len(canvases) <= 2:
                nrows = 1
                ncols = len(canvases)
            else:      
                nrows = 2
                ncols = 2

        # Two dummy rows/cols on each side of the
        # canvas cells are filled with empty space,
        # to ensure that the canvases are centered
        # in the available space
        self._canvasSizer = wx.FlexGridSizer(nrows + 2, ncols + 2)
        self._canvasSizer.AddGrowableRow(0)
        self._canvasSizer.AddGrowableRow(nrows + 1)
        self._canvasSizer.AddGrowableCol(0)
        self._canvasSizer.AddGrowableCol(ncols + 1) 

        # Make a list of widgets - spacers and canvases
        space   = (1, 1)
        widgets = [space] * (ncols + 2)
        
        if layout == 'vertical':
            for c in canvases:
                widgets += [space, c, space]
                
        elif layout == 'horizontal':
            widgets += [space] + canvases + [space]
            
        else:
            if len(canvases) <= 2:
                widgets += [space] + canvases + [space]
            else:
                widgets += [space] + canvases[:2]  + [space]
                widgets += [space] + canvases[ 2:] + [space, space]
                
        widgets += [space] * (ncols + 2)

        # Add all those widgets to the grid sizer
        for i, w in enumerate(widgets):
            self._canvasSizer.Add(w, flag=wx.ALIGN_CENTRE_HORIZONTAL |
                                          wx.ALIGN_CENTRE_VERTICAL)

        self.getCanvasPanel().SetSizer(self._canvasSizer)

        # Calculate/ adjust the appropriate sizes
        # for each canvas, such that they are scaled
        # appropriately relative to each other, and
        # the displayed world space aspect ratio is
        # maintained
        if layout == 'grid':
            self._configureGridLayout(width, height, canvases)
        elif layout == 'horizontal':
            self._configureFlatLayout(width, height, canvases, False)
        elif layout == 'vertical':
            self._configureFlatLayout(width, height, canvases, True)

        self.Layout()
        self.getCanvasPanel().Layout()
        self.Refresh()


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
