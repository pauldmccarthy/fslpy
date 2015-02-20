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


    def __init__(self, parent, imageList, displayCtx):

        import fsl.fslview.controls.atlasoverlaypanel as atlasoverlaypanel
        import fsl.fslview.controls.atlasinfopanel    as atlasinfopanel        

        fslpanel.FSLViewPanel.__init__(self, parent, imageList, displayCtx)

        self.loadedAtlases  = {}
        self.atlasRefCounts = {}

        self.notebook = notebook.Notebook(self)

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.notebook, flag=wx.EXPAND, proportion=1)
 
        self.SetSizer(self.sizer)

        # Temporary
        self.SetMaxSize((-1, 200))

        self.infoPanel = atlasinfopanel.AtlasInfoPanel(
            self.notebook, imageList, displayCtx, self)

        # Overlay panel, containing a list of regions,
        # allowing the user to add/remove overlays
        self.overlayPanel = atlasoverlaypanel.AtlasOverlayPanel(
            self.notebook, imageList, displayCtx, self)
        
        self.notebook.AddPage(self.infoPanel,
                              strings.titles[self.infoPanel])
        self.notebook.AddPage(self.overlayPanel,
                              strings.titles[self.overlayPanel])

        self.notebook.ShowPage(0)

        # TODO Listen on image list, and update overlay
        # panel states when an overlay image is removed

        self.Layout()


    def destroy(self):
        """Must be called on destruction. Performs some necessary clean up
        when this AtlasPanel is no longer needed.
        """
        fslpanel.FSLViewPanel.destroy(self)
        self.infoPanel.destroy()
        self.overlayPanel.destroy()


    def loadAtlas(self, atlasID, summary):

        desc = atlases.getAtlasDescription(atlasID)

        if desc.atlasType == 'summary':
            summary = True

        refCount = self.atlasRefCounts.get((atlasID, summary), 0)
        atlas    = self.loadedAtlases .get((atlasID, summary), None)

        if atlas is None:
            log.debug('Loading atlas {}/{} ({} references)'.format(
                atlasID,
                'label' if summary else 'prob',
                refCount + 1))
            atlas = atlases.loadAtlas(atlasID, summary)
            
        self.atlasRefCounts[atlasID, summary] = refCount + 1
        self.loadedAtlases[ atlasID, summary] = atlas

        return atlas

    
    def clearAtlas(self, atlasID, summary):

        desc = atlases.getAtlasDescription(atlasID)
        
        if desc.atlasType == 'summary':
            summary = True        

        refCount = self.atlasRefCounts[atlasID, summary]

        if refCount == 0:
            return
        
        self.atlasRefCounts[atlasID, summary] = refCount - 1
        
        if refCount - 1 == 0:
            log.debug('Clearing atlas {}/{} ({} references)'.format(
                atlasID,
                'label' if summary else 'prob',
                refCount - 1)) 
            self.loadedAtlases.pop((atlasID, summary))


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
        return self._imageList.find(name) is not None
    

    def toggleOverlay(self, atlasID, labelIdx, summary):

        atlasDesc            = atlases.getAtlasDescription(atlasID)
        overlayName, summary = self.getOverlayName(atlasID, labelIdx, summary)
        overlay              = self._imageList.find(overlayName)
 
        if overlay is not None:
            self.clearAtlas(atlasID, summary)
            self._imageList.remove(overlay)
            self.overlayPanel.setOverlayState(
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

        self._imageList.append(overlay)

        self.overlayPanel.setOverlayState(
            atlasID, labelIdx, summary, True)
        
        log.debug('Added overlay {}'.format(overlayName))

        display = self._displayCtx.getDisplayProperties(overlay)

        if labelIdx is not None:
            if summary: display.getDisplayOpts().colour = np.random.random(3)
            else:       display.getDisplayOpts().cmap   = 'hot'
        else:
            # The Harvard-Oxford atlases have special colour maps
            if   atlasID == 'HarvardOxford-Cortical':    cmap = 'cortical'
            elif atlasID == 'HarvardOxford-Subcortical': cmap = 'subcortical'
            else:                                        cmap = 'random'
                
            display.getDisplayOpts().cmap = cmap


    def locateRegion(self, atlasID, labelIdx):
        
        atlasDesc = atlases.getAtlasDescription(atlasID)
        label     = atlasDesc.labels[labelIdx]

        image   = self._displayCtx.getSelectedImage()
        display = self._displayCtx.getDisplayProperties(image)

        worldLoc = (label.x, label.y, label.z)
        dispLoc  = transform.transform(
            [worldLoc], display.worldToDisplayMat)[0]

        self._displayCtx.location.xyz = dispLoc
