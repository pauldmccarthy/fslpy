#!/usr/bin/env python
#
# modelopts.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import numpy as np

import props

import display as fsldisplay

import fsl.data.image   as fslimage
import fsl.data.strings as strings


class ModelOpts(fsldisplay.DisplayOpts):

    colour  = props.Colour()
    outline = props.Boolean(default=False)

    refImage = props.Choice()


    def __init__(self, *args, **kwargs):
        
        fsldisplay.DisplayOpts.__init__(self, *args, **kwargs)
        
        colour                  = np.random.random(3)
        colour[colour.argmax()] = 1
        colour[colour.argmin()] = 0
        
        np.random.shuffle(colour)

        self.colour = np.concatenate((colour, [1.0]))

        self.overlayList.addListener('overlays',
                                     self.name,
                                     self.__overlayListChanged)
        
        self.__overlayListChanged() 


    def destroy(self):
        fsldisplay.DisplayOpts.destroy(self)
        self.overlayList.removeListener('overlays', self.name)

        for overlay in self.overlayList:
            overlay.removeListener('name', self.name)
            

    def getDisplayBounds(self):
        return self.overlay.getBounds()


    def getOldDisplayBounds(self):
        return self.overlay.getBounds()

    
    def __overlayListChanged(self, *a):
        """Called when the overlay list changes. Updates the ``image``
        property so that it contains a list of overlays which can be
        associated with the model.
        """
        
        imgProp  = self.getProp('refImage')
        imgVal   = self.refImage
        overlays = self.displayCtx.getOrderedOverlays()

        # the overlay for this ModelOpts
        # instance has been removed
        if self.overlay not in overlays:
            self.overlayList.removeListener('overlays', self.name)
            return

        imgOptions = ['none']
        imgLabels  = [strings.choices['ModelOpts.refImage.none']]

        for overlay in overlays:
            
            # The image must be an Image instance.
            if not isinstance(overlay, fslimage.Image):
                continue

            imgOptions.append(overlay)
            imgLabels .append(overlay.name)
                
            overlay.addListener('name',
                                self.name,
                                self.__overlayListChanged,
                                overwrite=True)
            
        imgProp.setChoices(imgOptions, imgLabels, self)

        if imgVal in overlays: self.refImage = imgVal
        else:                  self.refImage = 'none' 
