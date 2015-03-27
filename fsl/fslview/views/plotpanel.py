#!/usr/bin/env python
#
# plotpanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import matplotlib as mpl

mpl.use('WxAgg')

import matplotlib.pyplot as plt

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as Canvas
from mpl_toolkits.mplot3d import Axes3D

import                     viewpanel
import fsl.data.strings as strings


log = logging.getLogger(__name__)


class PlotPanel(viewpanel.ViewPanel):
    def __init__(self, parent, imageList, displayCtx, actionz=None, proj=None):
        
        if actionz is None:
            actionz = {}

        actionz = dict([('screenshot', self.screenshot)] + actionz.items())
        
        viewpanel.ViewPanel.__init__(
            self, parent, imageList, displayCtx, actionz)

        # There is currently no screenshot functionality
        # because I haven't gotten around to implementing
        # it ...
        self.disable('screenshot')

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
        pass
