#!/usr/bin/env python
#
# plotcontrolpanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import wx

import props

import fsl.fslview.panel as fslpanel
import fsl.data.strings  as strings


class PlotControlPanel(fslpanel.FSLViewPanel):

    def __init__(self, parent, overlayList, displayCtx, plotPanel):

        fslpanel.FSLViewPanel.__init__(self, parent, overlayList, displayCtx)

        self.__plotPanel = plotPanel

        self.__logx      = props.makeWidget(self, plotPanel, 'xLogScale')
        self.__logy      = props.makeWidget(self, plotPanel, 'yLogScale')
        self.__smooth    = props.makeWidget(self, plotPanel, 'smooth')
        self.__legend    = props.makeWidget(self, plotPanel, 'legend')
        self.__ticks     = props.makeWidget(self, plotPanel, 'ticks')
        self.__grid      = props.makeWidget(self, plotPanel, 'grid')
        self.__autoScale = props.makeWidget(self, plotPanel, 'autoScale')
        self.__xlabel    = props.makeWidget(self, plotPanel, 'xlabel')
        self.__ylabel    = props.makeWidget(self, plotPanel, 'ylabel')

        limits           = props.makeListWidgets(self, plotPanel, 'limits')
        self.__xmin      = limits[0]
        self.__xmax      = limits[1]
        self.__ymin      = limits[2]
        self.__ymax      = limits[3]

        self.__lblLabel  = wx.StaticText(self)
        self.__xlblLabel = wx.StaticText(self)
        self.__ylblLabel = wx.StaticText(self)
        self.__xlimLabel = wx.StaticText(self)
        self.__ylimLabel = wx.StaticText(self)

        self.__logx     .SetLabel(strings.properties[plotPanel, 'xLogScale'])
        self.__logy     .SetLabel(strings.properties[plotPanel, 'yLogScale'])
        self.__smooth   .SetLabel(strings.properties[plotPanel, 'smooth'])
        self.__legend   .SetLabel(strings.properties[plotPanel, 'legend'])
        self.__ticks    .SetLabel(strings.properties[plotPanel, 'ticks'])
        self.__grid     .SetLabel(strings.properties[plotPanel, 'grid'])
        self.__autoScale.SetLabel(strings.properties[plotPanel, 'autoScale'])
        self.__xlimLabel.SetLabel(strings.labels[    self,      'xlim'])
        self.__ylimLabel.SetLabel(strings.labels[    self,      'ylim'])
        self.__lblLabel .SetLabel(strings.labels[    self,      'labels'])
        self.__xlblLabel.SetLabel(strings.labels[    self,      'xlabel'])
        self.__ylblLabel.SetLabel(strings.labels[    self,      'ylabel'])
 
        self.__sizer = wx.GridSizer(6, 3)
        self.SetSizer(self.__sizer)

        self.__xlblSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__xlblSizer.Add(self.__xlblLabel)
        self.__xlblSizer.Add(self.__xlabel, flag=wx.EXPAND, proportion=1)
        
        self.__ylblSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__ylblSizer.Add(self.__ylblLabel)
        self.__ylblSizer.Add(self.__ylabel, flag=wx.EXPAND, proportion=1) 

        self.__sizer.Add(self.__legend,    flag=wx.EXPAND)
        self.__sizer.Add(self.__ticks,     flag=wx.EXPAND)
        self.__sizer.Add(self.__grid,      flag=wx.EXPAND)
        
        self.__sizer.Add(self.__smooth,    flag=wx.EXPAND)
        self.__sizer.Add(self.__logx,      flag=wx.EXPAND)
        self.__sizer.Add(self.__logy,      flag=wx.EXPAND)

        self.__sizer.Add(self.__autoScale, flag=wx.EXPAND)
        self.__sizer.Add((-1, -1),         flag=wx.EXPAND)
        self.__sizer.Add((-1, -1),         flag=wx.EXPAND)
        
        self.__sizer.Add(self.__lblLabel,  flag=wx.EXPAND)
        self.__sizer.Add(self.__xlblSizer, flag=wx.EXPAND)
        self.__sizer.Add(self.__ylblSizer, flag=wx.EXPAND)
        
        self.__sizer.Add(self.__xlimLabel, flag=wx.EXPAND)
        self.__sizer.Add(self.__xmin,      flag=wx.EXPAND)
        self.__sizer.Add(self.__xmax,      flag=wx.EXPAND)
        
        self.__sizer.Add(self.__ylimLabel, flag=wx.EXPAND)
        self.__sizer.Add(self.__ymin,      flag=wx.EXPAND)
        self.__sizer.Add(self.__ymax,      flag=wx.EXPAND)

        self.Layout()

        plotPanel.addListener('autoScale', self._name, self.__autoScaleChanged)

        self.__autoScaleChanged()
        

    def __autoScaleChanged(self, *a):

        enableLim = not self.__plotPanel.autoScale

        self.__xlimLabel.Enable(enableLim)
        self.__ylimLabel.Enable(enableLim)
        self.__xmin     .Enable(enableLim)
        self.__xmax     .Enable(enableLim)
        self.__ymin     .Enable(enableLim)
        self.__ymax     .Enable(enableLim)
