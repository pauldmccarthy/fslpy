#!/usr/bin/env python
#
# SpacePanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import numpy               as np

import fsl.data.strings    as strings
import fsl.data.image      as fslimage
import fsl.utils.transform as transform
import                        plotpanel

class SpacePanel(plotpanel.PlotPanel):

    
    def __init__(self, parent, overlayList, displayCtx):
        plotpanel.PlotPanel.__init__(
            self, parent, overlayList, displayCtx, proj='3d')

        figure = self.getFigure()
        canvas = self.getCanvas()
        axis   = self.getAxis()

        axis.mouse_init()

        # the canvas doesn't seem to refresh itself,
        # so we'll do it manually on mouse events
        def draw(*a):
            canvas.draw()

        canvas.mpl_connect('button_press_event',   draw)
        canvas.mpl_connect('motion_notify_event',  draw)
        canvas.mpl_connect('button_release_event', draw) 

        figure.subplots_adjust(
            top=1.0, bottom=0.0, left=0.0, right=1.0)

        figure.patch.set_visible(False)

        self._overlayList.addListener('overlays', self._name,
                                      self._selectedOverlayChanged)
        self._displayCtx .addListener('selectedOverlay', self._name,
                                      self._selectedOverlayChanged)

        self._selectedOverlayChanged()


    def destroy(self):
        """De-registers property listeners."""

        plotpanel.PlotPanel.destroy(self)
        
        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)

        for overlay in self._overlayList:
            display = self._displayCtx.getDisplay(overlay)
            display.removeListener('transform', self._name)


    def _selectedOverlayChanged(self, *a):

        axis   = self.getAxis()
        canvas = self.getCanvas()

        axis.clear()

        if len(self._overlayList) == 0:
            canvas.draw()
            return

        overlay = self._displayCtx.getSelectedOverlay()
        display = self._displayCtx.getDisplay(overlay)
        opts    = display.getDisplayOpts()

        if not isinstance(overlay, fslimage.Image):
            self.message(strings.messages[self, 'nonVolumetric'])
            return

        opts.addListener('transform',
                         self._name,
                         self._selectedOverlayChanged,
                         overwrite=True)

        axis.set_title(display.name)
        axis.set_xlabel('X')
        axis.set_ylabel('Y')
        axis.set_zlabel('Z')

        self._plotOverlayCorners(overlay, opts)
        self._plotOverlayBounds( overlay, opts)
        self._plotOverlayLabels( overlay, opts)
        self._plotAxisLengths(   overlay, opts)

        axis.legend()
        canvas.draw()


    def _plotOverlayBounds(self, overlay, opts):

        v2DMat  = opts.getTransform('voxel', 'display')

        xlo, xhi = transform.axisBounds(overlay.shape, v2DMat, 0)
        ylo, yhi = transform.axisBounds(overlay.shape, v2DMat, 1)
        zlo, zhi = transform.axisBounds(overlay.shape, v2DMat, 2)

        points = np.zeros((8, 3), dtype=np.float32)
        points[0, :] = [xlo, ylo, zlo]
        points[1, :] = [xlo, ylo, zhi]
        points[2, :] = [xlo, yhi, zlo]
        points[3, :] = [xlo, yhi, zhi]
        points[4, :] = [xhi, ylo, zlo]
        points[5, :] = [xhi, ylo, zhi]
        points[6, :] = [xhi, yhi, zlo]
        points[7, :] = [xhi, yhi, zhi]

        self.getAxis().scatter(points[:, 0], points[:, 1], points[:, 2],
                               color='r', s=40)

        
    def _plotOverlayLabels(self, overlay, opts):

        axis   = self.getAxis()
        centre = np.array(overlay.shape[:3]) / 2.0

        for ax, colour in zip(range(3), ['r', 'g', 'b']):

            voxSpan = np.vstack((centre, centre))
            
            voxSpan[0, ax] = 0
            voxSpan[1, ax] = overlay.shape[ax]

            orient = overlay.getVoxelOrientation(ax)

            lblLo = strings.anatomy['Image', 'lowshort',  orient]
            lblHi = strings.anatomy['Image', 'highshort', orient]

            wldSpan = transform.transform(
                voxSpan, opts.getTransform('voxel', 'display'))

            axis.plot(wldSpan[:, 0],
                      wldSpan[:, 1],
                      wldSpan[:, 2],
                      lw=2,
                      color=colour)

            axis.text(wldSpan[0, 0], wldSpan[0, 1], wldSpan[0, 2], lblLo)
            axis.text(wldSpan[1, 0], wldSpan[1, 1], wldSpan[1, 2], lblHi)


    def _plotAxisLengths(self, overlay, opts):

        axis  = self.getAxis()
        xform = opts.getTransform('voxel', 'display')

        for ax, colour, label in zip(range(3),
                                     ['r', 'g', 'b'],
                                     ['X', 'Y', 'Z']):

            points = np.zeros((2, 3), dtype=np.float32)
            points[:]     = [-0.5, -0.5, -0.5]
            points[1, ax] = overlay.shape[ax] - 0.5

            tx    = transform.transform(points, xform)
            axlen = transform.axisLength(overlay.shape, xform, ax)

            axis.plot(tx[:, 0],
                      tx[:, 1],
                      tx[:, 2],
                      lw=1,
                      color=colour,
                      alpha=0.5,
                      label='Axis {} (length {:0.2f})'.format(label, axlen))


    def _plotOverlayCorners(self, overlay, opts):
        
        x, y, z = overlay.shape[:3]

        x = x - 0.5
        y = y - 0.5
        z = z - 0.5

        points = np.zeros((8, 3), dtype=np.float32)

        points[0, :] = [-0.5, -0.5, -0.5]
        points[1, :] = [-0.5, -0.5,  z]
        points[2, :] = [-0.5,  y,   -0.5]
        points[3, :] = [-0.5,  y,    z]
        points[4, :] = [x,    -0.5, -0.5]
        points[5, :] = [x,    -0.5,  z]
        points[6, :] = [x,     y,   -0.5]
        points[7, :] = [x,     y,    z] 

        points = transform.transform(
            points, opts.getTransform('voxel', 'display'))

        self.getAxis().scatter(points[:, 0], points[:, 1], points[:, 2],
                               color='b', s=40)
