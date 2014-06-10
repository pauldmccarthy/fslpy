#!/usr/bin/env python
#
# lightboxcanvas.py - A wx.GLCanvas canvas which displays multiple slices
# along a single axis from a collection of 3D images.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

log = logging.getLogger(__name__)

import wx

import numpy as np

import OpenGL.GL as gl

import fsl.fslview.slicecanvas as slicecanvas
import fsl.props               as props


class LightBoxCanvas(slicecanvas.SliceCanvas):

    # Properties which control the starting and end bounds of the
    # displayed slices, and the spacing between them (in real
    # world coordinates)
    sliceSpacing = props.Real(clamped=True, minval=0.1, default=1.0)

    # This property controls the number of slices
    # to be displayed on a single row.
    ncols = props.Int(clamped=True, minval=1, maxval=15, default=5)

    # These properties control the range, in world
    # coordinates, of slices to be displayed
    zmin = props.Real(clamped=True)
    zmax = props.Real(clamped=True)

    _labels = {
        'zmin'         : 'First slice',
        'zmax'         : 'Last slice',
        'sliceSpacing' : 'Slice spacing',
        'ncols'        : 'Number of columns',
        'zax'          : 'Z axis'}

    _view = props.VGroup(('zmin',
                          'zmax',
                          'sliceSpacing',
                          'ncols',
                          'zax'))

    def __init__(self,
                 parent,
                 imageList,
                 zax=2,
                 glContext=None,
                 scrollbar=None):
        """
        Create a LightBoxCanvas object. Parameters:
        
          - parent:    Parent wx object
        
          - imageList: a fsl.data.ImageList object which contains, or will
                       contain, a list of images to be displayed.
        
          - zax:       Image axis to be used as the 'depth' axis. Can be
                       changed via the LightBoxCanvas.zax property.

          - glContext: OpenGL context object. If None, one will be created.

          - scrollbar: A wx.ScrollBar object. If not provided, all slices
                       will be drawn on the screen.
        """

        if (scrollbar is not None) and (not scrollbar.IsVertical()):
            raise RuntimeError('LightBoxCanvas only supports '
                               'a vertical scrollbar')

        slicecanvas.SliceCanvas.__init__(
            self, parent, imageList, zax, glContext)

        self._scrollbar = scrollbar
        if scrollbar is not None:

            # Trigger a redraw whenever the scrollbar is scrolled
            def onScroll(ev):

                # all slices are displayed on the screen
                # - the scrollbar is not currently needed
                if scrollbar.GetPageSize() >= scrollbar.GetRange():
                    scrollbar.SetThumbPosition(0)
                    return
                self._draw(ev)
            scrollbar.Bind(wx.EVT_SCROLL, onScroll)

        # default to showing the entire slice range
        self.zmin = imageList.bounds.zmin
        self.zmax = imageList.bounds.zmax

        # Pick a sensible default for the
        # slice spacing - the smallest pixdim
        # across all images in the list
        if len(imageList) > 0:
            self.sliceSpacing = min([i.pixdim[self.zax] for i in imageList])

        # Called when any of the slice properties change
        def sliceRangeChanged(*a):
            self._genSliceLocations()
            self._updateScrollBar()
            self.Refresh()

        sliceRangeChanged()

        self.addListener('sliceSpacing', self.name, sliceRangeChanged)
        self.addListener('ncols',        self.name, sliceRangeChanged)
        self.addListener('zmin',         self.name, sliceRangeChanged)
        self.addListener('zmax',         self.name, sliceRangeChanged)

        # The _updateScrollBar method is ultimately
        # responsible for calculating the number of
        # rows which are to be displayed on the
        # canvas. So when the canvas resizes, we
        # want this to be recalculated.
        self.Bind(wx.EVT_SIZE, lambda ev: self._updateScrollBar())


    def _zAxisChanged(self, *a):
        """
        Overrides SliceCanvas._zAxisChanged. Called when the
        SliceCanvas.zax property changes. Calls the superclass
        implementation, and then sets the slice zmin/max bounds
        to the image bounds.
        """

        slicecanvas.SliceCanvas._zAxisChanged(self, *a)
        
        self.zmin = self.imageList.bounds.getmin(self.zax)
        self.zmax = self.imageList.bounds.getmax(self.zax)


    def _updateBounds(self, *a):
        """
        Overrides SliceCanvas._updateBounds. Called when the image bounds
        change. Updates the Z axis min/max values.
        """

        slicecanvas.SliceCanvas._updateBounds(self)

        imgzmin = self.imageList.bounds.getmin(self.zax)
        imgzmax = self.imageList.bounds.getmax(self.zax)

        self.setConstraint('zmin', 'minval', imgzmin)
        self.setConstraint('zmin', 'maxval', imgzmax)
        self.setConstraint('zmax', 'minval', imgzmin)
        self.setConstraint('zmax', 'maxval', imgzmax)

        # reset zmin/zmax in case they are
        # out of range of the new image bounds
        self.zmin = imgzmin
        self.zmax = imgzmax 


    def _genSliceLocations(self):
        """
        Called when any of the slice display properties change. For every
        image in the image list, generates a list of transformation
        matrices, and a list of slice indices. The latter specifies the
        slice indices from the image to be displayed, and the former
        specifies the transformation matrix to be used to position the
        slice on the canvas.        
        """
        
        # calculate the locations, in real world coordinates,
        # of all slices to be displayed on the canvas
        sliceLocs = np.arange(
            self.zmin + self.sliceSpacing * 0.5,
            self.zmax + self.sliceSpacing,
            self.sliceSpacing)

        self._nslices = len(sliceLocs)
        self._nrows   = int(np.ceil(self._nslices / float(self.ncols)))

        log.debug('{: 5.1f} - {: 5.1f}: {} slices {} rows {} columns'.format(
            self.zmin, self.zmax, self._nslices, self._nrows, self.ncols))
        
        self._sliceIdxs  = []
        self._transforms = []

        # calculate the transformation for each
        # slice in each image, and the index of
        # each slice to be displayed
        for i, image in enumerate(self.imageList):
            
            self._transforms.append([])
            self._sliceIdxs .append([])

            for zi, zpos in enumerate(sliceLocs):

                imgZi = image.worldToVox(zpos, self.zax)
                xform = self._calculateSliceTransform(image, zi)

                self._transforms[-1].append(xform)
                self._sliceIdxs[ -1].append(imgZi)


    def _calculateSliceTransform(self, image, sliceno):
        """
        Calculates a transformation matrix for the given slice number
        (voxel index) in the given image. Each slice is displayed on
        the same canvas, but is translated to a specific row/column.
        So a copy of the voxToWorld transformation matrix of the given
        image is made, and a translation applied to it, to position 
        the slice in the correct location on the canvas.
        """

        nrows = self._nrows
        ncols = self.ncols

        xform = np.array(image.voxToWorldMat, dtype=np.float32)

        row = nrows - int(np.floor(sliceno / ncols)) - 1
        col = int(np.floor(sliceno % ncols))

        xlen = self.displayBounds.xlen
        ylen = self.displayBounds.ylen

        translate              = np.identity(4, dtype=np.float32)
        translate[3, self.xax] = xlen * col
        translate[3, self.yax] = ylen * row
        translate[3, self.zax] = 0
        
        return xform.dot(translate)


    def _updateScrollBar(self):
        """
        If a scroll bar was passed in when this LightBoxCanvas was created,
        this method updates it to reflect the current state of the canvas
        size and the displayed list of images.  
        """
        
        if self._scrollbar is None: return
        
        if len(self.imageList) == 0:
            self._scrollbar.SetScrollbar(0, 0, 0, 0, True)
            return

        dispBounds = self.displayBounds
        screenSize = self.GetClientSize()
        
        sliceRatio = dispBounds.xlen / dispBounds.ylen
        
        sliceWidth   = screenSize.width / float(self.ncols)
        sliceHeight  = sliceWidth * sliceRatio
        
        rowsOnScreen = int(np.floor(screenSize.height / sliceHeight))
        oldPos       = self._scrollbar.GetThumbPosition()

        if rowsOnScreen == 0:
            rowsOnScreen = 1

        if rowsOnScreen > self._nrows:
            rowsOnScreen = self._nrows

        log.debug('Slice size {:3.0f} x {:3.0f}, '
                  'position: {}, '
                  'rows on screen: {} / {}'.format(
                      sliceWidth, sliceHeight,
                      oldPos, rowsOnScreen, self._nrows))

        self._scrollbar.SetScrollbar(oldPos,
                                     rowsOnScreen,
                                     self._nrows,
                                     rowsOnScreen,
                                     True)


    def _calculateCanvasBBox(self):
        """
        Calculates the bounding box for slices to be displayed
        on the canvas, such that their aspect ratio is maintained.
        """

        worldSliceWidth  = float(self.displayBounds.xlen)
        worldSliceHeight = float(self.displayBounds.ylen)

        # If there's a scrollbar, its pagesize
        # value contains the number of rows
        # to be displayed on the screen - see
        # the _updateScrollBar method
        if self._scrollbar is not None:
            rowsOnScreen = self._scrollbar.GetPageSize()
            worldWidth   = worldSliceWidth  * self.ncols
            worldHeight  = worldSliceHeight * rowsOnScreen

        # If there's no scrollbar, we display
        # all the slices on the screen
        else:
            worldWidth   = worldSliceWidth  * self.ncols
            worldHeight  = worldSliceHeight * self._nrows

        slicecanvas.SliceCanvas._calculateCanvasBBox(self,
                                                     worldWidth=worldWidth,
                                                     worldHeight=worldHeight)


    def _setViewport(self):
        """
        Sets up the GL canvas size, viewport and projection.
        """

        xlen = self.displayBounds.xlen
        ylen = self.displayBounds.ylen

        worldYMin  = None
        worldXMax  = self.displayBounds.xmin + xlen * self.ncols
        worldYMax  = self.displayBounds.ymin + ylen * self._nrows

        if self._scrollbar is not None:

            rowsOnScreen = self._scrollbar.GetPageSize()
            currentRow   = self._scrollbar.GetThumbPosition()
            currentRow   = self._nrows - currentRow - rowsOnScreen

            worldYMin = self.displayBounds.ymin + ylen * currentRow
            worldYMax = worldYMin               + ylen * rowsOnScreen

        slicecanvas.SliceCanvas._setViewport(self,
                                             xmax=worldXMax,
                                             ymin=worldYMin,
                                             ymax=worldYMax)

        
    def _draw(self, ev):
        """
        Draws the currently visible slices to the canvas.
        """

        # image data has not been initialised.
        if not self.glReady:
            wx.CallAfter(self._initGLData)
            return

        # No scrollbar -> draw all the slices 
        if self._scrollbar is None:
            startSlice = 0
            endSlice   = self._nslices

        # Scrollbar -> draw a selection of slices
        else:
            rowsOnScreen = self._scrollbar.GetPageSize()
            startRow     = self._scrollbar.GetThumbPosition()
            
            startSlice   = self.ncols * startRow
            endSlice     = startSlice + rowsOnScreen * self.ncols

            if endSlice > self._nslices:
                endSlice = self._nslices

        self.glContext.SetCurrent(self)
        self._setViewport()

        # clear the canvas
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        # load the shaders
        gl.glUseProgram(self.shaders)

        # enable transparency
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        # disable interpolation
        gl.glShadeModel(gl.GL_FLAT)

        # Draw all the slices for all the images.
        
        for i, image in enumerate(self.imageList):
            log.debug('Drawing {} slices for image {}'.format(
                endSlice - startSlice, i))
            for zi in range(startSlice, endSlice):
                self._drawSlice(image,
                                self._sliceIdxs[ i][zi],
                                self._transforms[i][zi]) 

        gl.glUseProgram(0)

        self.SwapBuffers()


class LightBoxPanel(wx.Panel):
    """
    Convenience Panel which contains a a LightBoxCanvas and a scrollbar,
    and sets up mouse-scrolling behaviour.
    """

    def __init__(self, parent, *args, **kwargs):
        """
        Accepts the same parameters as the LightBoxCanvas constructor,
        although if you pass in a scrollbar, it will be ignored.
        """

        wx.Panel.__init__(self, parent)

        self.scrollbar = wx.ScrollBar(self, style=wx.SB_VERTICAL)
        
        kwargs['scrollbar'] = self.scrollbar
        
        self.canvas = LightBoxCanvas(self, *args, **kwargs)

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)

        self.sizer.Add(self.canvas,    flag=wx.EXPAND, proportion=1)
        self.sizer.Add(self.scrollbar, flag=wx.EXPAND)

        def scrollOnMouse(ev):

            wheelDir = ev.GetWheelRotation()

            if   wheelDir > 0: wheelDir = -1
            elif wheelDir < 0: wheelDir =  1

            curPos       = self.scrollbar.GetThumbPosition()
            newPos       = curPos + wheelDir
            sbRange      = self.scrollbar.GetRange()
            rowsOnScreen = self.scrollbar.GetPageSize()

            if self.scrollbar.GetPageSize() >= self.scrollbar.GetRange():
                return
            if newPos < 0 or newPos + rowsOnScreen > sbRange:
                return
            
            self.scrollbar.SetThumbPosition(curPos + wheelDir)
            self.canvas._draw(None)

        self.Bind(wx.EVT_MOUSEWHEEL, scrollOnMouse)

        self.Layout()        
