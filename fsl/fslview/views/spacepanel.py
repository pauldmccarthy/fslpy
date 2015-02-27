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
import fsl.utils.transform as transform
import                        plotpanel

class SpacePanel(plotpanel.PlotPanel):

    
    def __init__(self, parent, imageList, displayCtx):
        plotpanel.PlotPanel.__init__(self, parent, imageList, displayCtx, '3d')

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

        self._imageList .addListener('images', self._name,
                                     self._selectedImageChanged)
        self._displayCtx.addListener('selectedImage', self._name,
                                     self._selectedImageChanged)

        self._selectedImageChanged()


    def destroy(self):
        """De-registers property listeners."""

        plotpanel.PlotPanel.destroy(self)
        
        self._imageList .removeListener('images',        self._name)
        self._displayCtx.removeListener('selectedImage', self._name)

        for image in self._imageList:
            display = self._displayCtx.getDisplayProperties(image)
            display.removeListener('transform', self._name)


    def _selectedImageChanged(self, *a):

        axis   = self.getAxis()
        canvas = self.getCanvas()

        axis.clear()

        if len(self._imageList) == 0:
            canvas.draw()
            return

        image   = self._displayCtx.getSelectedImage()
        display = self._displayCtx.getDisplayProperties(image)

        display.addListener('transform',
                            self._name,
                            self._selectedImageChanged,
                            overwrite=True)

        axis.set_title(image.name)
        axis.set_xlabel('X')
        axis.set_ylabel('Y')
        axis.set_zlabel('Z')

        self._plotImageCorners()
        self._plotImageBounds()
        self._plotImageLabels()
        self._plotAxisLengths()

        axis.legend()
        canvas.draw()


    def _plotImageBounds(self):

        image   = self._displayCtx.getSelectedImage()
        display = self._displayCtx.getDisplayProperties(image)
        v2DMat  = display.voxToDisplayMat

        xlo, xhi = transform.axisBounds(image.shape, v2DMat, 0)
        ylo, yhi = transform.axisBounds(image.shape, v2DMat, 1)
        zlo, zhi = transform.axisBounds(image.shape, v2DMat, 2)

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

        
    def _plotImageLabels(self):

        axis    = self.getAxis()
        image   = self._displayCtx.getSelectedImage()
        display = self._displayCtx.getDisplayProperties(image)
        
        centre = np.array(image.shape) / 2.0

        for ax, colour in zip(range(3), ['r', 'g', 'b']):

            voxSpan = np.vstack((centre, centre))
            
            voxSpan[0, ax] = 0
            voxSpan[1, ax] = image.shape[ax]

            orient = image.getVoxelOrientation(ax)

            lblLo = strings.anatomy['Image', 'lowshort',  orient]
            lblHi = strings.anatomy['Image', 'highshort', orient]

            wldSpan = transform.transform(voxSpan, display.voxToDisplayMat)

            axis.plot(wldSpan[:, 0],
                      wldSpan[:, 1],
                      wldSpan[:, 2],
                      lw=2,
                      color=colour)

            axis.text(wldSpan[0, 0], wldSpan[0, 1], wldSpan[0, 2], lblLo)
            axis.text(wldSpan[1, 0], wldSpan[1, 1], wldSpan[1, 2], lblHi)


    def _plotAxisLengths(self):

        axis    = self.getAxis()
        image   = self._displayCtx.getSelectedImage()
        display = self._displayCtx.getDisplayProperties(image)

        for ax, colour, label in zip(range(3),
                                     ['r', 'g', 'b'],
                                     ['X', 'Y', 'Z']):

            points = np.zeros((2, 3), dtype=np.float32)
            points[:]     = [-0.5, -0.5, -0.5]
            points[1, ax] = image.shape[ax] - 0.5

            tx = transform.transform(points, display.voxToDisplayMat)

            axlen = transform.axisLength(image.shape,
                                         display.voxToDisplayMat,
                                         ax)

            axis.plot(tx[:, 0],
                      tx[:, 1],
                      tx[:, 2],
                      lw=1,
                      color=colour,
                      alpha=0.5,
                      label='Axis {} (length {:0.2f})'.format(label, axlen))


    def _plotImageCorners(self):
        
        image   = self._displayCtx.getSelectedImage()
        display = self._displayCtx.getDisplayProperties(image)
        
        x, y, z = image.shape[:3]

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

        points = transform.transform(points, display.voxToDisplayMat)

        self.getAxis().scatter(points[:, 0], points[:, 1], points[:, 2],
                               color='b', s=40)
