#!/usr/bin/env python
#
# timeseriespanel.py - A panel which plots time series/volume data from a
# collection of overlays.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""A :class:`wx.Panel` which plots time series/volume data from a collection
of overlay objects stored in an :class:`.OverlayList`.

:mod:`matplotlib` is used for plotting.

"""

import logging

import numpy as np

import                               props

import                               plotpanel
import fsl.data.image             as fslimage
import fsl.fslview.displaycontext as fsldisplay
import fsl.fslview.controls       as fslcontrols
import fsl.utils.transform        as transform


log = logging.getLogger(__name__)

class TimeSeries(plotpanel.DataSeries):

    
    def __init__(self, overlay, coords):
        plotpanel.DataSeries.__init__(self, overlay)
        
        self.coords = map(int, coords)
        self.data   = overlay.data[coords[0], coords[1], coords[2], :]

        
    def getData(self):
        return self.data


class TimeSeriesPanel(plotpanel.PlotPanel):
    """A panel with a :mod:`matplotlib` canvas embedded within.

    The volume data for each of the overlay objects in the
    :class:`.OverlayList`, at the current :attr:`.DisplayContext.location` is
    plotted on the canvas.
    """

    
    demean    = props.Boolean(default=True)
    usePixdim = props.Boolean(default=False)


    def export(self, *a):
        # Export all displayed time series to text file
        pass
    

    def __init__(self, parent, overlayList, displayCtx):

        actionz = {
            'toggleTimeSeriesList'    : lambda *a: self.togglePanel(
                fslcontrols.TimeSeriesListPanel,    False, self),
            'toggleTimeSeriesControl' : lambda *a: self.togglePanel(
                fslcontrols.TimeSeriesControlPanel, False, self) 
        }

        plotpanel.PlotPanel.__init__(
            self, parent, overlayList, displayCtx, actionz=actionz)

        figure = self.getFigure()

        figure.subplots_adjust(
            top=1.0, bottom=0.0, left=0.0, right=1.0)

        figure.patch.set_visible(False)


        overlayList.addListener('overlays',
                                self._name,
                                self.__overlaysChanged)        
 
        displayCtx .addListener('selectedOverlay', self._name, self.draw) 
        displayCtx .addListener('location',        self._name, self.draw)
        
        self.Layout()
        self.draw()


    def destroy(self):
        plotpanel.PlotPanel.destroy(self)
        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._displayCtx .removeListener('location',        self._name)


    def __overlaysChanged(self, *a):

        self.disableListener('dataSeries', self._name)
        for ds in self.dataSeries:
            if ds.overlay not in self._overlayList:
                self.dataSeries.remove(ds)
        self.enableListener('dataSeries', self._name)
        self.draw()
            

        
    def __calcCurrent(self):

        self.__current = None

        if len(self._overlayList) == 0:
            return 

        x, y, z = self._displayCtx.location.xyz
        overlay = self._displayCtx.getSelectedOverlay()
        opts    = self._displayCtx.getOpts(overlay)

        if not isinstance(overlay, fslimage.Image)        or \
           not isinstance(opts,    fsldisplay.VolumeOpts) or \
           not overlay.is4DImage():
            return 
        
        xform = opts.getTransform('display', 'voxel')
        vox   = transform.transform([[x, y, z]], xform)[0]
        vox   = np.floor(vox + 0.5)

        if vox[0] < 0                 or \
           vox[1] < 0                 or \
           vox[2] < 0                 or \
           vox[0] >= overlay.shape[0] or \
           vox[1] >= overlay.shape[1] or \
           vox[2] >= overlay.shape[2]:
            return 

        ts = TimeSeries(overlay, vox)
        ts.colour    = [0.2, 0.2, 0.2]
        ts.lineWidth = 1
        ts.lineStyle = ':'
        ts.label     = None

        self.__current = ts

        
    def getCurrent(self):
        return self.__current


    def draw(self, *a):

        self.__calcCurrent()
        current = self.getCurrent()
        
        if current is not None: self.drawDataSeries([self.getCurrent()])
        else:                   self.drawDataSeries()
