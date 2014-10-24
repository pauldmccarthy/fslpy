#!/usr/bin/env python
#
# SpacePanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import numpy             as np
import matplotlib.pyplot as plt

import wx

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as Canvas
from mpl_toolkits.mplot3d              import Axes3D

import fsl.fslview.viewpanel as viewpanel
import fsl.utils.transform   as transform

class SpacePanel(viewpanel.ViewPanel):

    
    def __init__(self, parent, imageList, displayCtx):
        viewpanel.ViewPanel.__init__(self, parent, imageList, displayCtx)

        self._figure = plt.Figure()
        self._canvas = Canvas(self, -1, self._figure)
        self._axis   = self._figure.add_subplot(111, projection='3d')

        self._axis.mouse_init()

        # the canvas doesn't seem to refresh itself,
        # so we'll do it manually on mouse events
        def draw(*a):
            self._canvas.draw()

        self._canvas.mpl_connect('button_press_event',   draw)
        self._canvas.mpl_connect('motion_notify_event',  draw)
        self._canvas.mpl_connect('button_release_event', draw) 

        self._figure.subplots_adjust(
            top=1.0, bottom=0.0, left=0.0, right=1.0)

        self._figure.patch.set_visible(False)

        self._imageList .addListener('images', self._name,
                                     self._selectedImageChanged)
        self._displayCtx.addListener('selectedImage', self._name,
                                     self._selectedImageChanged)

        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self._sizer)
        self._sizer.Add(self._canvas, flag=wx.EXPAND, proportion=1)

        self.Bind(wx.EVT_WINDOW_DESTROY, self._onDestroy)
        
        self._selectedImageChanged()


    def _onDestroy(self, ev):
        ev.Skip()
        self._imageList.removeListener('images',        self._name)
        self._imageList.removeListener('selectedImage', self._name)

        


    def _selectedImageChanged(self, *a):

        self._axis.clear()

        if len(self._imageList) == 0:
            self._canvas.draw()
            return

        image   = self._imageList[self._displayCtx.selectedImage]
        display = image.getAttribute('display')

        display.addListener('transform',
                            self._name,
                            self._selectedImageChanged,
                            overwrite=True)

        self._axis.set_title(image.name)
        self._axis.set_xlabel('X')
        self._axis.set_ylabel('Y')
        self._axis.set_zlabel('Z')

        self._plotImageCorners()
        self._plotImageBounds()
        self._plotImageLabels()
        self._plotAxisLengths()

        self._axis.legend()
        self._canvas.draw()


    def _plotImageBounds(self):

        image   = self._imageList[self._displayCtx.selectedImage]
        display = image.getAttribute('display')
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

        self._axis.scatter(points[:, 0], points[:, 1], points[:, 2],
                           color='r', s=40)

        
    def _plotImageLabels(self):

        # Imported here to avoid circular import issues
        import fsl.fslview.strings as strings
        
        image   = self._imageList[self._displayCtx.selectedImage]
        display = image.getAttribute('display')
        
        centre = np.array(image.shape) / 2.0

        for ax, colour in zip(range(3), ['r', 'g', 'b']):

            voxSpan = np.vstack((centre, centre))
            
            voxSpan[0, ax] = 0
            voxSpan[1, ax] = image.shape[ax]

            orient = image.getVoxelOrientation(ax)

            lblLo = strings.imageAxisLowShortLabels[ orient]
            lblHi = strings.imageAxisHighShortLabels[orient]

            wldSpan = transform.transform(voxSpan, display.voxToDisplayMat)

            self._axis.plot(wldSpan[:, 0],
                            wldSpan[:, 1],
                            wldSpan[:, 2],
                            lw=2,
                            color=colour)

            self._axis.text(wldSpan[0, 0], wldSpan[0, 1], wldSpan[0, 2], lblLo)
            self._axis.text(wldSpan[1, 0], wldSpan[1, 1], wldSpan[1, 2], lblHi)


    def _plotAxisLengths(self):

        image   = self._imageList[self._displayCtx.selectedImage]
        display = image.getAttribute('display')

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

            self._axis.plot(tx[:, 0],
                            tx[:, 1],
                            tx[:, 2],
                            lw=1,
                            color=colour,
                            alpha=0.5,
                            label='Axis {} (length {:0.2f})'.format(label,
                                                                    axlen))


    def _plotImageCorners(self):
        
        image   = self._imageList[self._displayCtx.selectedImage]
        display = image.getAttribute('display')
        
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

        self._axis.scatter(points[:, 0], points[:, 1], points[:, 2],
                           color='b', s=40)


    def _plotAllSamples(self):

        import fsl.fslview.displaycontext as dc
        from fsl.fslview.gl.glimage import genVertexData


        for zax, colour in zip(range(3), ('r', 'g', 'b')):

            image = self._imageList[self._displayCtx.selectedImage]

            disp = dc.ImageDisplay(image)

            disp.worldResolution *= 2
            disp.voxelResolution *= 2

            dims = range(3)
            dims.pop(zax)
            xax = dims[0]
            yax = dims[1] 

            worldCoords, texCoords = genVertexData(image, disp, xax, yax)

            worldX = worldCoords[:, xax]
            worldY = worldCoords[:, yax]

            zlo, zhi = image.imageBounds(zax)
            zmid     = zlo + (zhi - zlo) / 2.0

            worldCoords      = [None] * 3
            worldCoords[xax] = worldX
            worldCoords[yax] = worldY
            worldCoords[zax] = np.repeat(zmid, len(worldX))

            vertices  = np.vstack(worldCoords)

            self._axis.scatter(vertices[0, :], vertices[1, :], vertices[2, :],
                               s=5, alpha=0.4, c=colour)
