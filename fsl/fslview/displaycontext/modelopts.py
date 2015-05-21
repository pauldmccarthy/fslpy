#!/usr/bin/env python
#
# modelopts.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import copy

import numpy as np

import props

import display                as fsldisplay

import fsl.fslview.colourmaps as colourmaps
import fsl.data.image         as fslimage
import fsl.data.strings       as strings
import fsl.utils.transform    as transform

import volumeopts


class ModelOpts(fsldisplay.DisplayOpts):

    colour     = props.Colour()

    
    outline    = props.Boolean(default=False)

    
    refImage   = props.Choice()

    
    coordSpace = copy.copy(volumeopts.ImageOpts.transform)


    transform  = copy.copy(volumeopts.ImageOpts.transform)


    def __init__(self, *args, **kwargs):

        # Create a random, highly
        # saturated colour
        colour      = colourmaps.randomBrightColour()
        self.colour = np.concatenate((colour, [1.0]))
 
        # But create that colour before
        # base class initialisation, as
        # there may be a parent colour
        # value which will override the
        # one we generated above.
        fsldisplay.DisplayOpts.__init__(self, *args, **kwargs)

        self.__oldRefImage = None

        self.overlayList.addListener('overlays',
                                     self.name,
                                     self.__overlayListChanged)

        self.addListener('refImage', self.name, self.__refImageChanged)
        
        self.__overlayListChanged() 


    def destroy(self):
        fsldisplay.DisplayOpts.destroy(self)
        self.overlayList.removeListener('overlays', self.name)

        for overlay in self.overlayList:
            overlay.removeListener('name', self.name)


    def getReferenceImage(self):
        """Overrides :meth:`.DisplayOpts.getReferenceIamge`.

        If a :attr:`refImage` is selected, it is returned. Otherwise,``None``
        is returned.
        """
        return self.refImage
            

    def getDisplayBounds(self):

        lo, hi = self.overlay.getBounds()
        xform  = self.getCoordSpaceTransform()

        if xform is None:
            return lo, hi

        lohi = transform.transform([lo, hi], xform)

        return lohi[0, :], lohi[1, :]


    def getOldDisplayBounds(self):
        return self.overlay.getBounds()


    def getCoordSpaceTransform(self):

        if self.refImage is None:
            return None

        if self.coordSpace == self.transform:
            return None

        opts = self.displayCtx.getOpts(self.refImage)

        return opts.getTransform(self.coordSpace, self.transform)


    def __refImageChanged(self, *a):
        
        if self.__oldRefImage is not None:
            opts = self.displayCtx.getOpts(self.__oldRefImage)
            self.unbindProps('transform', opts)

        self.__oldRefImage = self.refImage
        
        if self.refImage is not None:
            opts = self.displayCtx.getOpts(self.refImage)
            self.bindProps('transform', opts)
            
    
    def __overlayListChanged(self, *a):
        """Called when the overlay list changes. Updates the ``refImage``
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

        imgOptions = [None]
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
        else:                  self.refImage = None
