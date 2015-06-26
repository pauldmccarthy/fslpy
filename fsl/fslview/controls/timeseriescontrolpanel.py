#!/usr/bin/env python
#
# timeseriescontrolpanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import wx

import props

import fsl.fslview.panel as fslpanel
import fsl.data.strings  as strings


class TimeSeriesControlPanel(fslpanel.FSLViewPanel):

    def __init__(self, parent, overlayList, displayCtx, tsPanel):

        fslpanel.FSLViewPanel.__init__(self, parent, overlayList, displayCtx)

        self.__tsPanel   = tsPanel

        self.__demean    = props.makeWidget(self, tsPanel, 'demean')
        self.__usePixdim = props.makeWidget(self, tsPanel, 'usePixdim')
        self.__logx      = props.makeWidget(self, tsPanel, 'xLogScale')
        self.__logy      = props.makeWidget(self, tsPanel, 'yLogScale')
        self.__smooth    = props.makeWidget(self, tsPanel, 'smooth')
        self.__legend    = props.makeWidget(self, tsPanel, 'legend')
        self.__ticks     = props.makeWidget(self, tsPanel, 'ticks')
        self.__grid      = props.makeWidget(self, tsPanel, 'grid')
        self.__autoScale = props.makeWidget(self, tsPanel, 'autoScale')

        self.__xlabel    = props.makeWidget(self, tsPanel, 'xlabel')
        self.__ylabel    = props.makeWidget(self, tsPanel, 'ylabel')

        self.__xmin      = props.makeWidget(self, tsPanel, 'xmin')
        self.__xmax      = props.makeWidget(self, tsPanel, 'xmax')
        self.__ymin      = props.makeWidget(self, tsPanel, 'ymin')
        self.__ymax      = props.makeWidget(self, tsPanel, 'ymax')

        self.__lblLabel  = wx.StaticText(self)
        self.__xlblLabel = wx.StaticText(self)
        self.__ylblLabel = wx.StaticText(self)
        self.__xlimLabel = wx.StaticText(self)
        self.__ylimLabel = wx.StaticText(self)

        self.__demean   .SetLabel(strings.properties[tsPanel, 'demean'])
        self.__usePixdim.SetLabel(strings.properties[tsPanel, 'usePixdim'])
        self.__logx     .SetLabel(strings.properties[tsPanel, 'xLogScale'])
        self.__logy     .SetLabel(strings.properties[tsPanel, 'yLogScale'])
        self.__smooth   .SetLabel(strings.properties[tsPanel, 'smooth'])
        self.__legend   .SetLabel(strings.properties[tsPanel, 'legend'])
        self.__ticks    .SetLabel(strings.properties[tsPanel, 'ticks'])
        self.__grid     .SetLabel(strings.properties[tsPanel, 'grid'])
        self.__autoScale.SetLabel(strings.properties[tsPanel, 'autoScale'])
        self.__xlimLabel.SetLabel(strings.labels[    self,    'xlim'])
        self.__ylimLabel.SetLabel(strings.labels[    self,    'ylim'])
        self.__lblLabel .SetLabel(strings.labels[    self,    'labels'])
        self.__xlblLabel.SetLabel(strings.labels[    self,    'xlabel'])
        self.__ylblLabel.SetLabel(strings.labels[    self,    'ylabel'])
 
        self.__sizer = wx.GridSizer(6, 3)
        self.SetSizer(self.__sizer)

        self.__xlblSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__xlblSizer.Add(self.__xlblLabel)
        self.__xlblSizer.Add(self.__xlabel, flag=wx.EXPAND, proportion=1)
        
        self.__ylblSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__ylblSizer.Add(self.__ylblLabel)
        self.__ylblSizer.Add(self.__ylabel, flag=wx.EXPAND, proportion=1) 

        self.__sizer.Add(self.__demean,    flag=wx.EXPAND)
        self.__sizer.Add(self.__usePixdim, flag=wx.EXPAND)
        self.__sizer.Add(self.__smooth,    flag=wx.EXPAND)
        
        self.__sizer.Add(self.__logx,      flag=wx.EXPAND)
        self.__sizer.Add(self.__logy,      flag=wx.EXPAND)
        self.__sizer.Add(self.__legend,    flag=wx.EXPAND)
        
        self.__sizer.Add(self.__ticks,     flag=wx.EXPAND)
        self.__sizer.Add(self.__grid,      flag=wx.EXPAND)
        self.__sizer.Add(self.__autoScale, flag=wx.EXPAND)
        
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

        self.SetMinSize(self.__sizer.GetMinSize())
        self.SetMaxSize(self.__sizer.GetMinSize())

        tsPanel.addListener('autoScale', self._name, self.__autoScaleChanged)

        self.__autoScaleChanged()
        

    def __autoScaleChanged(self, *a):

        enableLim = not self.__tsPanel.autoScale

        self.__xlimLabel.Enable(enableLim)
        self.__ylimLabel.Enable(enableLim)
        self.__xmin     .Enable(enableLim)
        self.__xmax     .Enable(enableLim)
        self.__ymin     .Enable(enableLim)
        self.__ymax     .Enable(enableLim)
