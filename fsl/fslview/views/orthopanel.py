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

import copy

import wx
import props

import fsl.data.image                 as fslimage
import fsl.utils.layout               as fsllayout
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

    
    layout = props.Choice(
        ['horizontal', 'vertical', 'grid'],
        ['Horizontal', 'Vertical', 'Grid'])
    """How should we lay out each of the three canvases?"""

    

    xzoom = copy.copy(slicecanvas.WXGLSliceCanvas.zoom)
    """Controls zoom on the X canvas."""

    
    yzoom = copy.copy(slicecanvas.WXGLSliceCanvas.zoom)
    """Controls zoom on the Y canvas."""

    
    zzoom = copy.copy(slicecanvas.WXGLSliceCanvas.zoom)
    """Controls zoom on the Z canvas.

    Note that the :class:`OrthoPanel` class also inherits a ``zoom`` property
    from the :class:`~fsl.fslview.views.canvaspanel.CanvasPanel` class - this
    'global' property can be used to adjust all canvas zoom levels
    simultaneously.
    """

    
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
    """Labels for each of the user-editable :class:`OrthoPanel` properties."""


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

    def _init(self):

        canvasPanel = self.getCanvasPanel()
        imageList   = self._imageList
        displayCtx  = self._displayCtx

        # The canvases themselves - each one displays a
        # slice along each of the three world axes
        self._xcanvas = slicecanvas.WXGLSliceCanvas(canvasPanel,
                                                    imageList,
                                                    displayCtx,
                                                    zax=0)
        self._ycanvas = slicecanvas.WXGLSliceCanvas(canvasPanel,
                                                    imageList,
                                                    displayCtx,
                                                    zax=1)
        self._zcanvas = slicecanvas.WXGLSliceCanvas(canvasPanel,
                                                    imageList,
                                                    displayCtx,
                                                    zax=2)

        # Labels to show anatomical orientation,
        # stored in a dict for each canvas
        self._xLabels = {}
        self._yLabels = {}
        self._zLabels = {}
        for side in ('left', 'right', 'top', 'bottom'):
            self._xLabels[side] = wx.StaticText(canvasPanel)
            self._yLabels[side] = wx.StaticText(canvasPanel)
            self._zLabels[side] = wx.StaticText(canvasPanel)

        canvasPanel.SetBackgroundColour('black')

        for side in ('left', 'right', 'top', 'bottom'):
            self._xLabels[side].SetBackgroundColour('black')
            self._yLabels[side].SetBackgroundColour('black')
            self._zLabels[side].SetBackgroundColour('black')
            self._xLabels[side].SetForegroundColour('white')
            self._yLabels[side].SetForegroundColour('white')
            self._zLabels[side].SetForegroundColour('white') 

        self.bindProps('showCursor', self._xcanvas)
        self.bindProps('showCursor', self._ycanvas)
        self.bindProps('showCursor', self._zcanvas)

        # Callbacks for ortho panel layout options
        self.addListener('layout',     self._name, self._refreshLayout)
        self.addListener('showLabels', self._name, self._refreshLabels)

        # Individual zoom control for each canvas
        self.bindProps('xzoom', self._xcanvas, 'zoom')
        self.bindProps('yzoom', self._ycanvas, 'zoom')
        self.bindProps('zzoom', self._zcanvas, 'zoom')

        # And a global zoom which controls all canvases at once
        def onZoom(*a):
            self.xzoom = self.zoom
            self.yzoom = self.zoom
            self.zzoom = self.zoom

        minZoom = self.getConstraint('xzoom', 'minval')
        maxZoom = self.getConstraint('xzoom', 'maxval')

        self.setConstraint('zoom', 'minval', minZoom)
        self.setConstraint('zoom', 'maxval', maxZoom)

        self.addListener('zoom', self._name, onZoom)

        # Callbacks for image list/selected image changes
        self._imageList.addListener( 'images',
                                     self._name,
                                     self._imageListChanged)
        self._displayCtx.addListener('bounds',
                                     self._name,
                                     self._refreshLayout) 
        self._displayCtx.addListener('selectedImage',
                                     self._name,
                                     self._imageListChanged)

        # Callback for the display context location - when it
        # changes, update the displayed canvas locations
        def move(*a):
            self.setPosition(*self._displayCtx.location)

        self._displayCtx.addListener('location', self._name, move) 

        # Callbacks for toggling x/y/z canvas display
        self.addListener('showXCanvas',
                         self._name,
                         lambda *a: self._toggleCanvas('x'))
        self.addListener('showYCanvas',
                         self._name,
                         lambda *a: self._toggleCanvas('y'))
        self.addListener('showZCanvas',
                         self._name,
                         lambda *a: self._toggleCanvas('z'))

        # Do some cleaning up if/when this panel is destroyed
        self.Bind(wx.EVT_WINDOW_DESTROY, self._onDestroy)

        # And finally, call the _resize method to
        # refresh things when this panel is resized
        self.Bind(wx.EVT_SIZE, self._onResize)

        # Initialise the panel
        self._refreshLayout()
        self._imageListChanged()
        self._refreshLabels()
        self.setPosition(*self._displayCtx.location) 
        

    def _toggleCanvas(self, canvas):
        """Called when any of  show*Canvas properties are changed.
        
        Shows/hides the specified canvas ('x', 'y', or 'z') - this callback
        is configured in __init__ above.
        """

        if canvas == 'x':
            canvas = self._xcanvas
            show   = self.showXCanvas
            labels = self._xLabels
        elif canvas == 'y':
            canvas = self._ycanvas
            show   = self.showYCanvas
            labels = self._yLabels
        elif canvas == 'z':
            canvas = self._zcanvas
            show   = self.showZCanvas
            labels = self._zLabels

        self._canvasSizer.Show(canvas, show)
        for label in labels.values():
            if (not show) or (show and self.showLabels):
                self._canvasSizer.Show(label, show)

        if self.layout == 'grid':
            self._refreshLayout()

        self.PostSizeEvent()


    def _imageListChanged(self, *a):
        """Called when the image list or selected image is changed.

        Adds a listener to the currently selected image, to listen
        for changes on its affine transformation matrix.
        """
        
        for i, img in enumerate(self._imageList):

            display = self._displayCtx.getDisplayProperties(img)

            # Update anatomy labels when the image
            # transformation matrix changes
            if i == self._displayCtx.selectedImage:
                display.addListener('transform',
                                    self._name,
                                    self._refreshLabels,
                                    overwrite=True)
            else:
                display.removeListener('transform', self._name)
                
        # anatomical orientation may have changed with an image change
        self._refreshLabels()


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
        self._displayCtx.removeListener('bounds',        self._name)
        self._displayCtx.removeListener('selectedImage', self._name)
        self._imageList .removeListener('images',        self._name)

        # The _imageListChanged method adds
        # listeners to individual images,
        # so we have to remove them too
        for img in self._imageList:
            display = self._displayCtx.getDisplayProperties(img)
            display.removeListener('transform', self._name)
        
            
    def _onResize(self, ev):
        """
        Called whenever the panel is resized. Makes sure that the canvases
        are laid out nicely.
        """
        ev.Skip()
        self._calcCanvasSizes()


    def _refreshLabels(self, *a):
        """Shows/hides labels depicting anatomical orientation on each canvas.
        """

        allLabels = self._xLabels.values() + \
                    self._yLabels.values() + \
                    self._zLabels.values()

        # Are we showing or hiding the labels?
        if   len(self._imageList) == 0: show = False
        elif self.showLabels:           show = True
        else:                           show = False

        for lbl in allLabels:
            self._canvasSizer.Show(lbl, show)

        # If we're hiding the labels, do no more
        if not show:
            self.PostSizeEvent()
            return

        # Default colour is white - if the orientation labels
        # cannot be determined, the foreground colour will be
        # changed to red
        colour = 'white'

        image   = self._displayCtx.getSelectedImage()
        display = self._displayCtx.getDisplayProperties(image)

        # The image is being displayed as it is stored on
        # disk - the image.getOrientation method calculates
        # and returns labels for each voxelwise axis.
        if display.transform in ('pixdim', 'id'):
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

        self._xLabels['left']  .SetLabel(ylo)
        self._xLabels['right'] .SetLabel(yhi)
        self._xLabels['top']   .SetLabel(zlo)
        self._xLabels['bottom'].SetLabel(zhi)
        self._yLabels['left']  .SetLabel(xlo)
        self._yLabels['right'] .SetLabel(xhi)
        self._yLabels['top']   .SetLabel(zlo)
        self._yLabels['bottom'].SetLabel(zhi)
        self._zLabels['left']  .SetLabel(xlo)
        self._zLabels['right'] .SetLabel(xhi)
        self._zLabels['top']   .SetLabel(ylo)
        self._zLabels['bottom'].SetLabel(yhi)

        self.PostSizeEvent()


    def _calcCanvasSizes(self, *a):
        """Fixes the size for each displayed canvas (by setting their minimum
        and maximum sizes), so that they are scaled proportionally to each
        other.
        """

        layout = self.layout

        # Lay out this panel, so the canvas
        # panel size is up to date 
        self.Layout()

        width, height = self.getCanvasPanel().GetClientSize().Get()

        if width == 0 or height == 0: return
        if len(self._imageList) == 0: return

        show     = [self.showXCanvas, self.showYCanvas, self.showZCanvas]
        canvases = [self._xcanvas,    self._ycanvas,    self._zcanvas]
        labels   = [self._xLabels,    self._yLabels,    self._zLabels]

        canvases, labels, _ = zip(*filter(lambda (c, l, s): s,
                                          zip(canvases, labels, show)))

        canvases = list(canvases)
        labels   = list(labels)

        # Grid layout with 2 or less canvases displayed
        # is identical to horizontal layout
        if layout == 'grid' and len(canvases) <= 2:
            layout = 'horizontal'

        # Calculate the width/height (in pixels) which
        # is available to lay out all of the canvases
        # (taking into account anatomical orientation
        # labels).
        if layout == 'horizontal':
            maxh = 0
            sumw = 0
            for l in labels:

                if self.showLabels:
                    lw, lh = l['left']  .GetClientSize().Get()
                    rw, rh = l['right'] .GetClientSize().Get()
                    tw, th = l['top']   .GetClientSize().Get()
                    bw, bh = l['bottom'].GetClientSize().Get()
                else:
                    lw = rw = th = bh = 0

                sumw = sumw + lw + rw
                if th > maxh: maxh = th
                if bh > maxh: maxh = bh
            width  = width  -     sumw
            height = height - 2 * maxh
            
        elif layout == 'vertical':
            maxw = 0
            sumh = 0
            for l in labels:
                if self.showLabels:
                    lw, lh = l['left']  .GetClientSize().Get()
                    rw, rh = l['right'] .GetClientSize().Get()
                    tw, th = l['top']   .GetClientSize().Get()
                    bw, bh = l['bottom'].GetClientSize().Get()
                else:
                    lw = rw = th = bh = 0
                    
                sumh = sumh + th + bh
                if lw > maxw: maxw = lw
                if rw > maxw: maxw = rw
                
            width  = width  - 2 * maxw
            height = height -     sumh
            
        else:
            canvases = [self._ycanvas, self._xcanvas, self._zcanvas]

            if self.showLabels:
                xlw = self._xLabels['left']  .GetClientSize().GetWidth()
                xrw = self._xLabels['right'] .GetClientSize().GetWidth()
                ylw = self._yLabels['left']  .GetClientSize().GetWidth()
                yrw = self._yLabels['right'] .GetClientSize().GetWidth()
                zlw = self._zLabels['left']  .GetClientSize().GetWidth()
                zrw = self._zLabels['right'] .GetClientSize().GetWidth()             
                xth = self._xLabels['top']   .GetClientSize().GetHeight()
                xbh = self._xLabels['bottom'].GetClientSize().GetHeight()
                yth = self._yLabels['top']   .GetClientSize().GetHeight()
                ybh = self._yLabels['bottom'].GetClientSize().GetHeight()
                zth = self._zLabels['top']   .GetClientSize().GetHeight()
                zbh = self._zLabels['bottom'].GetClientSize().GetHeight()
            else:
                xlw = xrw = xth = xbh = 0
                ylw = yrw = yth = ybh = 0
                zlw = zrw = zth = zbh = 0

            width  = width  - max(xlw, zlw) - max(xrw, zrw) - ylw - yrw
            height = height - max(xth, yth) - max(xbh, ybh) - zth - zbh

        # Distribute the available width/height
        # to each of the displayed canvases -
        # fsl.utils.layout (a.k.a. fsllayout)
        # provides functions to do this for us
        canvasaxes = [(c.xax, c.yax) for c in canvases]
        axisLens   = [self._displayCtx.bounds.xlen,
                      self._displayCtx.bounds.ylen,
                      self._displayCtx.bounds.zlen]
        
        sizes = fsllayout.calcSizes(layout,
                                    canvasaxes,
                                    axisLens,
                                    width,
                                    height)

        for canvas, size in zip(canvases, sizes):
            canvas.SetMinSize(size)
            canvas.SetMaxSize(size)

        self.getCanvasPanel().Layout()

        
    def _refreshLayout(self, *a):
        """Called when the layout property changes, or the canvas layout needs
        to be refreshed. Updates the orthopanel layout accordingly.
        """

        layout = self.layout

        # For the grid layout if only one or two
        # canvases are being displayed, the layout
        # is equivalent to a horizontal layout
        nCanvases = 3
        nDisplayedCanvases = sum([self.showXCanvas,
                                  self.showYCanvas,
                                  self.showZCanvas])
         
        if layout == 'grid' and nDisplayedCanvases <= 2:
            layout = 'horizontal'

        # Regardless of the layout, we use a
        # FlexGridSizer with varying numbers
        # of rows/columns, depending upon the
        # layout strategy
        if   layout == 'horizontal':
            nrows = 3
            ncols = nCanvases * 3
        elif layout == 'vertical':
            nrows = nCanvases * 3
            ncols = 3
        elif layout == 'grid': 
            nrows = nCanvases * 2
            ncols = nCanvases * 2
        # if layout is something other than the above three,
        # then something's gone wrong and I'm going to crash

        self._canvasSizer = wx.FlexGridSizer(nrows, ncols)

        # The rows/columns that contain
        # canvases must also be growable
        if layout == 'horizontal':
            self._canvasSizer.AddGrowableRow(1)
            for i in range(nCanvases):
                self._canvasSizer.AddGrowableCol(i * 3 + 1)
                
        elif layout == 'vertical':
            self._canvasSizer.AddGrowableCol(1)
            for i in range(nCanvases):
                self._canvasSizer.AddGrowableRow(i * 3 + 1)
                
        elif layout == 'grid':
            self._canvasSizer.AddGrowableRow(1)
            self._canvasSizer.AddGrowableRow(4)
            self._canvasSizer.AddGrowableCol(1)
            self._canvasSizer.AddGrowableCol(4) 

        # Make a list of widgets - the canvases,
        # anatomical labels (if displayed), and
        # spacers for the empty cells
        space = (1, 1)
        xlbls = self._xLabels
        ylbls = self._yLabels
        zlbls = self._zLabels
        
        if layout == 'horizontal':
            widgets = [space,         xlbls['top'],    space,
                       space,         ylbls['top'],    space,
                       space,         zlbls['top'],    space,
                       xlbls['left'], self._xcanvas,   xlbls['right'],
                       ylbls['left'], self._ycanvas,   ylbls['right'],
                       zlbls['left'], self._zcanvas,   zlbls['right'],
                       space,         xlbls['bottom'], space,
                       space,         ylbls['bottom'], space,
                       space,         zlbls['bottom'], space] 
                
        elif layout == 'vertical':
            widgets = [space,         xlbls['top'],    space,
                       xlbls['left'], self._xcanvas,   xlbls['right'],
                       space,         xlbls['bottom'], space,
                       space,         ylbls['top'],    space,
                       ylbls['left'], self._ycanvas,   ylbls['right'],
                       space,         ylbls['bottom'], space,
                       space,         zlbls['top'],    space,
                       zlbls['left'], self._zcanvas,   zlbls['right'],
                       space,         zlbls['bottom'], space]

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
        elif layout == 'grid':
            widgets = [space,         ylbls['top'],    space,
                       space,         xlbls['top'],    space,
                       ylbls['left'], self._ycanvas,   ylbls['right'],
                       xlbls['left'], self._xcanvas,   xlbls['right'],
                       space,         ylbls['bottom'], space,
                       space,         xlbls['bottom'], space,
                       space,         zlbls['top'],    space,
                       space,         space,           space,
                       zlbls['left'], self._zcanvas,   zlbls['right'],
                       space,         space,           space,
                       space,         zlbls['bottom'], space,
                       space,         space,           space]

        # Add all those widgets to the grid sizer
        flag = wx.ALIGN_CENTRE_HORIZONTAL | wx.ALIGN_CENTRE_VERTICAL
        
        for w in widgets:

            if w in [self._xcanvas, self._ycanvas, self._zcanvas]:
                self._canvasSizer.Add(w, flag=flag)
            else:
                self._canvasSizer.Add(w, flag=flag)
                                          
        self.getCanvasPanel().SetSizer(self._canvasSizer)

        # Calculate/ adjust the appropriate sizes
        # for each canvas, such that they are scaled
        # appropriately relative to each other, and
        # the displayed world space aspect ratio is
        # maintained
        self._calcCanvasSizes()

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

        if self.xzoom != 100.0: self._xcanvas.panDisplayToShow(ypos, zpos)
        if self.yzoom != 100.0: self._ycanvas.panDisplayToShow(xpos, zpos)
        if self.zzoom != 100.0: self._zcanvas.panDisplayToShow(xpos, ypos)


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
