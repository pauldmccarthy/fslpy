#!/usr/bin/env python
#
# timeseriescontrolpanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import wx

import                        props
import pwidgets.widgetlist as widgetlist

import fsl.fslview.panel as fslpanel
import fsl.data.strings  as strings


class TimeSeriesControlPanel(fslpanel.FSLViewPanel):

    def __init__(self, parent, overlayList, displayCtx, tsPanel):

        fslpanel.FSLViewPanel.__init__(self, parent, overlayList, displayCtx)

        self.__tsPanel = tsPanel
        self.__widgets = widgetlist.WidgetList(self)
        self.__sizer   = wx.BoxSizer(wx.VERTICAL)

        self.SetSizer(self.__sizer)
        self.__sizer.Add(self.__widgets, flag=wx.EXPAND, proportion=1)

        tsProps   = ['demean',
                     'usePixdim',
                     'showCurrent']
        plotProps = ['xLogScale',
                     'yLogScale',
                     'smooth',
                     'legend',
                     'ticks',
                     'grid',
                     'autoScale']

        for prop in tsProps:
            self.__widgets.AddWidget(
                props.makeWidget(self.__widgets, tsPanel, prop),
                displayName=strings.properties[tsPanel, prop])

        self.__widgets.AddGroup(
            'plotSettings',
            strings.labels[tsPanel, 'plotSettings'])
        
        for prop in plotProps:
            self.__widgets.AddWidget(
                props.makeWidget(self.__widgets, tsPanel, prop),
                displayName=strings.properties[tsPanel, prop],
                groupName='plotSettings')

        xlabel = props.makeWidget(self.__widgets, tsPanel, 'xlabel')
        ylabel = props.makeWidget(self.__widgets, tsPanel, 'ylabel')

        labels = wx.BoxSizer(wx.HORIZONTAL)

        labels.Add(wx.StaticText(self.__widgets,
                                 label=strings.labels[tsPanel, 'xlabel']))
        labels.Add(xlabel, flag=wx.EXPAND, proportion=1)
        labels.Add(wx.StaticText(self.__widgets,
                                 label=strings.labels[tsPanel, 'ylabel']))
        labels.Add(ylabel, flag=wx.EXPAND, proportion=1) 

        limits = props.makeListWidgets(self.__widgets, tsPanel, 'limits')
        xlims  = wx.BoxSizer(wx.HORIZONTAL)
        ylims  = wx.BoxSizer(wx.HORIZONTAL)
        
        xlims.Add(limits[0], flag=wx.EXPAND, proportion=1)
        xlims.Add(limits[1], flag=wx.EXPAND, proportion=1)
        ylims.Add(limits[2], flag=wx.EXPAND, proportion=1)
        ylims.Add(limits[3], flag=wx.EXPAND, proportion=1) 

        self.__widgets.AddWidget(
            labels,
            strings.labels[tsPanel, 'labels'],
            groupName='plotSettings')
        self.__widgets.AddWidget(
            xlims,
            strings.labels[tsPanel, 'xlim'],
            groupName='plotSettings')
        self.__widgets.AddWidget(
            ylims,
            strings.labels[tsPanel, 'ylim'],
            groupName='plotSettings')
