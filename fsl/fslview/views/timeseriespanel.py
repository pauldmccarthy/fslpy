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


class TimeSeries(props.HasProperties):

    colour    = props.Colour()
    alpha     = props.Real(minval=0.0, maxval=1.0, default=1.0, clamped=True)
    label     = props.String()
    lineWidth = props.Choice((1, 2, 3, 4, 5))
    lineStyle = props.Choice(
        *zip(*[('-',  'Solid line'),
               ('--', 'Dashed line'),
               ('-.', 'Dash-dot line'),
               (':',  'Dotted line')]))

    def __init__(self, overlay, coords, data):
        self.overlay = overlay
        self.coords  = map(int, coords)
        self.data    = data


class TimeSeriesPanel(plotpanel.PlotPanel):
    """A panel with a :mod:`matplotlib` canvas embedded within.

    The volume data for each of the overlay objects in the
    :class:`.OverlayList`, at the current :attr:`.DisplayContext.location` is
    plotted on the canvas.
    """


    timeSeries = props.List()

    demean = props.Boolean(default=True)

    
    legend = props.Boolean(default=True)


    def export(self, *a):
        # Export all displayed time series to text file
        pass
    

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

        def tsChanged(*a):
            for ts in self.timeSeries:
                ts.addGlobalListener(name, draw, overwrite=True)
            draw()

        self._overlayList.addListener('overlays',        name, draw)
        self._displayCtx .addListener('selectedOverlay', name, draw) 
        self._displayCtx .addListener('location',        name, draw)
        self             .addListener('timeSeries',      name, tsChanged)

        self.Layout()
        self._draw()


    def destroy(self):
        plotpanel.PlotPanel.destroy(self)

        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._displayCtx .removeListener('location',        self._name)

        
    def getCurrent(self):

        if len(self._overlayList) == 0:
            return None

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

        ts = TimeSeries(
            overlay,
            vox,
            overlay.data[vox[0], vox[1], vox[2], :])
        ts.colour    = [0.2, 0.2, 0.2]
        ts.lineWidth = 1
        ts.lineStyle = ':'
        ts.label     = None
        return ts


    def _draw(self, *a):

        axis   = self.getAxis()
        canvas = self.getCanvas()

        axis.clear()
        
        toPlot    = self.timeSeries[:]
        currentTs = self.getCurrent()

        if currentTs is not None:
            toPlot =  [currentTs] + toPlot

        if len(toPlot) == 0:
            canvas.draw()
            self.Refresh()
            return

        xlims = []
        ylims = []

        for ts in toPlot:
            if ts is currentTs:
                xlim, ylim = self._drawTimeSeries(ts)
            else:
                xlim, ylim = self._drawTimeSeries(ts)
            xlims.append(xlim)
            ylims.append(ylim)

        # Set x/ylim
        xmin = min([lim[0] for lim in xlims])
        xmax = max([lim[1] for lim in xlims])
        ymin = min([lim[0] for lim in ylims])
        ymax = max([lim[1] for lim in ylims])

        xpad = 0.05 * (xmax - xmin)
        ypad = 0.05 * (ymax - ymin)

        axis.set_xlim((xmin - xpad, xmax + xpad))
        axis.set_ylim((ymin - ypad, ymax + ypad))

        # legend - don't show if we're only
        # plotting the current location
        if len(self.timeSeries) > 0 and self.legend:
            handles, labels = axis.get_legend_handles_labels()
            legend          = axis.legend(
                handles,
                labels,
                loc='upper right',
                fancybox=True)
            legend.get_frame().set_alpha(0.3)

        canvas.draw()
        self.Refresh()


    def _drawTimeSeries(self, ts):

        if ts.alpha == 0:
            return (0, 0), (0, 0)
        
        data = ts.data

        if self.demean:
            data = data - data.mean()

        kwargs = {}
        kwargs['lw']    = ts.lineWidth
        kwargs['alpha'] = ts.alpha
        kwargs['color'] = ts.colour
        kwargs['label'] = ts.label
        kwargs['ls']    = ts.lineStyle
        
        self.getAxis().plot(data, **kwargs)

        # TODO take into account TR
        return (0, len(data)), (data.min(), data.max())
