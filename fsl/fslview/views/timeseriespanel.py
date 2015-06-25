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

import numpy                      as np

import                               props

import                               plotpanel
import fsl.data.image             as fslimage
import fsl.data.strings           as strings
import fsl.fslview.displaycontext as fsldisplay
import fsl.fslview.colourmaps     as fslcm
import fsl.fslview.controls       as fslcontrols
import fsl.utils.transform        as transform


log = logging.getLogger(__name__)



# TODO
#      - Whack a scrollbar in there, to allow 
#        zooming/scrolling on the horizontal axis
# 
#      - Add a list, allowing the user to persist
#        time-courses. The list has overlay name and coordinates
#        of each persistent time course


class TimeSeries(object):

    def __init__(self, overlay, coords, data, colour, label):
        self.overlay = overlay
        self.coords  = coords
        self.data    = data
        self.colour  = colour
        self.label   = label


class TimeSeriesPanel(plotpanel.PlotPanel):
    """A panel with a :mod:`matplotlib` canvas embedded within.

    The volume data for each of the overlay objects in the
    :class:`.OverlayList`, at the current :attr:`.DisplayContext.location` is
    plotted on the canvas.
    """


    timeSeries = props.List()
    

    def __init__(self, parent, overlayList, displayCtx):

        actionz = {
            'toggleTimeSeriesList' : lambda *a: self.togglePanel(
                fslcontrols.TimeSeriesListPanel, False, self)
        }

        plotpanel.PlotPanel.__init__(
            self, parent, overlayList, displayCtx, actionz=actionz)

        figure = self.getFigure()

        figure.subplots_adjust(
            top=1.0, bottom=0.0, left=0.0, right=1.0)

        figure.patch.set_visible(False)

        name = self._name
        draw = self._draw

        self._overlayList.addListener('overlays',        name, draw)
        self._displayCtx .addListener('selectedOverlay', name, draw) 
        self._displayCtx .addListener('location',        name, draw)
        self             .addListener('timeSeries',      name, draw)

        self.Layout()
        self._draw()


    def destroy(self):
        plotpanel.PlotPanel.destroy(self)

        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._displayCtx .removeListener('location',        self._name)

        
    def getCurrent(self):

        x, y, z = self._displayCtx.location.xyz
        overlay = self._displayCtx.getSelectedOverlay()
        opts    = self._displayCtx.getOpts(overlay)

        if not isinstance(overlay, fslimage.Image)        or \
           not isinstance(opts,    fsldisplay.VolumeOpts) or \
           not overlay.is4DImage():
            return None
        
        xform = opts.getTransform('display', 'voxel')
        vox   = transform.transform([[x, y, z]], xform)[0]
        vox   = np.floor(vox + 0.5)

        if vox[0] < 0                 or \
           vox[1] < 0                 or \
           vox[2] < 0                 or \
           vox[0] >= overlay.shape[0] or \
           vox[1] >= overlay.shape[1] or \
           vox[2] >= overlay.shape[2]:
            return None

        return TimeSeries(
            overlay,
            vox,
            overlay.data[vox[0], vox[1], vox[2], :],
            [0.5, 0.5, 0.5],
            '{} [{} {} {}]'.format(overlay.name, vox[0], vox[1], vox[2]))


    def _draw(self, *a):

        axis   = self.getAxis()
        canvas = self.getCanvas()

        axis.clear()
        
        toPlot    = self.timeSeries[:]
        currentTs = self.getCurrent()

        if currentTs is not None:
            toPlot = [currentTs] + toPlot

        if len(toPlot) == 0:
            canvas.draw()
            self.Refresh()
            return

        xlims = []
        ylims = []

        for ts in toPlot:
            xlim, ylim = self._drawTimeSeries(ts)
            xlims.append(xlim)
            ylims.append(ylim)

        # Set x/ylim
        xmin = min([lim[0] for lim in xlims])
        xmax = max([lim[1] for lim in xlims])
        ymin = min([lim[0] for lim in ylims])
        ymax = max([lim[1] for lim in ylims])

        axis.set_xlim((xmin, xmax))
        axis.set_ylim((ymin, ymax))

        canvas.draw()
        self.Refresh()


    def _drawTimeSeries(self, ts):

        display = self._displayCtx.getDisplay(ts.overlay)

        if not display.enabled:
            return None

        data = ts.data
        
        self.getAxis().plot(data, lw=2, c=ts.colour, label=ts.label)

        # TODO take into account TR
        return (0, len(data)), (data.min(), data.max())
