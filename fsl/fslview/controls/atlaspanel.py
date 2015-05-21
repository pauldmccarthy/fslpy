#!/usr/bin/env python
#
# atlaspanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import numpy as np
import          wx

import pwidgets.notebook   as notebook

import fsl.data.image      as fslimage
import fsl.data.atlases    as atlases
import fsl.data.strings    as strings
import fsl.utils.transform as transform
import fsl.fslview.panel   as fslpanel


log = logging.getLogger(__name__)


class AtlasPanel(fslpanel.FSLViewPanel):


    def __init__(self, parent, overlayList, displayCtx):

        import fsl.fslview.controls.atlasoverlaypanel as atlasoverlaypanel
        import fsl.fslview.controls.atlasinfopanel    as atlasinfopanel        

        fslpanel.FSLViewPanel.__init__(self, parent, overlayList, displayCtx)

        self.__loadedAtlases  = {}
        self.__atlasRefCounts = {}

        self.__notebook = notebook.Notebook(self)

        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__sizer.Add(self.__notebook, flag=wx.EXPAND, proportion=1)
 
        self.SetSizer(self.__sizer)

        self.__infoPanel = atlasinfopanel.AtlasInfoPanel(
            self.__notebook, overlayList, displayCtx, self)

        # Overlay panel, containing a list of regions,
        # allowing the user to add/remove overlays
        self.__overlayPanel = atlasoverlaypanel.AtlasOverlayPanel(
            self.__notebook, overlayList, displayCtx, self)
        
        self.__notebook.AddPage(self.__infoPanel,
                                strings.titles[self.__infoPanel])
        self.__notebook.AddPage(self.__overlayPanel,
                                strings.titles[self.__overlayPanel])

        # TODO Listen on overlay list, and update atlas
        # overlay panel states when an overlay image is
        # removed

        self.Layout()
        self.SetMinSize(self.__sizer.GetMinSize())


    def destroy(self):
        """Must be called on destruction. Performs some necessary clean up
        when this AtlasPanel is no longer needed.
        """
        fslpanel.FSLViewPanel.destroy(self)
        self.__infoPanel     .destroy()
        self.__overlayPanel  .destroy()


    def loadAtlas(self, atlasID, summary):

        desc = atlases.getAtlasDescription(atlasID)

        if desc.atlasType == 'summary':
            summary = True

        refCount = self.__atlasRefCounts.get((atlasID, summary), 0)
        atlas    = self.__loadedAtlases .get((atlasID, summary), None)

        if atlas is None:
            log.debug('Loading atlas {}/{} ({} references)'.format(
                atlasID,
                'label' if summary else 'prob',
                refCount + 1))
            atlas = atlases.loadAtlas(atlasID, summary)
            
        self.__atlasRefCounts[atlasID, summary] = refCount + 1
        self.__loadedAtlases[ atlasID, summary] = atlas

        return atlas

    
    def clearAtlas(self, atlasID, summary):

        desc = atlases.getAtlasDescription(atlasID)
        
        if desc.atlasType == 'summary':
            summary = True        

        refCount = self.__atlasRefCounts[atlasID, summary]

        if refCount == 0:
            return
        
        self.__atlasRefCounts[atlasID, summary] = refCount - 1
        
        if refCount - 1 == 0:
            log.debug('Clearing atlas {}/{} ({} references)'.format(
                atlasID,
                'label' if summary else 'prob',
                refCount - 1)) 
            self.__loadedAtlases.pop((atlasID, summary))


    def getOverlayName(self, atlasID, labelIdx, summary):
        atlasDesc = atlases.getAtlasDescription(atlasID)

        if atlasDesc.atlasType == 'summary' or labelIdx is None:
            summary = True

        if summary: overlayType = 'label'
        else:       overlayType = 'prob'

        if labelIdx is None:
            overlayName = '{}/{}/all'.format(atlasID, overlayType)
        else:
            overlayName = '{}/{}/{}' .format(atlasID,
                                             overlayType,
                                             atlasDesc.labels[labelIdx].name)
 
        return overlayName, summary

    
    def getOverlayState(self, atlasID, labelIdx, summary):

        name, _ = self.getOverlayName(atlasID, labelIdx, summary)
        return self._overlayList.find(name) is not None
    

    def toggleOverlay(self, atlasID, labelIdx, summary):

        atlasDesc            = atlases.getAtlasDescription(atlasID)
        overlayName, summary = self.getOverlayName(atlasID, labelIdx, summary)
        overlay              = self._overlayList.find(overlayName)
 
        if overlay is not None:
            self.clearAtlas(atlasID, summary)
            self._overlayList.remove(overlay)
            self.__overlayPanel.setOverlayState(
                atlasID, labelIdx, summary, False)
            log.debug('Removed overlay {}'.format(overlayName))
            return

        atlas = self.loadAtlas(atlasID, summary)

        # label image
        if labelIdx is None:
            imageType = 'volume'
            data      = atlas.data
        else:

            # regional label image
            if summary:
                if   atlasDesc.atlasType == 'probabilistic':
                    labelVal = labelIdx + 1
                elif atlasDesc.atlasType == 'label':
                    labelVal = labelIdx

                imageType = 'mask' 
                data      = np.zeros(atlas.shape, dtype=np.uint16)
                data[atlas.data == labelIdx] = labelVal
                
            # regional probability image
            else:
                imageType = 'volume' 
                data      = atlas.data[:, :, :, labelIdx]

        overlay = fslimage.Image(
            data,
            header=atlas.nibImage.get_header(),
            name=overlayName)
            
        overlay.imageType = imageType

        self._overlayList.append(overlay)

        self.__overlayPanel.setOverlayState(
            atlasID, labelIdx, summary, True)
        
        log.debug('Added overlay {}'.format(overlayName))

        opts = self._displayCtx.getOpts(overlay)

        if labelIdx is not None:
            if summary: opts.colour = np.random.random(3)
            else:       opts.cmap   = 'hot'
        else:
            # The Harvard-Oxford atlases have special colour maps
            if   atlasID == 'HarvardOxford-Cortical':
                cmap = 'MGH Cortical'
            elif atlasID == 'HarvardOxford-Subcortical':
                cmap = 'MGH Sub-cortical'
            else:
                cmap = 'Random'
                
            opts.cmap = cmap


    def locateRegion(self, atlasID, labelIdx):
        
        atlasDesc = atlases.getAtlasDescription(atlasID)
        label     = atlasDesc.labels[labelIdx]
        overlay   = self._displayCtx.getReferenceImage(
            self._displayCtx.getSelectedOverlay())

        if overlay is None:
            log.warn('No reference image available - cannot locate region')
        
        opts     = self._displayCtx.getOpts(overlay)
        worldLoc = (label.x, label.y, label.z)
        dispLoc  = transform.transform(
            [worldLoc], opts.getTransform('world', 'display'))[0]

        self._displayCtx.location.xyz = dispLoc
