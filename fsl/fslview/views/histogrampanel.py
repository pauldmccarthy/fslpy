#!/usr/bin/env python
#
# histogrampanel.py - A panel which plots a histogram for the data from the
#                     currently selected image.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging


import wx

import numpy             as np
import matplotlib.pyplot as plt

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as Canvas

import props

import fsl.fslview.panel as fslpanel
import fsl.data.strings  as strings


log = logging.getLogger(__name__)

#
# Ideas:
#
#    - Plot histogram for multiple images (how to select them?)
#
#    - Ability to apply a label mask image, and plot separate
#      histograms for each label
# 
#    - Ability to put an overlay on the display, showing the
#      voxels that are within the histogram range
#
#    - For 4D images, add an option to plot the histogram for
#      the current volume only, or for all volumes
#
#    - For different image types (e.g. vector), add anoption
#      to plot the histogram of calculated values, e.g.
#      magnitude, or separate histogram lines for xyz
#      components?
# 
class HistogramPanel(fslpanel.FSLViewPanel):

    
    dataRange = props.Bounds(
        ndims=1,
        labels=[strings.choices['HistogramPanel.dataRange.min'],
                strings.choices['HistogramPanel.dataRange.max']])
    
    nbins     = props.Int( minval=10,  maxval=500, default=100, clamped=True)
    autoHist  = props.Boolean(default=True)


    def __init__(self, parent, imageList, displayCtx):

        fslpanel.FSLViewPanel.__init__(self, parent, imageList, displayCtx)


        self._figure = plt.Figure()
        self._axis   = self._figure.add_subplot(111)
        self._canvas = Canvas(self, -1, self._figure)
        
        self._figure.subplots_adjust(
            top=1.0, bottom=0.0, left=0.0, right=1.0)

        self._figure.patch.set_visible(False)

        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self._sizer)

        import fsl.fslview.layouts as layouts
        self._configPanel = fslpanel.ConfigPanel(
            self, self, layouts.layouts[self, 'props'])
        
        self._sizer.Add(self._configPanel, flag=wx.EXPAND)
        self._sizer.Add(self._canvas,      flag=wx.EXPAND, proportion=1) 

        self._imageList.addListener(
            'images',
            self._name,
            self._selectedImageChanged) 
        self._displayCtx.addListener(
            'selectedImage',
            self._name,
            self._selectedImageChanged)

        self._mouseDown = False
        self._canvas.mpl_connect('button_press_event',   self._onPlotMouseDown)
        self._canvas.mpl_connect('button_release_event', self._onPlotMouseUp)
        self._canvas.mpl_connect('motion_notify_event',  self._onPlotMouseMove)        

        self.addListener('dataRange', self._name, self._drawPlot)
        self.addListener('nbins',     self._name, self._drawPlot)
        self.addListener('autoHist',  self._name, self._drawPlot)

        self._domainHighlight = None
        
        self._selectedImageChanged()

        self.Layout()

        
    def destroy(self):
        """De-registers property listeners. """
        fslpanel.FSLViewPanel.destroy(self)

        self._imageList .removeListener('images',        self._name)
        self._displayCtx.removeListener('selectedImage', self._name)

        
    def _autoHistogramBins(self, data):

        # Automatic histogram bin calculation
        # as implemented in the original FSLView

        dMin, dMax = self.dataRange.x
        dRange     = dMax - dMin

        binSize = np.power(10, np.ceil(np.log10(dRange) - 1) - 1)

        nbins = dRange / binSize
        
        while nbins < 100:
            binSize /= 2
            nbins    = dRange / binSize

        if issubclass(data.dtype.type, np.integer):
            binSize = max(1, np.ceil(binSize))

        adjMin = np.floor(dMin / binSize) * binSize
        adjMax = np.ceil( dMax / binSize) * binSize

        nbins = int((adjMax - adjMin) / binSize) + 1

        print binSize, nbins

        return nbins

    
    def _calcHistogram(self, data):
        
        if self.autoHist: nbins = self._autoHistogramBins(data)
        else:             nbins = self.nbins
        
        histY, histX = np.histogram(data.flat,
                                    bins=nbins,
                                    range=self.dataRange.x)
        
        # np.histogram returns all bin
        # edges, including the right hand
        # side of the final bin. Remove it.
        # And also shift the remaining
        # bin edges so they are centred
        # within each bin
        histX  = histX[:-1]
        histX += (histX[1] - histX[0]) / 2.0

        return histX, histY

    
    def _selectedImageChanged(self, *a):

        if len(self._imageList) == 0:
            return

        image = self._displayCtx.getSelectedImage()

        minval = float(image.data.min())
        maxval = float(image.data.max())

        # update the  histgram range from the data range
        self.disableListener('dataRange', self._name)
        
        self.dataRange.setMin(  0, minval)
        self.dataRange.setMax(  0, maxval)
        self.dataRange.setRange(0, minval, maxval)
        
        self.enableListener('dataRange', self._name)

        self._drawPlot()


    def _onPlotMouseDown(self, ev):
        
        if ev.inaxes != self._axis:
            return
        if self._displayCtx.getSelectedImage() is None:
            return

        self._mouseDown       = True
        self._domainHighlight = [ev.xdata, ev.xdata]

    
    def _onPlotMouseMove(self, ev):
        if not self._mouseDown:
            return
        
        if ev.inaxes != self._axis:
            return

        self._domainHighlight[1] = ev.xdata
        self._drawPlot()

    
    def _onPlotMouseUp(self, ev):

        if not self._mouseDown or self._domainHighlight is None:
            return

        # Sort the domain min/max in case the mouse was
        # dragged from right to left, in which case the
        # second value would be less than the first
        newRange              = sorted(self._domainHighlight)
        self._mouseDown       = False
        self._domainHighlight = None
        self.dataRange.x      = newRange

    
    def _drawPlot(self, *a):

        self._axis.clear()

        image = self._displayCtx.getSelectedImage()
        x, y  = self._calcHistogram(image.data)

        self._axis.step(x, y)
        self._axis.grid(True)
        
        xmin = x.min()
        xmax = x.max()
        ymin = y.min()
        ymax = y.max()

        xlen = xmax - xmin
        ylen = ymax - ymin

        self._axis.grid(True)
        self._axis.set_xlim((xmin - xlen * 0.05, xmax + xlen * 0.05))
        self._axis.set_ylim((ymin - ylen * 0.05, ymax + ylen * 0.05))

        if ymin != ymax: yticks = np.linspace(ymin, ymax, 5)
        else:            yticks = [ymin]

        self._axis.set_yticks(yticks)

        for tick in self._axis.yaxis.get_major_ticks():
            tick.set_pad(-15)
            tick.label1.set_horizontalalignment('left')
        for tick in self._axis.xaxis.get_major_ticks():
            tick.set_pad(-20)


        if self._domainHighlight is not None:
            self._axis.axvspan(self._domainHighlight[0],
                               self._domainHighlight[1],
                               fill=True,
                               facecolor='#000080',
                               edgecolor='none',
                               alpha=0.4)

        self._canvas.draw()
        self.Refresh() 
