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
import fsl.fslview.controls   as fslcontrols
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

        self.__calcInitDataRange()
        self.histPropsChanged()

        self.addListener('nbins',       self.name, self.histPropsChanged)
        self.addListener('ignoreZeros', self.name, self.histPropsChanged)
        self.addListener('volume',      self.name, self.histPropsChanged)
        self.addListener('allVolumes',  self.name, self.histPropsChanged)
        self.addListener('dataRange',   self.name, self.histPropsChanged)

        
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

        nvals     = data.size
        dataRange = self.dataRange.x

        log.debug('Calculating histogram for overlay '
                  '{} (number of values {})'.format(
                      self.overlay.name,
                      nvals))
        
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
        self.nvals = nvals


    def getData(self):

        xdata    = self.xdata
        ydata    = self.ydata
        nvals    = self.nvals
        histType = self.hsPanel.histType

        if   histType == 'count':       return xdata, ydata
        elif histType == 'probability': return xdata, ydata / nvals

    
class HistogramPanel(plotpanel.PlotPanel):


    autoBin       = props.Boolean(default=True)
    showCurrent   = props.Boolean(default=True)
    enableOverlay = props.Boolean(default=False)
    histType      = props.Choice(('probability', 'count'))
    

    def __init__(self, parent, overlayList, displayCtx):

        actionz = {
            'toggleHistogramList'    : lambda *a: self.togglePanel(
                fslcontrols.HistogramListPanel,    False, self),
            'toggleHistogramControl' : lambda *a: self.togglePanel(
                fslcontrols.HistogramControlPanel, False, self) 
        }

        plotpanel.PlotPanel.__init__(
            self, parent, overlayList, displayCtx, actionz)

        figure = self.getFigure()
        
        figure.subplots_adjust(
            top=1.0, bottom=0.0, left=0.0, right=1.0)

        figure.patch.set_visible(False)

        self._overlayList.addListener('overlays',
                                      self._name,
                                      self.__overlaysChanged)
        self._displayCtx .addListener('selectedOverlay',
                                      self._name,
                                      self.draw)

        # Re draw whenever any PlotPanel or
        # HistogramPanel property changes.
        self.addGlobalListener(self._name, self.draw)

        # But a separate listener for autoBin -
        # this overwrites the one added by the
        # addGlobalListener method above. See
        # the __autoBinChanged method.
        self.addListener('autoBin',
                         self._name,
                         self.__autoBinChanged,
                         overwrite=True)

        self.__current = None
        self.__updateCurrent()

        self.Layout()


    def destroy(self):
        """De-registers property listeners. """
        plotpanel.PlotPanel.destroy(self)

        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)


    def __overlaysChanged(self, *a):
        self.disableListener('dataSeries', self._name)
        for ds in self.dataSeries:
            if ds.overlay not in self._overlayList:
                self.dataSeries.remove(ds)
        self.enableListener('dataSeries', self._name)
        self.draw() 

        
    def __autoBinChanged(self, *a):
        """Called when the :attr:`autoBin` property changes. Makes sure that
        all existing :class:`HistogramSeries` instances are updated before
        the plot is refreshed.
        """

        for ds in self.dataSeries:
            ds.histPropsChanged()

        if self.__current is not None:
            self.__current.histPropsChanged()

        self.draw()
        

    def __updateCurrent(self, *a):

        overlay        = self._displayCtx.getSelectedOverlay()
        currentHs      = self.__current
        self.__current = None

        if len(self._overlayList) == 0             or \
           not isinstance(overlay, fslimage.Image) or \
           overlay in [hs.overlay for hs in self.dataSeries]:
            return
        
        if currentHs is not None and \
           currentHs.overlay not in [hs.overlay for hs in self.dataSeries]:
            self.__current = currentHs
            
        else:
            hs             = HistogramSeries(self, overlay)
            hs.colour      = [0, 0, 0]
            hs.alpha       = 1
            hs.lineWidth   = 2
            hs.lineStyle   = ':'
            hs.label       = None

            self.__current = hs


    def getCurrent(self): 
        return self.__current


    def draw(self, *a):

        self.__updateCurrent()
        current = self.getCurrent()

        if self.showCurrent and \
           current is not None: self.drawDataSeries([current])
        else:                   self.drawDataSeries()
