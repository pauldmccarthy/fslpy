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
log = logging.getLogger(__name__)

import numpy as np

import                        plotpanel
import fsl.data.image      as fslimage
import fsl.utils.transform as transform

# TODO
#      - Whack a scrollbar in there, to allow 
#        zooming/scrolling on the horizontal axis
# 
#      - Add a list, allowing the user to persist
#        time-courses. The list has overlay name and coordinates
#        of each persistent time course


class TimeSeriesPanel(plotpanel.PlotPanel):
    """A panel with a :mod:`matplotlib` canvas embedded within.

    The volume data for each of the overlay objects in the
    :class:`.OverlayList`, at the current :attr:`.DisplayContext.location` is
    plotted on the canvas.
    """

    def __init__(self, parent, overlayList, displayCtx):

        plotpanel.PlotPanel.__init__(self, parent, overlayList, displayCtx)

        figure = self.getFigure()
        canvas = self.getCanvas()

        figure.subplots_adjust(
            top=1.0, bottom=0.0, left=0.0, right=1.0)

        figure.patch.set_visible(False)

        self._mouseDown = False
        canvas.mpl_connect('button_press_event',   self._onPlotMouseDown)
        canvas.mpl_connect('button_release_event', self._onPlotMouseUp)
        canvas.mpl_connect('motion_notify_event',  self._onPlotMouseMove)

        self._overlayList.addListener(
            'overlays',
            self._name,
            self._locationChanged) 
        self._displayCtx.addListener(
            'location',
            self._name,
            self._locationChanged)
        self._displayCtx.addListener(
            'volume',
            self._name,
            self._locationChanged) 

        self.Layout()


    def destroy(self):
        plotpanel.PlotPanel.destroy(self)

        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._displayCtx .removeListener('location',        self._name)
        self._displayCtx .removeListener('volume',          self._name)
        
        
    def _locationChanged(self, *a):
        
        self.getAxis().clear()

        if len(self._overlayList) == 0:
            return 

        self._drawPlot() 


    def _drawPlot(self):

        axis    = self.getAxis()
        canvas  = self.getCanvas()
        x, y, z = self._displayCtx.location.xyz
        vol     = self._displayCtx.volume

        mins = []
        maxs = []
        vols = []

        for overlay in self._overlayList:

            if not isinstance(overlay, fslimage.Image):
                log.warn('{}: Non-volumetric overlay types '
                         'not supported yet'.format(overlay))
                continue

            display = self._displayCtx.getDisplayProperties(overlay)
            xform   = display.getTransform('display', 'voxel')

            ix, iy, iz = transform.transform([[x, y, z]], xform)[0]

            ix = round(ix)
            iy = round(iy)
            iz = round(iz)

            minmaxvol = self._drawPlotOneOverlay(overlay, ix, iy, iz)

            if minmaxvol is not None:
                mins.append(minmaxvol[0])
                maxs.append(minmaxvol[1])
                vols.append(minmaxvol[2])

        axis.axvline(vol, c='#000080', lw=2, alpha=0.4)

        if len(mins) > 0:

            xmin = 0
            xmax = max(vols) - 1
            ymin = min(mins)
            ymax = max(maxs)

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

        canvas.draw()
        self.Refresh()

        
    def _drawPlotOneOverlay(self, overlay, x, y, z):

        display = self._displayCtx.getDisplayProperties(overlay)

        if not overlay.is4DImage(): return None
        if not display.enabled:     return None

        for vox, shape in zip((x, y, z), overlay.shape):
            if vox >= shape or vox < 0:
                return None

        data = overlay.data[x, y, z, :]
        self.getAxis().plot(data, lw=2)

        return data.min(), data.max(), len(data)


    def _onPlotMouseDown(self, ev):
        if ev.inaxes != self.getAxis(): return
        self._mouseDown = True
        self._displayCtx.volume = np.floor(ev.xdata)
        

    def _onPlotMouseUp(self, ev):
        self._mouseDown = False

        
    def _onPlotMouseMove(self, ev):
        if not self._mouseDown:         return
        if ev.inaxes != self.getAxis(): return
        self._displayCtx.volume = np.floor(ev.xdata)
