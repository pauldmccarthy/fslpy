#!/usr/bin/env python
#
# timeserieslistpanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import          wx
import numpy as np

import                           props
import pwidgets.elistbox      as elistbox
import fsl.fslview.panel      as fslpanel
import fsl.utils.transform    as transform
import fsl.fslview.colourmaps as fslcm


class TimeSeriesWidget(wx.Panel):

    def __init__(self, parent, timeSeries):

        wx.Panel.__init__(self, parent)

        self.colour    = props.makeWidget(self,
                                          timeSeries,
                                          'colour')
        self.alpha     = props.makeWidget(self,
                                          timeSeries,
                                          'alpha',
                                          slider=True,
                                          spin=False,
                                          showLimits=False) 
        self.lineWidth = props.makeWidget(self,
                                          timeSeries,
                                          'lineWidth')
        self.lineStyle = props.makeWidget(self,
                                          timeSeries,
                                          'lineStyle') 

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)

        self.sizer.Add(self.colour)
        self.sizer.Add(self.alpha)
        self.sizer.Add(self.lineWidth)
        self.sizer.Add(self.lineStyle)

        self.Layout()
    

class TimeSeriesListPanel(fslpanel.FSLViewPanel):

    def __init__(self, parent, overlayList, displayCtx, timeSeriesPanel):

        fslpanel.FSLViewPanel.__init__(self, parent, overlayList, displayCtx)

        self.__tsPanel      = timeSeriesPanel
        self.__currentLabel = wx.StaticText(self)
        self.__tsList       = elistbox.EditableListBox(
            self, style=(elistbox.ELB_NO_MOVE |
                         elistbox.ELB_EDITABLE))

        self.__sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.__sizer)

        self.__sizer.Add(self.__currentLabel, flag=wx.EXPAND)
        self.__sizer.Add(self.__tsList,       flag=wx.EXPAND, proportion=1)

        self.__tsList.Bind(elistbox.EVT_ELB_ADD_EVENT,    self.__onListAdd)
        self.__tsList.Bind(elistbox.EVT_ELB_REMOVE_EVENT, self.__onListRemove)
        self.__tsList.Bind(elistbox.EVT_ELB_EDIT_EVENT,   self.__onListEdit)
        self.__tsList.Bind(elistbox.EVT_ELB_SELECT_EVENT, self.__onListSelect)
        
        displayCtx    .addListener('selectedOverlay',
                                   self._name,
                                   self.__locationChanged)
        displayCtx    .addListener('location',
                                   self._name,
                                   self.__locationChanged) 
        overlayList   .addListener('overlays',
                                   self._name,
                                   self.__locationChanged)
        self.__tsPanel.addListener('timeSeries',
                                   self._name,
                                   self.__timeSeriesChanged)

        self.__timeSeriesChanged()
        self.__locationChanged()
        self.Layout()

        
    def destroy(self):
        fslpanel.FSLViewPanel.destroy(self)
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._overlayList.removeListener('overlays',        self._name)
        self.__tsPanel   .removeListener('timeSeries',      self._name)



    def __makeLabel(self, ts):
        return '{} [{} {} {}]'.format(ts.overlay.name,
                                      ts.coords[0],
                                      ts.coords[1],
                                      ts.coords[2])    


    def __timeSeriesChanged(self, *a):

        self.__tsList.Clear()

        for ts in self.__tsPanel.timeSeries:
            widg = TimeSeriesWidget(self, ts)
            self.__tsList.Append(ts.label, clientData=ts, extraWidget=widg)


    def __locationChanged(self, *a):

        ts = self.__tsPanel.getCurrent()

        if ts is None:
            self.__currentLabel.SetLabel('')
            return
        
        self.__currentLabel.SetLabel(self.__makeLabel(ts))

 
    
    def __onListAdd(self, ev):
        
        ts = self.__tsPanel.getCurrent()

        if ts is None:
            return
        
        ts.alpha     = 1
        ts.lineWidth = 2
        ts.lineStyle = '-'
        ts.colour    = fslcm.randomColour()
        ts.label     = self.__makeLabel(ts)
        self.__tsPanel.timeSeries.append(ts)

        
    def __onListEdit(self, ev):
        ev.data.label = ev.label

        
    def __onListSelect(self, ev):

        opts = self._displayCtx.getOpts(ev.data.overlay)
        vox   = np.array(ev.data.coords)
        xform = opts.getTransform('voxel', 'display')
        disp  = transform.transform([vox], xform)[0]

        self._displayCtx.location = disp

        
    def __onListRemove(self, ev):
        self.__tsPanel.timeSeries.remove(ev.data)
