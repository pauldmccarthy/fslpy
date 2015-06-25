#!/usr/bin/env python
#
# plotpanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import wx

import matplotlib as mpl
import numpy      as np


mpl.use('WxAgg')


import matplotlib.pyplot as plt
import matplotlib.image  as mplimg

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as Canvas
from mpl_toolkits.mplot3d              import Axes3D

import                     viewpanel
import fsl.data.strings as strings


log = logging.getLogger(__name__)


class PlotPanel(viewpanel.ViewPanel):
    def __init__(self,
                 parent,
                 overlayList,
                 displayCtx,
                 actionz=None,
                 proj=None):
        
        if actionz is None:
            actionz = {}

        actionz = dict([('screenshot', self.screenshot)] + actionz.items())
        
        viewpanel.ViewPanel.__init__(
            self, parent, overlayList, displayCtx, actionz)

        # There is currently no screenshot functionality
        # because I haven't gotten around to implementing
        # it ...
        # self.disable('screenshot')

        self.__figure = plt.Figure()
        self.__axis   = self.__figure.add_subplot(111, projection=proj)
        self.__canvas = Canvas(self, -1, self.__figure) 

        self.setCentrePanel(self.__canvas)

        
    def destroy(self):
        viewpanel.ViewPanel.destroy(self)


    def getFigure(self):
        return self.__figure
    

    def getAxis(self):
        return self.__axis


    def getCanvas(self):
        return self.__canvas

        
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
