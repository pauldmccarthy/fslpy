#!/usr/bin/env python
#
# lightboxpanel.py - A panel which contains a LightBoxCanvas, for displaying
# multiple slices from a collection of images.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines the :class:`LightBoxPanel, a panel which contains a
:class:`~fsl.fslview.gl.LightBoxCanvas`, for displaying multiple slices from a
collection of images.
"""

import logging
log = logging.getLogger(__name__)

import wx

import numpy as np

import fsl.utils.layout                        as fsllayout
import fsl.fslview.gl.wxgllightboxcanvas       as lightboxcanvas
import fsl.fslview.controls.lightboxtoolbar    as lightboxtoolbar
import fsl.fslview.displaycontext.lightboxopts as lightboxopts
import canvaspanel


class LightBoxPanel(canvaspanel.CanvasPanel):
    """Convenience Panel which contains a 
    :class:`~fsl.fslview.gl.LightBoxCanvas` and a scrollbar, and sets up
    mouse-scrolling behaviour.
    """


    def __init__(self, parent, imageList, displayCtx):
        """
        """

        sceneOpts = lightboxopts.LightBoxOpts()

        actionz = {
            'toggleLightBoxToolBar' : lambda *a: self.togglePanel(
                lightboxtoolbar.LightBoxToolBar, False, self)
        }

        canvaspanel.CanvasPanel.__init__(self,
                                         parent,
                                         imageList,
                                         displayCtx,
                                         sceneOpts,
                                         actionz)

        imageList  = self._imageList
        displayCtx = self._displayCtx

        self._scrollbar = wx.ScrollBar(
            self.getCanvasPanel(),
            style=wx.SB_VERTICAL)
        
        self._lbCanvas  = lightboxcanvas.LightBoxCanvas(
            self.getCanvasPanel(),
            imageList,
            displayCtx)

        # My properties are the canvas properties
        self._lbCanvas.bindProps('zax',             sceneOpts)
        self._lbCanvas.bindProps('nrows',           sceneOpts)
        self._lbCanvas.bindProps('ncols',           sceneOpts)
        self._lbCanvas.bindProps('topRow',          sceneOpts)
        self._lbCanvas.bindProps('sliceSpacing',    sceneOpts)
        self._lbCanvas.bindProps('zrange',          sceneOpts)
        self._lbCanvas.bindProps('showCursor',      sceneOpts)
        self._lbCanvas.bindProps('showGridLines',   sceneOpts)
        self._lbCanvas.bindProps('highlightSlice',  sceneOpts)
        self._lbCanvas.bindProps('renderMode',      sceneOpts)
        self._lbCanvas.bindProps('softwareMode',    sceneOpts)
        self._lbCanvas.bindProps('resolutionLimit', sceneOpts)

        self._canvasSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.getCanvasPanel().SetSizer(self._canvasSizer)

        self._canvasSizer.Add(self._lbCanvas,  flag=wx.EXPAND, proportion=1)
        self._canvasSizer.Add(self._scrollbar, flag=wx.EXPAND)

        # When the display context location changes,
        # make sure the location is shown on the canvas
        self._lbCanvas.pos.xyz = self._displayCtx.location
        self._displayCtx.addListener('location',
                                     self._name,
                                     self._onLocationChange)
        self._displayCtx.addListener('selectedImage',
                                     self._name,
                                     self._selectedImageChanged)
        self._imageList.addListener('images',
                                     self._name,
                                     self._selectedImageChanged) 

        sceneOpts.zoom = 750

        self._onLightBoxChange()
        self._onZoom()

        # When any lightbox properties change,
        # make sure the scrollbar is updated
        sceneOpts.addListener(
            'ncols',        self._name, self._ncolsChanged)
        sceneOpts.addListener(
            'nrows',        self._name, self._onLightBoxChange)
        sceneOpts.addListener(
            'topRow',       self._name, self._onLightBoxChange)
        sceneOpts.addListener(
            'sliceSpacing', self._name, self._onLightBoxChange)
        sceneOpts.addListener(
            'zrange',       self._name, self._onLightBoxChange)
        sceneOpts.addListener(
            'zax',          self._name, self._onLightBoxChange)
        sceneOpts.addListener(
            'zoom',         self._name, self._onZoom)

        # When the scrollbar is moved,
        # update the canvas display
        self._scrollbar.Bind(wx.EVT_SCROLL, self._onScroll)

        self.Bind(wx.EVT_SIZE, self._onResize)

        self.Layout()

        self._selectedImageChanged()
        self.initProfile()


    def destroy(self):
        """Removes property listeners"""
        canvaspanel.CanvasPanel.destroy(self)

        self._displayCtx.removeListener('location',      self._name)
        self._displayCtx.removeListener('selectedImage', self._name)
        self._imageList .removeListener('images',        self._name)

        
    def _selectedImageChanged(self, *a):
        """Called when the selected image changes.

        Registers a listener on the
        :attr:`~fsl.fslview.displaycontext.ImageDisplay.transform` property
        associated with the selected image, so that the
        :meth:`_transformChanged` method will be called on ``transform``
        changes.
        """

        image = self._displayCtx.getSelectedImage()

        # do nothing if the image list is empty
        if image is None:
            return

        for img in self._imageList:

            display = self._displayCtx.getDisplayProperties(img)

            display.removeListener('transform', self._name)

            if img == image:
                display.addListener('transform',
                                    self._name,
                                    self._transformChanged)

        self._transformChanged()


    def _transformChanged(self, *a):
        """Called when the transform for the currently selected image changes.

        Updates the ``sliceSpacing`` and ``zrange`` properties to values
        sensible to the new image display space.
        """
        
        image = self._displayCtx.getSelectedImage()
        opts  = self.getSceneOptions()

        if image is None:
            return
        
        display = self._displayCtx.getDisplayProperties(image)

        loBounds, hiBounds = display.getDisplayBounds()

        if display.transform == 'id':
            opts.sliceSpacing = 1
            opts.zrange.x     = (0, image.shape[opts.zax] - 1)
        else:
            opts.sliceSpacing = image.pixdim[opts.zax]
            opts.zrange.x     = (loBounds[opts.zax], hiBounds[opts.zax])

        self._onResize()


    def getCanvas(self):
        """Returns a reference to the
        :class:`~fsl.fslview.gl.lightboxcanvas.LightBoxCanvas` instance
        (which is actually a :class:`~fsl.fslview.gl.WXGLLightBoxCanvas`).
        """
        return self._lbCanvas

        
    def _onZoom(self, *a):
        """Called when the :attr:`zoom` property changes. Updates the
        number of columns on the lightbox canvas.
        """
        opts       = self.getSceneOptions()
        minval     = opts.getConstraint('zoom', 'minval')
        maxval     = opts.getConstraint('zoom', 'maxval')
        normZoom   = 1.0 - (opts.zoom - minval) / float(maxval)
        opts.ncols = int(1 + np.round(normZoom * 29))


    def _onResize(self, ev=None):
        """Called when the panel is resized. Automatically adjusts the
        number of lightbox rows to the maximum displayable number (given
        that the number of columns is fixed).
        """
        if ev is not None: ev.Skip()

        # Lay this panel out, so the
        # canvas panel size is up to date
        self.Layout()

        width,   height   = self._lbCanvas .GetClientSize().Get()
        sbWidth, sbHeight = self._scrollbar.GetClientSize().Get()

        width = width - sbWidth

        xlen = self._displayCtx.bounds.getLen(self._lbCanvas.xax)
        ylen = self._displayCtx.bounds.getLen(self._lbCanvas.yax)

        sliceWidth  = width / float(self._lbCanvas.ncols)
        sliceHeight = fsllayout.calcPixHeight(xlen, ylen, sliceWidth)

        if sliceHeight > 0: 
            self._lbCanvas.nrows = int(height / sliceHeight)


    def _onLocationChange(self, *a):
        """Called when the display context location changes.

        Updates the canvas location.
        """
        
        xpos = self._displayCtx.location.getPos(self._lbCanvas.xax)
        ypos = self._displayCtx.location.getPos(self._lbCanvas.yax)
        zpos = self._displayCtx.location.getPos(self._lbCanvas.zax)
        self._lbCanvas.pos.xyz = (xpos, ypos, zpos)


    def _ncolsChanged(self, *a):
        """Called when the lightbox canvas ``ncols`` property changes.
        Calculates the number of rows to display, and updates the
        scrollbar.
        """
        self._onResize()
        self._onLightBoxChange()


    def _onLightBoxChange(self, *a):
        """Called when any lightbox display properties change.

        Updates the scrollbar to reflect the change.
        """
        self._scrollbar.SetScrollbar(self._lbCanvas.topRow,
                                     self._lbCanvas.nrows,
                                     self._lbCanvas.getTotalRows(),
                                     self._lbCanvas.nrows,
                                     True)

        
    def _onScroll(self, *a):
        """Called when the scrollbar is moved.

        Updates the top row displayed on the canvas.
        """
        self._lbCanvas.topRow = self._scrollbar.GetThumbPosition()
