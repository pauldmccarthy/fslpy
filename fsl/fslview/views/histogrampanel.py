#!/usr/bin/env python
#
# histogrampanel.py - A panel which plots a histogram for the data from the
#                     currently selected image.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging


import wx

import numpy             as np
import matplotlib.pyplot as plt

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as Canvas

import props

import fsl.fslview.panel as fslpanel
import fsl.data.strings  as strings


log = logging.getLogger(__name__)

#
# Ideas:
#
#    - Plot histogram for multiple images (how to select them?)
#
#    - Ability to apply a label mask image, and plot separate
#      histograms for each label
# 
#    - Add an intensity range control which limits the range
#      of values values that are included in the histogram,
#      and which puts an overlay on the display, showing the
#      voxels that are within the range
#
#    - For 4D images, add an option to plot the histogram for
#      the current volume only, or for all volumes
#
#    - For different image types (e.g. vector), add anoption
#      to plot the histogram of calculated values, e.g.
#      magnitude, or separate histogram lines for xyz
#      components?
# 
class HistogramPanel(fslpanel.FSLViewPanel):


    histRange = props.Bounds(
        ndims=1,
        labels=[strings.choices['HistogramPanel.histRange.min'],
                strings.choices['HistogramPanel.histRange.max']])

    
    nbins = props.Int(minval=10, maxval=500, default=100)

    
    def __init__(self, parent, imageList, displayCtx):

        fslpanel.FSLViewPanel.__init__(self, parent, imageList, displayCtx)


        self._figure = plt.Figure()
        self._axis   = self._figure.add_subplot(111)
        self._canvas = Canvas(self, -1, self._figure)
        
        self._figure.subplots_adjust(
            top=1.0, bottom=0.0, left=0.0, right=1.0)

        self._figure.patch.set_visible(False)

        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self._sizer)

        import fsl.fslview.layouts as layouts
        self._configPanel = fslpanel.ConfigPanel(
            self, self, layouts.layouts[self, 'props'])
        
        self._sizer.Add(self._configPanel, flag=wx.EXPAND)
        self._sizer.Add(self._canvas,      flag=wx.EXPAND, proportion=1) 

        self._imageList.addListener(
            'images',
            self._name,
            self._selectedImageChanged) 
        self._displayCtx.addListener(
            'selectedImage',
            self._name,
            self._selectedImageChanged)


        self.addListener('histRange', self._name, self._drawPlot)
        self.addListener('nbins',     self._name, self._drawPlot)

        self.Bind(wx.EVT_WINDOW_DESTROY, self._onDestroy)

        self._selectedImageChanged()

        self.Layout()

    def _onDestroy(self, ev):
        ev.Skip()

        if ev.GetEventObject() is not self:
            return

        self._imageList .removeListener('images',        self._name)
        self._displayCtx.removeListener('selectedImage', self._name)


    def _selectedImageChanged(self, *a):

        if len(self._imageList) == 0:
            return

        image = self._displayCtx.getSelectedImage()

        minval = float(image.data.min())
        maxval = float(image.data.max())

        self.histRange.setMin(  0, minval)
        self.histRange.setMax(  0, maxval)
        self.histRange.setRange(0, minval, maxval)

        self._drawPlot()


    def _drawPlot(self, *a):

        self._axis.clear()

        image = self._displayCtx.getSelectedImage()

        hist, bins, _ = self._axis.hist(image.data.flat,
                                         bins=self.nbins,
                                         range=self.histRange.x,
                                         histtype='step')

        self._axis.grid(True)
        
        xmin = bins.min()
        xmax = bins.max()
        ymin = hist.min()
        ymax = hist.max()

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
