#!/usr/bin/env python
#
# histogramcontrolpanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import wx

import                        props
import pwidgets.widgetlist as widgetlist

import fsl.fslview.panel   as fslpanel
import fsl.data.strings    as strings


class HistogramControlPanel(fslpanel.FSLViewPanel):

    def __init__(self, parent, overlayList, displayCtx, hsPanel):

        fslpanel.FSLViewPanel.__init__(self, parent, overlayList, displayCtx)

        self.__hsPanel  = hsPanel
        self.__widgets  = widgetlist.WidgetList(self)
        self.__sizer    = wx.BoxSizer(wx.VERTICAL)
        
        self.SetSizer(self.__sizer)
        self.__sizer.Add(self.__widgets, flag=wx.EXPAND, proportion=1)

        histProps = ['histType',
                     'autoBin',
                     'showCurrent']
        plotProps = ['xLogScale',
                     'yLogScale',
                     'smooth',
                     'legend',
                     'ticks',
                     'grid',
                     'autoScale']

        for prop in histProps:
            self.__widgets.AddWidget(
                props.makeWidget(self.__widgets, hsPanel, prop),
                displayName=strings.properties[hsPanel, prop])

        self.__widgets.AddGroup(
            'plotSettings',
            strings.labels[self, 'plotSettings'])
        
        for prop in plotProps:
            self.__widgets.AddWidget(
                props.makeWidget(self.__widgets, hsPanel, prop),
                displayName=strings.properties[hsPanel, prop],
                groupName='plotSettings')

        xlabel = props.makeWidget(self.__widgets, hsPanel, 'xlabel')
        ylabel = props.makeWidget(self.__widgets, hsPanel, 'ylabel')

        labels = wx.BoxSizer(wx.HORIZONTAL)

        labels.Add(wx.StaticText(self.__widgets,
                                 label=strings.labels[self, 'xlabel']))
        labels.Add(xlabel, flag=wx.EXPAND, proportion=1)
        labels.Add(wx.StaticText(self.__widgets,
                                 label=strings.labels[self, 'ylabel']))
        labels.Add(ylabel, flag=wx.EXPAND, proportion=1) 

        limits = props.makeListWidgets(self.__widgets, hsPanel, 'limits')
        xlims  = wx.BoxSizer(wx.HORIZONTAL)
        ylims  = wx.BoxSizer(wx.HORIZONTAL)
        
        xlims.Add(limits[0], flag=wx.EXPAND, proportion=1)
        xlims.Add(limits[1], flag=wx.EXPAND, proportion=1)
        ylims.Add(limits[2], flag=wx.EXPAND, proportion=1)
        ylims.Add(limits[3], flag=wx.EXPAND, proportion=1) 

        self.__widgets.AddWidget(
            labels,
            strings.labels[self, 'labels'],
            groupName='plotSettings')
        self.__widgets.AddWidget(
            xlims,
            strings.labels[self, 'xlim'],
            groupName='plotSettings')
        self.__widgets.AddWidget(
            ylims,
            strings.labels[self, 'ylim'],
            groupName='plotSettings')

        self.__currentHs = None
        hsPanel.addListener('selectedSeries',
                            self._name,
                            self.__selectedSeriesChanged)
        
        hsPanel.addListener('dataSeries',
                            self._name,
                            self.__selectedSeriesChanged)

        self.__selectedSeriesChanged()


    def __selectedSeriesChanged(self, *a):

        panel = self.__hsPanel 
        
        if len(panel.dataSeries) == 0:
            self.__currentHs = None
            return

        hs = panel.dataSeries[panel.selectedSeries]

        if hs == self.__currentHs:
            return

        self.__currentHs = hs
