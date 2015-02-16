#!/usr/bin/env python
#
# atlasoverlaypanel.py - 
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""
"""

import logging

import          wx
import numpy as np

import pwidgets.elistbox  as elistbox

import fsl.data.atlases   as atlases
import fsl.data.image     as fslimage
import fsl.data.constants as constants
import fsl.fslview.panel  as fslpanel


log = logging.getLogger(__name__)


class OverlayListWidget(wx.CheckBox):

    def __init__(self, parent, atlasID, label=None):

        wx.CheckBox.__init__(self, parent)

        self.parent   = parent
        self.atlasID  = atlasID
        self.label    = label

        
    def _onCheck(self, ev):
        pass


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
        
        self.regionFilter.Bind(wx.EVT_TEXT, self._onRegionFilter)
        self.atlasList.Bind(elistbox.EVT_ELB_SELECT_EVENT, self._onAtlasSelect)

        self.regionSizer.Layout()
        self.sizer      .Layout()


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

            print 'Creating region list for {} ({})'.format(
                atlasDesc.atlasID, id(regionList))
            
            self.regionLists[atlasIdx] = regionList

            for label in atlasDesc.labels:
                regionList.Append(label.name)

            filterStr = self.regionFilter.GetValue().lower()
            regionList.ApplyFilter(filterStr, ignoreCase=True)

            self._updateAtlasState(atlasIdx)
            
        print 'Showing region list for {} ({})'.format(
            atlasDesc.atlasID, id(regionList))

        old = self.regionSizer.GetItem(1).GetWindow()
        
        if old is not None:
            old.Show(False)
            
        regionList.Show(True)
        self.regionSizer.Remove(1)
        
        self.regionSizer.Insert(1, regionList, flag=wx.EXPAND, proportion=1)
        self.regionSizer.Layout()


    def overlayIsEnabled(self, atlasDesc, label=None, summary=False):
        pass

        
    def toggleSummaryOverlay(self, atlasDesc):

        atlasID     = atlasDesc.atlasID
        overlayName = '{}/all'.format(atlasID)
        overlay     = self._imageList.find(overlayName)

        if overlay is not None:
            self._imageList.remove(overlay)
            log.debug('Removed summary overlay {}'.format(overlayName))
            
        else:
            overlay = self.enabledAtlases.get(atlasID, None)
            if overlay is None or \
               isinstance(overlay, atlases.ProbabilisticAtlas):
                overlay = atlases.loadAtlas(atlasDesc, True)
                
            overlay.name = overlayName


            self._imageList.append(overlay)
            log.debug('Added summary overlay {}'.format(overlayName))
            
    
    def toggleOverlay(self, atlasDesc, labelIndex, label):
        """
        """

        atlasID     = atlasDesc.atlasID
        overlayName = '{}/{}'.format(atlasID,
                                     atlasDesc.labels[labelIndex].name)
        overlay     = self._imageList.find(overlayName)

        if overlay is not None:
            self._imageList.remove(overlay)
            log.debug('Removed overlay {}'.format(overlayName))

        else:
            atlas = self.enabledAtlases.get(atlasID, None)
            if atlas is None or \
               (label and isinstance(overlay, atlases.LabelAtlas)):
                atlas = atlases.loadAtlas(atlasDesc, True)

            if label:
                if   atlasDesc.atlasType == 'probabilistic':
                    labelVal = labelIndex + 1
                elif atlasDesc.atlasType == 'label':
                    labelVal = labelIndex 
            
                mask = np.zeros(atlas.shape, dtype=np.uint8)
                mask[atlas.data == labelIndex] = labelVal
            else:
                mask = atlas.data[..., labelIndex]

            overlay = fslimage.Image(
                mask,
                header=atlas.nibImage.get_header(),
                name=overlayName)

            # See comment  in toggleSummaryOverlay
            overlay.nibImage.get_header().set_sform(
                None, code=constants.NIFTI_XFORM_MNI_152)

            if label:
                overlay.imageType = 'mask'

            self._imageList.append(overlay)
            log.debug('Added overlay {}'.format(overlayName))
            
            display = self._displayCtx.getDisplayProperties(overlay)

            if label:
                display.getDisplayOpts().colour = np.random.random(3)
            else:
                display.getDisplayOpts().cmap = 'hot'
