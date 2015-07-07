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

        displayCtx .addListener('selectedOverlay',
                                self._name,
                                self.__selectedOverlayChanged)
        overlayList.addListener('overlays',
                                self._name,
                                self.__selectedOverlayChanged)

        # This attribute keeps track of the currently
        # selected overlay, but only if said overlay
        # is a FEATImage.
        self.__selectedOverlay = None
        self.__selectedOverlayChanged()


    def destroy(self):
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._overlayList.removeListener('overlays',        self._name)

        if self.__selectedOverlay is not None:
            display = self._displayCtx.getDisplay(self.__selectedOverlay)
            display.removeListener('name', self._name)


    def __selectedOverlayNameChanged(self, *a):
        display = self._displayCtx.getDisplay(self.__selectedOverlay)
        self.__widgets.RenameGroup(
            'currentFEATSettings',
            strings.labels[self, 'currentFEATSettings'].format(
                display.name))

    
    def __selectedOverlayChanged(self, *a):

        # We're assuminbg that the TimeSeriesPanel has
        # already updated its current TimeSeries for
        # the newly selected overlay.
        
        import fsl.fslview.views.timeseriespanel as tsp

        if self.__selectedOverlay is not None:
            display = self._displayCtx.getDisplay(self.__selectedOverlay)
            display.removeListener('name', self._name)
            self.__selectedOverlay = None

        if self.__widgets.HasGroup('currentFEATSettings'):
            self.__widgets.RemoveGroup('currentFEATSettings')

        ts = self.__tsPanel.getCurrent()

        if ts is None or not isinstance(ts, tsp.FEATTimeSeries):
            return

        overlay = ts.overlay
        display = self._displayCtx.getDisplay(overlay)

        self.__selectedOverlay = overlay

        display.addListener('name',
                            self._name,
                            self.__selectedOverlayNameChanged)

        self.__widgets.AddGroup(
            'currentFEATSettings',
            displayName=strings.labels[self, 'currentFEATSettings'].format(
                display.name))

        full    = props.makeWidget(     self.__widgets, ts, 'plotFullModelFit')
        pes     = props.makeListWidgets(self.__widgets, ts, 'plotPEFits')
        copes   = props.makeListWidgets(self.__widgets, ts, 'plotCOPEFits')
        self.__widgets.AddWidget(
            full,
            displayName=strings.properties[ts, 'plotFullModelFit'],
            groupName='currentFEATSettings')

        for i, pe in enumerate(pes):
            peName = 'PE {}'.format(i + 1)
            self.__widgets.AddWidget(
                pe,
                displayName=strings.properties[ts, 'plotPEFits'].format(
                    peName),
                groupName='currentFEATSettings') 


        copeNames = overlay.contrastNames()
        for i, (cope, name) in enumerate(zip(copes, copeNames)):
            self.__widgets.AddWidget(
                cope,
                displayName=strings.properties[ts, 'plotCOPEFits'].format(
                    i, name),
                groupName='currentFEATSettings') 
