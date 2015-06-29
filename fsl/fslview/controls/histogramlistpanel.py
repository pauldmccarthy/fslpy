#!/usr/bin/env python
#
# histogramlistpanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import wx

import props

import pwidgets.elistbox      as elistbox
import fsl.fslview.panel      as fslpanel
import fsl.data.strings       as strings
import fsl.fslview.colourmaps as fslcm

import                           timeserieslistpanel 
    

class HistogramListPanel(fslpanel.FSLViewPanel):

    def __init__(self, parent, overlayList, displayCtx, histPanel):

        fslpanel.FSLViewPanel.__init__(self, parent, overlayList, displayCtx)

        self.__hsPanel      = histPanel
        self.__hsList       = elistbox.EditableListBox(
            self, style=(elistbox.ELB_NO_MOVE |
                         elistbox.ELB_EDITABLE))

        self.__sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.__sizer)

        self.__sizer.Add(self.__hsList, flag=wx.EXPAND, proportion=1)

        self.__hsList.Bind(elistbox.EVT_ELB_ADD_EVENT,    self.__onListAdd)
        self.__hsList.Bind(elistbox.EVT_ELB_REMOVE_EVENT, self.__onListRemove)
        self.__hsList.Bind(elistbox.EVT_ELB_EDIT_EVENT,   self.__onListEdit)
        self.__hsList.Bind(elistbox.EVT_ELB_SELECT_EVENT, self.__onListSelect)
        
        self.__hsPanel.addListener('dataSeries',
                                   self._name,
                                   self.__histSeriesChanged)

        self.__histSeriesChanged()
        self.Layout()

        
    def destroy(self):
        fslpanel.FSLViewPanel.destroy(self)
        self.__hsPanel.removeListener('dataSeries', self._name)


    def __histSeriesChanged(self, *a):

        self.__hsList.Clear()

        for hs in self.__hsPanel.dataSeries:
            widg = timeserieslistpanel.TimeSeriesWidget(self, hs)

            widg.more = wx.Button(widg, label='More')
            widg.sizer.Add(widg.more)
            widg.Layout()
            widg.more.target = hs
            widg.more.Bind(wx.EVT_BUTTON, self.__showHsControlPanel)
            
            self.__hsList.Append(hs.overlay.name,
                                 clientData=hs,
                                 extraWidget=widg)

        if len(self.__hsPanel.dataSeries) > 0:
            self.__hsList.SetSelection(0)


    def __showHsControlPanel(self, ev):

        hs  = ev.GetEventObject().target
        dlg = HistSeriesDialog(self, self.__hsPanel, hs)

        dlg.Show()
        
    
    def __onListAdd(self, ev):
        
        hs = self.__hsPanel.getCurrent()

        if hs is None:
            return
        
        hs.alpha     = 1
        hs.lineWidth = 2
        hs.lineStyle = '-'
        hs.colour    = fslcm.randomColour()
        hs.label     = hs.overlay.name
        
        self.__hsPanel.dataSeries.append(hs)

        
    def __onListEdit(self, ev):
        ev.data.label = ev.label

        
    def __onListSelect(self, ev):
        overlay = ev.data.overlay
        self._displayCtx.selectedOverlay = self._overlayList.index(overlay)

        
    def __onListRemove(self, ev):
        self.__hsPanel.dataSeries.remove(ev.data)



class HistSeriesDialog(wx.Dialog):
    def __init__(self, parent, hsPanel, hs):
        wx.Dialog.__init__(self,
                           parent,
                           title=hs.overlay.name,
                           style=wx.CLOSE_BOX | wx.STAY_ON_TOP)

        self.__name    = '{}_{}'.format(type(self).__name__, id(self))
        self.__hsPanel = hsPanel
        self.__hs      = hs

        self.__nbins       = props.makeWidget(self, hs, 'nbins',
                                              showLimits=False)
        self.__ignoreZeros = props.makeWidget(self, hs, 'ignoreZeros')
        self.__showOverlay = props.makeWidget(self, hs, 'showOverlay')
        self.__volume      = props.makeWidget(self, hs, 'volume',
                                              showLimits=False)
        self.__dataRange   = props.makeWidget(self, hs, 'dataRange',
                                              showLimits=False)

        self.__nbinsLbl       = wx.StaticText(self)
        self.__ignoreZerosLbl = wx.StaticText(self)
        self.__showOverlayLbl = wx.StaticText(self)
        self.__volumeLbl      = wx.StaticText(self)
        self.__dataRangeLbl   = wx.StaticText(self)

        self.__nbinsLbl      .SetLabel(strings.properties[hs, 'nbins'])
        self.__ignoreZerosLbl.SetLabel(strings.properties[hs, 'ignoreZeros'])
        self.__showOverlayLbl.SetLabel(strings.properties[hs, 'showOverlay'])
        self.__volumeLbl     .SetLabel(strings.properties[hs, 'volume'])     
        self.__dataRangeLbl  .SetLabel(strings.properties[hs, 'dataRange'])  

        self.__sizer = wx.FlexGridSizer(5, 2)

        self.SetSizer(self.__sizer)

        self.__sizer.Add(self.__nbinsLbl,       flag=wx.EXPAND)
        self.__sizer.Add(self.__nbins,          flag=wx.EXPAND)
        self.__sizer.Add(self.__ignoreZerosLbl, flag=wx.EXPAND)
        self.__sizer.Add(self.__ignoreZeros,    flag=wx.EXPAND)
        self.__sizer.Add(self.__showOverlayLbl, flag=wx.EXPAND)
        self.__sizer.Add(self.__showOverlay,    flag=wx.EXPAND) 
        self.__sizer.Add(self.__volumeLbl,      flag=wx.EXPAND)
        self.__sizer.Add(self.__volume,         flag=wx.EXPAND)
        self.__sizer.Add(self.__dataRangeLbl,   flag=wx.EXPAND)
        self.__sizer.Add(self.__dataRange,      flag=wx.EXPAND)

        self.__volume   .Enable(hs.overlay.is4DImage())
        self.__volumeLbl.Enable(hs.overlay.is4DImage())
        self.__autoBinChanged()

        hsPanel.addListener('autoBin',
                            self.__name, 
                            self.__autoBinChanged)
        hsPanel.addListener('dataSeries',
                            self.__name, 
                            self.__dataSeriesChanged) 

        self.Bind(wx.EVT_WINDOW_DESTROY, self.__onDestroy)

        self.Layout()
        self.Fit()
        self.CentreOnParent()


    def __onDestroy(self, ev=None):
        if ev is not None:
            ev.Skip()
        self.__hsPanel.removeListener('autoBin', self.__name)


    def __dataSeriesChanged(self, *a):
        if self.__hs not in self.__hsPanel.dataSeries:
            self.Close()
            self.Destroy()
            self.__onDestroy()

        
    def __autoBinChanged(self, *a):
        self.__nbins   .Enable(not self.__hsPanel.autoBin)
        self.__nbinsLbl.Enable(not self.__hsPanel.autoBin)
