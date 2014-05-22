#!/usr/bin/env python
#
# lightboxcanvas.py - A wx.GLCanvas canvas whcih displays all slices from
# a collection of 3D images.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import wx

import numpy as np

import OpenGL.GL as gl

import fsl.fslview.slicecanvas as slicecanvas


class LightBoxCanvas(slicecanvas.SliceCanvas):
    """
    """


    def __init__(self,
                 parent,
                 imageList,
                 zax,
                 context=None,
                 sliceSpacing=2,
                 ncols=20,
                 scrollbar=None):
        """
        """

        if (scrollbar is not None) and (not scrollbar.IsVertical()):
            raise RuntimeError('LightBoxCanvas only supports '
                               'a vertical scrollbar')

        slicecanvas.SliceCanvas.__init__(self, parent, imageList, zax, context)

        self._scrollbar    = scrollbar
        self._sliceSpacing = sliceSpacing
        self._ncols        = ncols

        # nrows is automatically calculated 
        # in the _imageListChangd method -
        # the value 0 is just a placeholder
        self._nrows = 0

        if scrollbar is not None:
            scrollbar.Bind(wx.EVT_SCROLL, self._draw)


    def _imageListChanged(self):
        """
        Called when the list of displayed images changes. Calls
        SliceCanvas._imageListChanged (which recalculates the
        bounds of all images in the list) and then, for each
        image, generates a list of transformation matrices, and
        a list of slice indices. The latter specifies the slice
        indices from the image to be displayed, and the former
        specifies the transformation matrix to be used to
        position the slice on the canvas.
        """

        self._updateScrollBar()

        # recalculate image bounds, and create
        # GL data for any newly added images.
        slicecanvas.SliceCanvas._imageListChanged(self)

        # calculate the locations, in real world coordinates,
        # of all slices to be displayed on the canvas
        sliceLocs = np.arange(
            self.zmin + 0.5 * self._sliceSpacing,
            self.zmax,
            self._sliceSpacing)

        self._nslices = len(sliceLocs)
        self._nrows   = int(np.ceil(self._nslices / float(self._ncols)))

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


    def _updateScrollBar(self):
        """
        If a scroll bar was passed in when this LightBoxCanvas was created,
        this method updates it to reflect the current state of the canvas
        size and the displayed list of images.
        """
        
        if self._scrollbar is None: return

        screenSize = self.GetClientSize()
        sliceRatio = abs(self.xmax - self.xmin) / abs(self.ymax - self.ymin)

        sliceWidth   = screenSize.width / float(self._ncols)
        sliceHeight  = sliceWidth * sliceRatio
        rowsOnScreen = int(np.floor(screenSize.height / sliceHeight))
        oldPos       = self._scrollbar.GetThumbPosition()

        if rowsOnScreen == 0:
            rowsOnScreen = 1

        self._scrollbar.SetScrollbar(oldPos,
                                     rowsOnScreen,
                                     self._nrows,
                                     rowsOnScreen,
                                     True)


    def _calculateSliceTransform(self, image, sliceno):
        """
        Calculates a transformation matrix for the given slice
        number. Each slice is displayed on the same canvas, but
        is translated to a specific row/column. So a copy of
        the voxToWorld transformation matrix of the given image
        is made, and a translation applied to it, to position
        the slice in the correct location on the canvas.
        """

        nrows = self._nrows
        ncols = self._ncols

        xform = np.array(image.voxToWorldMat, dtype=np.float32)

        row = nrows - int(np.floor(sliceno / ncols)) - 1
        col = int(np.floor(sliceno % ncols))

        xlen = abs(self.xmax - self.xmin)
        ylen = abs(self.ymax - self.ymin)

        translate              = np.identity(4, dtype=np.float32)
        translate[3, self.xax] = xlen * col
        translate[3, self.yax] = ylen * row
        translate[3, self.zax] = 0
        
        return xform.dot(translate)


    def _calculateCanvasBBox(self, ev):
        """
        Calculates the bounding box for slices to be displayed
        on the canvas, such that their aspect ratio is maintained.
        """

        # _calculateCanvasBBox is called on window resizes.
        # We also want the scroll bar to be updated when
        # the window size changes, so there you go.
        self._updateScrollBar()

        worldSliceWidth  = float(abs(self.xmax - self.xmin))
        worldSliceHeight = float(abs(self.ymax - self.ymin))

        if self._scrollbar is not None:
            rowsOnScreen = self._scrollbar.GetPageSize()
            worldWidth   = worldSliceWidth  * self._ncols
            worldHeight  = worldSliceHeight * rowsOnScreen
            
        else:
            worldWidth   = worldSliceWidth  * self._ncols
            worldHeight  = worldSliceHeight * self._nrows

        slicecanvas.SliceCanvas._calculateCanvasBBox(self,
                                                     ev,
                                                     worldWidth=worldWidth,
                                                     worldHeight=worldHeight)


    def _resize(self):
        """
        Sets up the GL canvas size, viewport and projection.
        """

        xlen = abs(self.xmax - self.xmin)
        ylen = abs(self.ymax - self.ymin)        

        worldYMin  = None
        worldXMax  = self.xmin + xlen * self._ncols
        worldYMax  = self.ymin + ylen * self._nrows

        if self._scrollbar is not None:

            rowsOnScreen = self._scrollbar.GetPageSize()
            currentRow   = self._scrollbar.GetThumbPosition()
            currentRow   = self._nrows - currentRow - rowsOnScreen

            worldYMin = self.ymin + ylen * currentRow
            worldYMax = worldYMin + ylen * rowsOnScreen

        slicecanvas.SliceCanvas._resize(self,
                                        xmax=worldXMax,
                                        ymin=worldYMin,
                                        ymax=worldYMax)

        
    def _draw(self, ev):
        """
        Draws the currently selected slice to the canvas.
        """

        # image data has not been initialised.
        if not self.glReady:
            wx.CallAfter(self._initGLData)
            return

        if self._scrollbar is None:
            startSlice = 0
            endSlice   = self._nslices
        else:
            rowsOnScreen = self._scrollbar.GetPageSize()
            startRow     = self._scrollbar.GetThumbPosition()
            
            startSlice   = self._ncols * startRow
            endSlice     = startSlice + rowsOnScreen * self._ncols

            if endSlice > self._nslices:
                endSlice = self._nslices

        self.context.SetCurrent(self)
        self._resize()

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
            for zi in range(startSlice, endSlice):
                self._drawSlice(image,
                                self._sliceIdxs[ i][zi],
                                self._transforms[i][zi]) 

        gl.glUseProgram(0)

        self.SwapBuffers()


class LightBoxFrame(wx.Frame):
    """
    Convenience class for displaying a LightBoxPanel in a standalone window.
    """

    def __init__(self, parent, imageList, title=None):

        wx.Frame.__init__(self, parent, title=title)

        import fsl.fslview.imagelistpanel as imagelistpanel


        self.canvasPanel = wx.Panel(self)
        self.listPanel   = imagelistpanel.ImageListPanel(self, imageList)


        self.scrollbar = wx.ScrollBar(  self.canvasPanel, style=wx.SB_VERTICAL)
        self.mainPanel = LightBoxCanvas(self.canvasPanel, imageList, zax=1,
                                        scrollbar=self.scrollbar,
                                        sliceSpacing=0.5,
                                        ncols=10)

        self.canvasSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.canvasPanel.SetSizer(self.canvasSizer)

        self.canvasSizer.Add(self.mainPanel, flag=wx.EXPAND, proportion=1)
        self.canvasSizer.Add(self.scrollbar, flag=wx.EXPAND)

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.sizer.Add(self.canvasPanel, flag=wx.EXPAND, proportion=1)
        self.sizer.Add(self.listPanel,   flag=wx.EXPAND)

        self.SetSizer(self.sizer)
        self.Layout()


if __name__ == '__main__':

    import sys
    import fsl.data.fslimage as fslimage

    files = sys.argv[1:]
    # files = ['/Users/paulmc/MNI152_T1_2mm.nii']

    imgs    = map(fslimage.Image, files)
    imgList = fslimage.ImageList(imgs)
    app     = wx.App()
    oframe  = LightBoxFrame(None, imgList, "Test")
    
    oframe.Show()



    # import wx.lib.inspection
    # wx.lib.inspection.InspectionTool().Show()    
    app.MainLoop()
