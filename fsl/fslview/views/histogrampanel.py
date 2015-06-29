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

import fsl.data.image         as fslimage
import fsl.data.strings       as strings
import fsl.fslview.colourmaps as fslcm
import                           plotpanel


log = logging.getLogger(__name__)


        
def autoBin(data, dataRange):

    # Automatic histogram bin calculation
    # as implemented in the original FSLView

    dMin, dMax = dataRange
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

class HistogramSeries(plotpanel.DataSeries):

    nbins       = props.Int(minval=10, maxval=500, default=100, clamped=True)
    ignoreZeros = props.Boolean(default=True)
    volume      = props.Int(minval=0, maxval=0, clamped=True)
    allVolumes  = props.Boolean(default=False)
    dataRange   = props.Bounds(
        ndims=1,
        labels=[strings.choices['HistogramPanel.dataRange.min'],
                strings.choices['HistogramPanel.dataRange.max']])

    
    def __init__(self, hsPanel, overlay, volume=0):

        plotpanel.DataSeries.__init__(self, overlay)
        self.hsPanel = hsPanel
        self.name    = '{}_{}'.format(type(self).__name__, id(self))
        self.volume  = volume

        if overlay.is4DImage():
            self.setConstraint('volume', 'maxval', overlay.shape[3] - 1)

        hsPanel.addListener('autoBin',   self.name, self.histPropsChanged)
        self   .addListener('nbins',     self.name, self.histPropsChanged)
        self   .addListener('dataRange', self.name, self.histPropsChanged)

        self.__calcInitDataRange()
        self.histPropsChanged()

        
    def __del__(self):
        self.hsPanel.removeListener('autoBin', self.name)

        
    def __calcInitDataRange(self):
        
        if self.overlay.is4DImage():
            if self.allVolumes: data = self.overlay.data[:]
            else:               data = self.overlay.data[..., self.volume]
        else:
            data = self.overlay.data[:]

        data = data[np.isfinite(data)]

        if self.ignoreZeros:
            data = data[data != 0]

        self.dataRange.x = data.min(), data.max()

    
    def histPropsChanged(self, *a):

        if self.overlay.is4DImage():
            if self.allVolumes: data = self.overlay.data[:]
            else:               data = self.overlay.data[..., self.volume]
        else:
            data = self.overlay.data[:]

        data = data[np.isfinite(data)]

        if self.ignoreZeros:
            data = data[data != 0]

        dataRange = self.dataRange.x
        
        if self.hsPanel.autoBin: nbins = autoBin(data, dataRange)
        else:                    nbins = self.nbins
        
        histY, histX = np.histogram(data.flat,
                                    bins=nbins,
                                    range=dataRange)
        
        # np.histogram returns all bin
        # edges, including the right hand
        # side of the final bin. Remove it.
        # And also shift the remaining
        # bin edges so they are centred
        # within each bin
        histX  = histX[:-1]
        histX += (histX[1] - histX[0]) / 2.0

        self.xdata = np.array(histX, dtype=np.float32)
        self.ydata = np.array(histY, dtype=np.float32)


    def getData(self):
        return self.xdata, self.ydata

    
class HistogramPanel(plotpanel.PlotPanel):


    autoBin       = props.Boolean(default=True)
    showCurrent   = props.Boolean(default=True)

    enableOverlay = props.Boolean(default=False)
    

    def __init__(self, parent, overlayList, displayCtx):

        actionz = {}

        plotpanel.PlotPanel.__init__(
            self, parent, overlayList, displayCtx, actionz)

        figure = self.getFigure()
        
        figure.subplots_adjust(
            top=1.0, bottom=0.0, left=0.0, right=1.0)

        figure.patch.set_visible(False)

        self._overlayList.addListener(
            'overlays',
            self._name,
            self.__selectedOverlayChanged) 
        self._displayCtx.addListener(
            'selectedOverlay',
            self._name,
            self.__selectedOverlayChanged)

        self.__selectedOverlayChanged()

        self.Layout()

        
    def destroy(self):
        """De-registers property listeners. """
        plotpanel.PlotPanel.destroy(self)

        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)


    def __calcCurrent(self):
        self.__current = None

        if self._overlayList == 0:
            return

        overlay = self._displayCtx.getSelectedOverlay()

        if not isinstance(overlay, fslimage.Image):
            return

        hs             = HistogramSeries(self, overlay)
        hs.colour      = [0.2, 0.2, 0.2]
        hs.alpha       = 1
        hs.lineWidth   = 0.5
        hs.lineStyle   = ':'
        hs.label       = None

        self.__current = hs


    def getCurrent(self): 
        return self.__current

    
    def __selectedOverlayChanged(self, *a):

        if len(self._overlayList) == 0:
            return


        self.draw()


    def draw(self, *a):

        self.__calcCurrent()
        current = self.getCurrent()

        if current is not None: self.drawDataSeries([current])
        else:                   self.drawDataSeries()
