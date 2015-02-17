#!/usr/bin/env python
#
# atlasoverlaypanel.py - 
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""
"""

import logging

import wx

import pwidgets.elistbox as elistbox

import fsl.data.atlases  as atlases
import fsl.fslview.panel as fslpanel


log = logging.getLogger(__name__)


class OverlayListWidget(wx.Panel):

    def __init__(self, parent, atlasID, atlasPanel, labelIdx=None):

        wx.Panel.__init__(self, parent)
        
        self.atlasID    = atlasID
        self.atlasDesc  = atlases.getAtlasDescription(atlasID)
        self.atlasPanel = atlasPanel
        self.labelIdx   = labelIdx

        self.enableBox = wx.CheckBox(self)
        self.enableBox.SetValue(False)

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)

        self.sizer.Add(self.enableBox, flag=wx.EXPAND)

        self.enableBox.Bind(wx.EVT_CHECKBOX, self._onEnable)
        
        if labelIdx is not None:
            self.locateButton = wx.Button(self,
                                          label='+',
                                          style=wx.BU_EXACTFIT)
            self.sizer.Add(self.locateButton, flag=wx.EXPAND)

            self.locateButton.Bind(wx.EVT_BUTTON, self._onLocate)
        
    def _onEnable(self, ev):
        self.atlasPanel.toggleOverlay(
            self.atlasID,
            self.labelIdx,
            self.atlasDesc.atlasType == 'label')

    def _onLocate(self, ev):
        self.atlasPanel.locateRegion(self.atlasID, self.labelIdx)

        
# TODO control to locate region (in addition 
# to control displaying the region)

class AtlasOverlayPanel(fslpanel.FSLViewPanel):

    def __init__(self, parent, imageList, displayCtx, atlasPanel):

        fslpanel.FSLViewPanel.__init__(self, parent, imageList, displayCtx)

        self.enabledOverlays = {}
        self.atlasPanel      = atlasPanel
        self.atlasList       = elistbox.EditableListBox(
            self,
            style=(elistbox.ELB_NO_ADD    |
                   elistbox.ELB_NO_REMOVE |
                   elistbox.ELB_NO_MOVE))

        self.regionPanel     = wx.Panel(   self)
        self.regionFilter    = wx.TextCtrl(self.regionPanel)

        atlasDescs = atlases.listAtlases()

        self.regionLists = [None] * len(atlasDescs)

        self.sizer       = wx.BoxSizer(wx.HORIZONTAL)
        self.regionSizer = wx.BoxSizer(wx.VERTICAL)
        
        self.sizer      .Add(self.atlasList,    flag=wx.EXPAND, proportion=1)
        self.regionSizer.Add(self.regionFilter, flag=wx.EXPAND)
        self.regionSizer.AddStretchSpacer()
        self.sizer      .Add(self.regionPanel,  flag=wx.EXPAND, proportion=1)
        
        self.regionPanel.SetSizer(self.regionSizer) 
        self            .SetSizer(self.sizer)

        for i, atlasDesc in enumerate(atlasDescs):
            self.atlasList.Append(atlasDesc.name, atlasDesc)
            self._updateAtlasState(i)
            widget = OverlayListWidget(self.atlasList,
                                       atlasDesc.atlasID,
                                       atlasPanel)
            self.atlasList.SetItemWidget(i, widget)
        
        self.regionFilter.Bind(wx.EVT_TEXT, self._onRegionFilter)
        self.atlasList.Bind(elistbox.EVT_ELB_SELECT_EVENT, self._onAtlasSelect)

        self.regionSizer.Layout()
        self.sizer      .Layout()


    def setOverlayState(self, atlasID, labelIdx, summary, state):

        atlasDesc = atlases.getAtlasDescription(atlasID)
        log.debug('Setting {}/{} overlay state to {}'.format(
            atlasID, labelIdx, state))

        if labelIdx is None:
            widget = self.atlasList.GetItemWidget(atlasDesc.index)
            widget.enableBox.SetValue(state)
        else:
            regionList = self.regionLists[atlasDesc.index]
            
            if regionList is not None:
                regionList.GetItemWidget(labelIdx).enableBox.SetValue(state)


    def _onRegionFilter(self, ev):
        
        filterStr = self.regionFilter.GetValue().lower()

        for i, listBox in enumerate(self.regionLists):

            if listBox is None:
                continue
            
            listBox.ApplyFilter(filterStr, ignoreCase=True)
            self._updateAtlasState(i)


    def _updateAtlasState(self, atlasIdx):

        listBox = self.regionLists[atlasIdx]
        
        if listBox is None:
            weight = wx.FONTWEIGHT_LIGHT
            colour = '#a0a0a0'
        
        elif listBox.VisibleItemCount() == 0:
            weight = wx.FONTWEIGHT_LIGHT
            colour = '#303030'
        else:
            weight = wx.FONTWEIGHT_BOLD
            colour = '#000000'

        font = self.atlasList.GetItemFont(atlasIdx)
        font.SetWeight(weight)
        
        self.atlasList.SetItemFont(atlasIdx, font)
        self.atlasList.SetItemForegroundColour(atlasIdx, colour, colour) 
 
            
    def _onAtlasSelect(self, ev):

        atlasDesc  = ev.data
        atlasIdx   = ev.idx
        regionList = self.regionLists[atlasIdx]

        if regionList is None:
            
            regionList = elistbox.EditableListBox(
                self.regionPanel,
                style=(elistbox.ELB_NO_ADD    |
                       elistbox.ELB_NO_REMOVE |
                       elistbox.ELB_NO_MOVE))

            log.debug('Creating region list for {} ({})'.format(
                atlasDesc.atlasID, id(regionList)))
            
            self.regionLists[atlasIdx] = regionList

            for i, label in enumerate(atlasDesc.labels):
                regionList.Append(label.name)
                widget = OverlayListWidget(regionList,
                                           atlasDesc.atlasID,
                                           self.atlasPanel,
                                           label.index)
                regionList.SetItemWidget(i, widget)
                                           


            filterStr = self.regionFilter.GetValue().lower()
            regionList.ApplyFilter(filterStr, ignoreCase=True)

            self._updateAtlasState(atlasIdx)
            
        log.debug('Showing region list for {} ({})'.format(
            atlasDesc.atlasID, id(regionList)))

        old = self.regionSizer.GetItem(1).GetWindow()
        
        if old is not None:
            old.Show(False)
            
        regionList.Show(True)
        self.regionSizer.Remove(1)
        
        self.regionSizer.Insert(1, regionList, flag=wx.EXPAND, proportion=1)
        self.regionSizer.Layout()
