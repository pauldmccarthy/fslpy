#!/usr/bin/env python
#
# timeserieslistpanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import wx

import pwidgets.elistbox      as elistbox
import fsl.fslview.panel      as fslpanel
import fsl.fslview.colourmaps as fslcm


class TimeSeriesListPanel(fslpanel.FSLViewPanel):

    def __init__(self, parent, overlayList, displayCtx, timeSeriesPanel):

        fslpanel.FSLViewPanel.__init__(self, parent, overlayList, displayCtx)

        self.__tsPanel      = timeSeriesPanel
        self.__currentLabel = wx.StaticText(           self)
        self.__tsList       = elistbox.EditableListBox(self)

        self.__sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.__sizer)

        self.__sizer.Add(self.__currentLabel, flag=wx.EXPAND)
        self.__sizer.Add(self.__tsList,       flag=wx.EXPAND, proportion=1)


        displayCtx .addListener('selectedOverlay',
                                self._name,
                                self.__locationChanged)
        overlayList.addListener('overlays',
                                self._name,
                                self.__locationChanged)

        self.Layout()

        
    def destroy(self):
        fslpanel.FSLViewPanel.destroy(self)
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._overlayList.removeListener('overlays',        self._name)


    def __locationChanged(self, *a):
        pass

    
    def __onListAdd(self, ev):
        
        ts = self.__tsPanel.getCurrent()

        ts.colour = fslcm.randomColour()

        self.__tsPanel.timeSeries.append(ts)
    
