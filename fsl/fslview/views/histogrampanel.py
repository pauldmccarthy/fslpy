#!/usr/bin/env python
#
# histogrampanel.py - A panel which plots a histogram for the data from the
#                     currently selected overlay.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging


import numpy as np

import props

import fsl.data.image                        as fslimage
import fsl.data.strings                      as strings
import fsl.fslview.controls.histogramtoolbar as histogramtoolbar
import                                          plotpanel


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
class HistogramPanel(plotpanel.PlotPanel):

    
    dataRange = props.Bounds(
        ndims=1,
        labels=[strings.choices['HistogramPanel.dataRange.min'],
                strings.choices['HistogramPanel.dataRange.max']])
    
    nbins     = props.Int( minval=10,  maxval=500, default=100, clamped=True)
    autoHist  = props.Boolean(default=True)


    def __init__(self, parent, overlayList, displayCtx):

        actionz = {'toggleToolbar' : lambda *a: self.togglePanel(
            histogramtoolbar.HistogramToolBar, False, self)}

        plotpanel.PlotPanel.__init__(
            self, parent, overlayList, displayCtx, actionz)

        figure = self.getFigure()
        canvas = self.getCanvas()
        
        figure.subplots_adjust(
            top=1.0, bottom=0.0, left=0.0, right=1.0)

        figure.patch.set_visible(False)

        self._overlayList.addListener(
            'overlays',
            self._name,
            self._selectedOverlayChanged) 
        self._displayCtx.addListener(
            'selectedOverlay',
            self._name,
            self._selectedOverlayChanged)

        self.addListener('dataRange', self._name, self._drawPlot)
        self.addListener('nbins',     self._name, self._drawPlot)
        self.addListener('autoHist',  self._name, self._drawPlot)

        self._domainHighlight = None
        
        self._selectedOverlayChanged()

        self.Layout()

        
    def destroy(self):
        """De-registers property listeners. """
        plotpanel.PlotPanel.destroy(self)

        self             .removeListener('dataRange',       self._name)
        self             .removeListener('nbins',           self._name)
        self             .removeListener('autoHist',        self._name)
        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)

        
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

    
    def _selectedOverlayChanged(self, *a):

        if len(self._overlayList) == 0:
            return

        overlay = self._displayCtx.getSelectedOverlay()

        if not isinstance(overlay, fslimage.Image):
            self.message(strings.messages[self, 'noData'])
            return

        minval = float(overlay.data.min())
        maxval = float(overlay.data.max())

        # update the  histgram range from the data range
        self.disableListener('dataRange', self._name)
        
        self.dataRange.setMin(  0, minval)
        self.dataRange.setMax(  0, maxval)
        self.dataRange.setRange(0, minval, maxval)
        
        self.enableListener('dataRange', self._name)

        self._drawPlot()


    def _drawPlot(self, *a):

        overlay = self._displayCtx.getSelectedOverlay()

        if overlay is None or not isinstance(overlay, fslimage.Image):
            return

        axis    = self.getAxis()
        x, y    = self._calcHistogram(overlay.data)

        axis.clear()
        axis.step(x, y)
        axis.grid(True)
        
        xmin = x.min()
        xmax = x.max()
        ymin = y.min()
        ymax = y.max()

        xlen = xmax - xmin
        ylen = ymax - ymin

        axis.grid(True)
        axis.set_xlim((xmin - xlen * 0.05, xmax + xlen * 0.05))
        axis.set_ylim((ymin - ylen * 0.05, ymax + ylen * 0.05))

        if ymin != ymax: yticks = np.linspace(ymin, ymax, 5)
        else:            yticks = [ymin]

        axis.set_yticks(yticks)

        for tick in axis.yaxis.get_major_ticks():
            tick.set_pad(-15)
            tick.label1.set_horizontalalignment('left')
            
        for tick in axis.xaxis.get_major_ticks():
            tick.set_pad(-20)

        self.getCanvas().draw()
        self.Refresh() 
