#!/usr/bin/env python
#
# plotpanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import wx

import matplotlib        as mpl
import numpy             as np
import scipy.interpolate as interp


mpl.use('WxAgg')

import matplotlib.pyplot as plt
import matplotlib.image  as mplimg

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as Canvas
from mpl_toolkits.mplot3d              import Axes3D

import                     props
import                     viewpanel
import fsl.data.strings as strings


log = logging.getLogger(__name__)


class DataSeries(props.HasProperties):

    colour    = props.Colour()
    alpha     = props.Real(minval=0.0, maxval=1.0, default=1.0, clamped=True)
    label     = props.String()
    lineWidth = props.Choice((0.5, 1, 2, 3, 4, 5))
    lineStyle = props.Choice(
        *zip(*[('-',  'Solid line'),
               ('--', 'Dashed line'),
               ('-.', 'Dash-dot line'),
               (':',  'Dotted line')]))

    
    def __init__(self, overlay):
        self.overlay = overlay


    def getData(self):
        raise NotImplementedError('The getData method must be '
                                  'implemented by subclasses')


class PlotPanel(viewpanel.ViewPanel):


    dataSeries = props.List()
    legend     = props.Boolean(default=True)
    autoScale  = props.Boolean(default=True)
    xLogScale  = props.Boolean(default=False)
    yLogScale  = props.Boolean(default=False) 
    ticks      = props.Boolean(default=True)
    grid       = props.Boolean(default=True)
    smooth     = props.Boolean(default=False)
    xlabel     = props.String()
    ylabel     = props.String()
    limits     = props.Bounds(ndims=2)


    def importDataSeries(self, *a):
        # TODO import data series from text file
        pass


    def exportDataSeries(self, *a):
        # TODO export all displayed data series to text file
        pass
    
    
    def __init__(self,
                 parent,
                 overlayList,
                 displayCtx,
                 actionz=None,
                 proj=None,
                 interactive=True):
        
        if actionz is None:
            actionz = {}

        actionz = dict([('screenshot', self.screenshot)] + actionz.items())
        
        viewpanel.ViewPanel.__init__(
            self, parent, overlayList, displayCtx, actionz)

        figure = plt.Figure()
        axis   = figure.add_subplot(111, projection=proj)
        canvas = Canvas(self, -1, figure) 

        self.setCentrePanel(canvas)

        self.__figure          = figure
        self.__axis            = axis
        self.__canvas          = canvas
        self.__zoomMode        = False
        self.__mouseDown       = None
        self.__mouseDownLimits = None

        if interactive:
            canvas.mpl_connect('button_press_event',   self.__onMouseDown)
            canvas.mpl_connect('button_release_event', self.__onMouseUp)
            canvas.mpl_connect('motion_notify_event',  self.__onMouseMove)

        self.__name = '{}_{}'.format(type(self).__name__, self._name)
        self.addListener('dataSeries', self.__name, self.__dataSeriesChanged)

        self.Bind(wx.EVT_SIZE, lambda *a: self.draw())


    def draw(self, *a):
        raise NotImplementedError('The draw method must be '
                                  'implemented by PlotPanel subclasses')


    def __dataSeriesChanged(self, *a):
        for ds in self.dataSeries:
            ds.addGlobalListener(self.__name, self.draw, overwrite=True)

        
    def destroy(self):
        viewpanel.ViewPanel.destroy(self)
        self.removeGlobalListener(self.__name)


    def getFigure(self):
        return self.__figure
    

    def getAxis(self):
        return self.__axis


    def getCanvas(self):
        return self.__canvas


    def __calcLimits(self, xlims, ylims):

        xmin = min([lim[0] for lim in xlims])
        xmax = max([lim[1] for lim in xlims])
        ymin = min([lim[0] for lim in ylims])
        ymax = max([lim[1] for lim in ylims])

        if (self.autoScale and self.__mouseDown is None):
            
            self.disableListener('limits', self._name)
            self.limits[:] = [xmin, xmax, ymin, ymax]
            self.enableListener('limits', self._name)            

        else:
            xmin = self.limits.xlo
            xmax = self.limits.xhi
            ymin = self.limits.ylo
            ymax = self.limits.yhi
            
        return (xmin, xmax), (ymin, ymax)


    def drawDataSeries(self, extraSeries=None, **plotArgs):

        if extraSeries is None:
            extraSeries = []

        axis          = self.getAxis()
        canvas        = self.getCanvas()
        width, height = canvas.get_width_height()

        axis.clear()

        toPlot = self.dataSeries[:]
        toPlot = extraSeries + toPlot

        if len(toPlot) == 0:
            canvas.draw()
            self.Refresh()
            return

        xlims = []
        ylims = []

        for ds in toPlot:
            xlim, ylim = self.__drawOneDataSeries(ds, **plotArgs)
            xlims.append(xlim)
            ylims.append(ylim)

        (xmin, xmax), (ymin, ymax) = self.__calcLimits(xlims, ylims)

        if xmax - xmin < 0.0000000001 or \
           ymax - ymin < 0.0000000001:
            axis.clear()
            canvas.draw()
            self.Refresh()
            return

        # x/y axis labels
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

        # Ticks
        if self.ticks:
            xticks = np.linspace(xmin, xmax, 4)
            yticks = np.linspace(ymin, ymax, 4)

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

        # Limits
        bPad = (ymax - ymin) * (50.0 / height)
        tPad = (ymax - ymin) * (50.0 / height)
        lPad = (xmax - xmin) * (50.0 / width)
        rPad = (xmax - xmin) * (50.0 / width)
        
        axis.set_xlim((xmin - lPad, xmax + rPad))
        axis.set_ylim((ymin - bPad, ymax + tPad))

        # legend
        labels = [ds.label for ds in toPlot if ds.label is not None]
        if len(labels) > 0 and self.legend:
            handles, labels = axis.get_legend_handles_labels()
            legend          = axis.legend(
                handles,
                labels,
                loc='upper right',
                fancybox=True)
            legend.get_frame().set_alpha(0.6)

        if self.grid:
            axis.grid()

        canvas.draw()
        self.Refresh()


    def __drawOneDataSeries(self, ds, **plotArgs):

        if ds.alpha == 0:
            return (0, 0), (0, 0)

        log.debug('Drawing plot for {}'.format(ds.overlay))

        xdata, ydata = ds.getData()

        if len(xdata) != len(ydata) or len(xdata) == 0:
            return (0, 0), (0, 0)

        # Note to self: If the smoothed data is
        # filled with NaNs, it is possibly due
        # to duplicate values in the x data, which
        # are not handled very well by splrep.
        if self.smooth:

            tck   = interp.splrep(xdata, ydata)
            xdata = np.linspace(xdata[0],
                                xdata[-1],
                                len(xdata) * 5,
                                dtype=np.float32)
            ydata = interp.splev(xdata, tck)

        if self.xLogScale: xdata = np.log10(xdata)
        if self.yLogScale: ydata = np.log10(ydata)

        nans = ~(np.isfinite(xdata) & np.isfinite(ydata))

        xdata[nans] = np.nan
        ydata[nans] = np.nan

        if np.all(np.isnan(xdata) | np.isnan(ydata)):
            return (0, 0), (0, 0)

        kwargs = plotArgs
        kwargs['lw']    = kwargs.get('lw',    ds.lineWidth)
        kwargs['alpha'] = kwargs.get('alpha', ds.alpha)
        kwargs['color'] = kwargs.get('color', ds.colour)
        kwargs['label'] = kwargs.get('label', ds.label)
        kwargs['ls']    = kwargs.get('ls',    ds.lineStyle)

        self.getAxis().plot(xdata, ydata, **kwargs)

        return ((np.nanmin(xdata), np.nanmax(xdata)),
                (np.nanmin(ydata), np.nanmax(ydata)))


    def __onMouseDown(self, ev):

        axis = self.getAxis()
        
        if ev.inaxes != axis:
            return

        if ev.key == 'shift': self.__zoomMode = True
        else:                 self.__zoomMode = False

        self.__mouseDown       = ev.xdata, ev.ydata
        self.__mouseDownLimits = (self.limits.x, self.limits.y)

    
    def __onMouseUp(self, ev):
        self.__mouseDown = None

        
    def __onMouseMove(self, ev):

        axis = self.getAxis()

        if self.__mouseDown is None: return
        if ev.inaxes != axis:        return

        if self.__zoomMode: newxlim, newylim = self.__zoomLimits(ev)
        else:               newxlim, newylim = self.__panLimits( ev)
        
        self.disableListener('limits', self._name)
        self.limits[:] = newxlim + newylim
        self.enableListener('limits', self._name)

        self.draw()
            

    def __zoomLimits(self, ev):

        xlim, ylim = self.__mouseDownLimits

        xlen = xlim[1] - xlim[0]
        ylen = ylim[1] - ylim[0]

        xmid = xlim[0] + 0.5 * xlen
        ymid = ylim[0] + 0.5 * ylen

        mdx, mdy = self.__mouseDown
        evx, evy = ev.xdata, ev.ydata

        mdx = (mdx - xlim[0]) / xlen
        mdy = (mdy - ylim[0]) / ylen
        
        evx = (evx - self.limits.xlo) / self.limits.xlen
        evy = (evy - self.limits.ylo) / self.limits.ylen

        xdist = 2 * xlen * (evx - mdx)
        ydist = 2 * ylen * (evy - mdy)

        newxlen = abs(xlen - xdist)
        newylen = abs(ylen - ydist)

        newxlim = [xmid - newxlen * 0.5, xmid + newxlen * 0.5]
        newylim = [ymid - newylen * 0.5, ymid + newylen * 0.5]

        return newxlim, newylim

    
    def __panLimits(self, mouseEv):

        xdist = self.__mouseDown[0] - mouseEv.xdata
        ydist = self.__mouseDown[1] - mouseEv.ydata

        return ((self.limits.xlo + xdist, self.limits.xhi + xdist),
                (self.limits.ylo + ydist, self.limits.yhi + ydist))

        
    def screenshot(self, *a):

        dlg = wx.FileDialog(self,
                            message=strings.messages[self, 'screenshot'],
                            style=wx.FD_SAVE)

        if dlg.ShowModal() != wx.ID_OK:
            return

        path = dlg.GetPath()

        buf          = self.__canvas.tostring_argb()
        ncols, nrows = self.__canvas.get_width_height()

        bitmap = np.fromstring(buf, dtype=np.uint8)
        bitmap = bitmap.reshape(nrows, ncols, 4)

        rgb    = bitmap[:, :, 1:]
        a      = bitmap[:, :, 0]
        bitmap = np.dstack((rgb, a))

        mplimg.imsave(path, bitmap)


    def message(self, msg):

        axis = self.getAxis()
        axis.clear()
        axis.set_xlim((0.0, 1.0))
        axis.set_ylim((0.0, 1.0))

        if isinstance(axis, Axes3D):
            axis.text(0.5, 0.5, 0.5, msg, ha='center', va='center')
        else:
            axis.text(0.5, 0.5, msg, ha='center', va='center')
        
        self.getCanvas().draw()
        self.Refresh() 
