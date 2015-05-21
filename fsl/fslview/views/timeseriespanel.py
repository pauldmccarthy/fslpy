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

import                               plotpanel
import fsl.data.image             as fslimage
import fsl.data.strings           as strings
import fsl.fslview.displaycontext as fsldisplay
import fsl.utils.transform        as transform


log = logging.getLogger(__name__)



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
            self._selectedOverlayChanged)
        self._displayCtx.addListener(
            'selectedOverlay',
            self._name,
            self._selectedOverlayChanged) 
        self._displayCtx.addListener(
            'location',
            self._name,
            self._locationChanged)

        self.Layout()
        self._selectedOverlayChanged()


    def destroy(self):
        plotpanel.PlotPanel.destroy(self)

        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._displayCtx .removeListener('location',        self._name)

        for ovl in self._overlayList:
            opts = self._displayCtx.getOpts(ovl)

            if isinstance(opts, fsldisplay.ImageOpts):
                opts.removeListener('volume', self._name)


    def _selectedOverlayChanged(self, *a):

        overlay = self._displayCtx.getSelectedOverlay()

        for ovl in self._overlayList:

            if not isinstance(ovl, fslimage.Image):
                continue

            opts = self._displayCtx.getOpts(ovl)

            if ovl is overlay:
                opts.addListener('volume',
                                 self._name,
                                 self._locationChanged,
                                 overwrite=True)
            else:
                opts.removeListener('volume', self._name)

        self._locationChanged()
        
        
        
    def _locationChanged(self, *a):
        
        self.getAxis().clear()
        if len(self._overlayList) == 0:
            self.getCanvas().draw()
            self.Refresh()
        else:
            self._drawPlot() 


    def _drawPlot(self):

        axis    = self.getAxis()
        canvas  = self.getCanvas()
        x, y, z = self._displayCtx.location.xyz
        overlay = self._displayCtx.getSelectedOverlay()

        if not isinstance(overlay, fslimage.Image):
            self.message(strings.messages[self, 'noData'])

        elif not overlay.is4DImage():
            self.message(strings.messages[self, 'not4D'])

        else:
            opts  = self._displayCtx.getOpts(overlay)
            xform = opts.getTransform('display', 'voxel')

            vox = transform.transform([[x, y, z]], xform)[0]
            vox = np.floor(vox + 0.5)

            if vox[0] < 0                 or \
               vox[1] < 0                 or \
               vox[2] < 0                 or \
               vox[0] >= overlay.shape[0] or \
               vox[1] >= overlay.shape[1] or \
               vox[2] >= overlay.shape[2]:
                
                self.message(strings.messages[self, 'outOfBounds'])

            else:
                self._drawPlotOneOverlay(overlay, *vox)
                axis.axvline(opts.volume, c='#000080', lw=2, alpha=0.4)

        canvas.draw()
        self.Refresh()

        
    def _drawPlotOneOverlay(self, overlay, x, y, z):

        display = self._displayCtx.getDisplay(overlay)

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

        overlay = self._displayCtx.getSelectedOverlay()

        if not isinstance(overlay, fslimage.Image) or not overlay.is4DImage():
            return
        self._mouseDown = True

        opts = self._displayCtx.getOpts(overlay)
        opts.volume = np.floor(ev.xdata)
        

    def _onPlotMouseUp(self, ev):
        self._mouseDown = False

        
    def _onPlotMouseMove(self, ev):
        if not self._mouseDown:         return
        if ev.inaxes != self.getAxis(): return
        
        overlay = self._displayCtx.getSelectedOverlay()

        if not isinstance(overlay, fslimage.Image) or not overlay.is4DImage():
            return

        opts = self._displayCtx.getOpts(overlay)
        
        opts.volume = np.floor(ev.xdata)
