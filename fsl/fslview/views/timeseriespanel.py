#!/usr/bin/env python
#
# timeseriespanel.py - A panel which plots time series/volume data from a
# collection of images.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""A :class:`wx.Panel` which plots time series/volume data from a
collection of :class:`~fsl.data.image.Image` objects stored in an
:class:`~fsl.data.image.ImageList`.

:mod:`matplotlib` is used for plotting.
"""

import logging
log = logging.getLogger(__name__)

import wx
import numpy      as np
import matplotlib as mpl

mpl.use('WXAgg')

import matplotlib.pyplot as plt
from   matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as Canvas

import fsl.fslview.panel   as fslpanel
import fsl.utils.transform as transform


class TimeSeriesPanel(fslpanel.FSLViewPanel):
    """A panel with a :mod:`matplotlib` canvas embedded within.

    The volume data for each of the :class:`~fsl.data.image.Image`
    objects in the :class:`~fsl.data.image.ImageList`, at the current
    :attr:`~fsl.data.image.ImageList.location` is plotted on the canvas.
    """

    def __init__(self, parent, imageList, displayCtx):

        fslpanel.FSLViewPanel.__init__(self, parent, imageList, displayCtx)

        self._figure = plt.Figure()
        self._axis   = self._figure.add_subplot(111)
        self._canvas = Canvas(self, -1, self._figure)

        self._figure.subplots_adjust(
            top=1.0, bottom=0.0, left=0.0, right=1.0)

        self._figure.patch.set_visible(False)

        self._mouseDown = False
        self._canvas.mpl_connect('button_press_event',   self._onPlotMouseDown)
        self._canvas.mpl_connect('button_release_event', self._onPlotMouseUp)
        self._canvas.mpl_connect('motion_notify_event',  self._onPlotMouseMove)

        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self._sizer)
        self._sizer.Add(self._canvas, flag=wx.EXPAND, proportion=1)

        self._displayCtx.addListener(
            'selectedImage',
            self._name,
            self._selectedImageChanged)
        self._displayCtx.addListener(
            'location',
            self._name,
            self._locationChanged)
        self._displayCtx.addListener(
            'volume',
            self._name,
            self._locationChanged) 

        def onDestroy(ev):
            ev.Skip()
            self._displayCtx.removeListener('selectedImage', self._name)
            self._displayCtx.removeListener('location',      self._name)
            self._displayCtx.removeListener('volume',        self._name)

        self.Bind(wx.EVT_WINDOW_DESTROY, onDestroy)

        self._selectedImageChanged()
        
        self.Layout()

        
    def _selectedImageChanged(self, *a):
        
        self._axis.clear()

        if len(self._imageList) == 0:
            return

        image = self._displayCtx.getSelectedImage()

        if not image.is4DImage():
            return

        self._drawPlot()

        
    def _locationChanged(self, *a):
        
        self._axis.clear()

        if len(self._imageList) == 0:
            return 
        
        image = self._displayCtx.getSelectedImage()

        if not image.is4DImage():
            return

        self._drawPlot() 



    def _drawPlot(self):

        x, y, z = self._displayCtx.location.xyz
        vol     = self._displayCtx.volume

        mins = []
        maxs = []
        vols = []

        for image in self._imageList:

            display = self._displayCtx.getDisplayProperties(image)
            xform   = display.displayToVoxMat

            ix, iy, iz = transform.transform([[x, y, z]], xform)[0]

            ix = round(ix)
            iy = round(iy)
            iz = round(iz)

            minmaxvol = self._drawPlotOneImage(image, ix, iy, iz)

            if minmaxvol is not None:
                mins.append(minmaxvol[0])
                maxs.append(minmaxvol[1])
                vols.append(minmaxvol[2])

        self._axis.axvline(vol, c='#000080', lw=2, alpha=0.4)


        if len(mins) > 0:

            xmin = 0
            xmax = max(vols) - 1
            ymin = min(mins)
            ymax = max(maxs)

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

        self._canvas.draw()
        self.Refresh()

        
    def _drawPlotOneImage(self, image, x, y, z):

        display = self._displayCtx.getDisplayProperties(image)

        if not image.is4DImage(): return None
        if not display.enabled:   return None

        for vox, shape in zip((x, y, z), image.shape):
            if vox >= shape or vox < 0:
                return None

        data = image.data[x, y, z, :]
        self._axis.plot(data, lw=2)

        return data.min(), data.max(), len(data)


    def _onPlotMouseDown(self, ev):
        if ev.inaxes != self._axis: return
        self._mouseDown = True
        self._displayCtx.volume = np.floor(ev.xdata)
        

    def _onPlotMouseUp(self, ev):
        self._mouseDown = False

        
    def _onPlotMouseMove(self, ev):
        if not self._mouseDown:     return
        if ev.inaxes != self._axis: return
        self._displayCtx.volume = np.floor(ev.xdata)
