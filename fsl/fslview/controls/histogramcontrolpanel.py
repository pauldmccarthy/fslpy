#!/usr/bin/env python
#
# histogramcontrolpanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import wx

import props

import fsl.fslview.panel as fslpanel
import fsl.data.strings  as strings
import                      plotcontrolpanel


class HistogramControlPanel(fslpanel.FSLViewPanel):


    def __init__(self, parent, overlayList, displayCtx, hsPanel):

        fslpanel.FSLViewPanel.__init__(self, parent, overlayList, displayCtx)

        self.__plotControl = plotcontrolpanel.PlotControlPanel(
            self, overlayList, displayCtx, hsPanel)
        self.__plotControl.SetWindowStyleFlag(wx.SUNKEN_BORDER)

        self.__histType      = props.makeWidget(self, hsPanel, 'histType')
        self.__autoBin       = props.makeWidget(self, hsPanel, 'autoBin')
        self.__showCurrent   = props.makeWidget(self, hsPanel, 'showCurrent')

        self.__histTypeLabel = wx.StaticText(self)

        self.__histTypeLabel.SetLabel(strings.properties[hsPanel,
                                                         'histType'])
        self.__autoBin      .SetLabel(strings.properties[hsPanel,
                                                         'autoBin'])
        self.__showCurrent  .SetLabel(strings.properties[hsPanel,
                                                         'showCurrent'])

        self.__htSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__htSizer.Add(self.__histTypeLabel, flag=wx.EXPAND)
        self.__htSizer.Add(self.__histType,      flag=wx.EXPAND, proportion=1)
 
        self.__optSizer = wx.GridSizer(1, 3)

        self.__optSizer.Add(self.__htSizer,       flag=wx.EXPAND)
        self.__optSizer.Add(self.__autoBin,       flag=wx.EXPAND)
        self.__optSizer.Add(self.__showCurrent,   flag=wx.EXPAND)

        self.__sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.__sizer)
        
        self.__sizer.Add(self.__plotControl,
                         flag=wx.EXPAND | wx.ALL,
                         border=5,
                         proportion=1)
        self.__sizer.Add(self.__optSizer,
                         flag=wx.EXPAND)

        self.Layout()
        
        self.SetMinSize(self.__sizer.GetMinSize())
        self.SetMaxSize(self.__sizer.GetMinSize())
