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

import                               wx
import numpy                      as np

import                               props

import                               plotpanel
import fsl.data.image             as fslimage
import fsl.fslview.displaycontext as fsldisplay
import fsl.fslview.controls       as fslcontrols
import fsl.utils.transform        as transform


log = logging.getLogger(__name__)


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

    demean    = props.Boolean(default=True)
    legend    = props.Boolean(default=True)
    usePixdim = props.Boolean(default=False)
    autoScale = props.Boolean(default=True)
    xLogScale = props.Boolean(default=False)
    yLogScale = props.Boolean(default=False) 
    ticks     = props.Boolean(default=True)
    grid      = props.Boolean(default=True)
    xlabel    = props.String()
    ylabel    = props.String()
    xmin      = props.Real()
    xmax      = props.Real()
    ymin      = props.Real()
    ymax      = props.Real()


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
        
        displayCtx .addListener('selectedOverlay', self._name, self._draw) 
        displayCtx .addListener('location',        self._name, self._draw)
        
        self.addGlobalListener(self._name, self.__propChanged)

        self.Bind(wx.EVT_SIZE, self._draw)

        self.Layout()
        self._draw()


    def destroy(self):
        plotpanel.PlotPanel.destroy(self)

        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._displayCtx .removeListener('location',        self._name)


    def __propChanged(self, value, valid, ctx, name):

        if name == 'timeSeries':
            for ts in self.timeSeries:
                ts.addGlobalListener(self._name, self._draw, overwrite=True)
        self._draw()
        

    def __overlaysChanged(self, *a):

        for ts in self.timeSeries[:]:
            if ts.overlay not in self._overlayList:
                self.timeSeries.remove(ts)
        self._draw()

        
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

        ts = TimeSeries(
            overlay,
            vox,
            overlay.data[vox[0], vox[1], vox[2], :])
        ts.colour    = [0.2, 0.2, 0.2]
        ts.lineWidth = 1
        ts.lineStyle = ':'
        ts.label     = None

        self.__current = ts

        
    def getCurrent(self):
        return self.__current


    def __calcLimits(self, xlims, ylims):

        if self.autoScale:
            xmin = min([lim[0] for lim in xlims])
            xmax = max([lim[1] for lim in xlims])
            ymin = min([lim[0] for lim in ylims])
            ymax = max([lim[1] for lim in ylims])
        else:
            xmin = self.xmin
            xmax = self.xmax
            ymin = self.ymin
            ymax = self.ymax

        for prop in ['xmin', 'xmax', 'ymin', 'ymax']:
            self.disableListener(prop, self._name)
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        for prop in ['xmin', 'xmax', 'ymin', 'ymax']:
            self.enableListener(prop, self._name)

        return (xmin, xmax), (ymin, ymax)



    def _draw(self, *a):

        self.__calcCurrent()

        axis          = self.getAxis()
        canvas        = self.getCanvas()
        width, height = canvas.get_width_height()

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

        if self.xLogScale: axis.set_xscale('log')
        else:              axis.set_xscale('linear')
        if self.yLogScale: axis.set_yscale('log')
        else:              axis.set_yscale('linear')

        xlim, ylim = self.__calcLimits(xlims, ylims)

        bPad = (ylim[1] - ylim[0]) * (50.0 / height)
        tPad = (ylim[1] - ylim[0]) * (20.0 / height)
        lPad = (xlim[1] - xlim[0]) * (50.0 / width)
        rPad = (xlim[1] - xlim[0]) * (20.0 / width)

        axis.set_xlim((xlim[0] - lPad, xlim[1] + rPad))
        axis.set_ylim((ylim[0] - bPad, ylim[1] + tPad))

        xlabel = self.xlabel 
        ylabel = self.ylabel

        if xlabel is None: xlabel = ''
        if ylabel is None: ylabel = ''

        xlabel = xlabel.strip()
        ylabel = ylabel.strip()

        if xlabel != '':
            axis.set_xlabel(self.xlabel, va='bottom')
            axis.xaxis.set_label_coords(0.5, 10.0 / height)
            
        if ylabel != '':
            axis.set_ylabel(self.ylabel, va='top')
            axis.yaxis.set_label_coords(10.0 / width, 0.5)

        if self.ticks:
            xticks = np.linspace(xlim[0], xlim[1], 4)
            yticks = np.linspace(ylim[0], ylim[1], 4)

            axis.tick_params(direction='in', pad=-5)

            axis.set_xticks(xticks)
            axis.set_yticks(yticks)

            for ytl in axis.yaxis.get_ticklabels():
                ytl.set_horizontalalignment('left')
                
            for xtl in axis.xaxis.get_ticklabels():
                xtl.set_verticalalignment('bottom')
        else:
            axis.set_xticks([])
            axis.set_yticks([])

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


        if self.grid:
            axis.grid()

        canvas.draw()
        self.Refresh()


    def _drawTimeSeries(self, ts):

        if ts.alpha == 0:
            return (0, 0), (0, 0)
        
        ydata = ts.data

        if self.demean:
            ydata = ydata - ydata.mean()

        if self.usePixdim: xdata = np.arange(len(ydata)) * ts.overlay.pixdim[3]
        else:              xdata = np.arange(len(ydata))

        kwargs = {}
        kwargs['lw']    = ts.lineWidth
        kwargs['alpha'] = ts.alpha
        kwargs['color'] = ts.colour
        kwargs['label'] = ts.label
        kwargs['ls']    = ts.lineStyle
        
        self.getAxis().plot(xdata, ydata, **kwargs)

        return ((xdata.min(), xdata.max()), 
                (ydata.min(), ydata.max()))
