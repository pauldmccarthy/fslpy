#!/usr/bin/env python
#
# plotpanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import                      wx
import wx.lib.agw.aui    as aui
import matplotlib        as mpl

mpl.use('WxAgg')

import matplotlib.pyplot as plt

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as Canvas
from mpl_toolkits.mplot3d import Axes3D

import fsl.fslview.panel as fslpanel
import fsl.data.strings  as strings


log = logging.getLogger(__name__)


class PlotPanel(fslpanel.FSLViewPanel):
    def __init__(self, parent, imageList, displayCtx, actionz=None, proj=None):
        
        if actionz is None:
            actionz = {}

        actionz = dict([('screenshot', self.screenshot)] + actionz.items())
        
        fslpanel.FSLViewPanel.__init__(
            self, parent, imageList, displayCtx, actionz)

        self.__figure = plt.Figure()
        self.__axis   = self.__figure.add_subplot(111, projection=proj)
        self.__canvas = Canvas(self, -1, self.__figure) 
        
        self.__auiMgr = aui.AuiManager(self, agwFlags=(
            aui.AUI_MGR_ALLOW_FLOATING)) 
        self.__auiMgr.AddPane(self.__canvas, wx.CENTRE)
        self.__auiMgr.Update()

        self.__controlPanels = {}



    # TODO All of this AUI rubbish should go
    # into a 'ViewPanel' superclass, from
    # which PlotPanel and CanvasPanel inherit.
    def toggleControlPanel(self, panelType, floatPane=False, *args, **kwargs):

        window = panelType(
            self, self._imageList, self._displayCtx, *args, **kwargs)
        
        paneInfo = aui.AuiPaneInfo()        \
            .MinSize(window.GetMinSize())   \
            .BestSize(window.GetBestSize()) \
            .Caption(strings.titles[window])

        if isinstance(window, fslpanel.FSLViewToolBar):
            paneInfo = paneInfo.ToolbarPane()

        if floatPane is False: paneInfo.Top()
        else:                  paneInfo.Float()
                
        self.__auiMgr.AddPane(window, paneInfo)
        self.__auiMgr.Update()

        
    def destroy(self):
        fslpanel.FSLViewPanel.destroy(self)


    def getFigure(self):
        return self.__figure
    

    def getAxis(self):
        return self.__axis


    def getCanvas(self):
        return self.__canvas

        
    def screenshot(self, *a):
        pass
