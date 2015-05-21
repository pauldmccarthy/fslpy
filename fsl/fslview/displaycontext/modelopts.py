#!/usr/bin/env python
#
# modelopts.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import copy

import numpy as np

import props

import display as fsldisplay

import fsl.data.image   as fslimage
import fsl.data.strings as strings

import volumeopts


class ModelOpts(fsldisplay.DisplayOpts):

    colour   = props.Colour()
    outline  = props.Boolean(default=False)

    refImage = props.Choice()

    coordSpace = copy.copy(volumeopts.ImageOpts.transform)


    def __init__(self, *args, **kwargs):

        # Create a random, highly
        # saturated colour
        colour                  = np.random.random(3)
        colour[colour.argmax()] = 1
        colour[colour.argmin()] = 0

        np.random.shuffle(colour)

        self.colour = np.concatenate((colour, [1.0]))
 
        # But create that colour before
        # base class initialisation, as
        # there may be a parent colour
        # value which will override the
        # one we generated above.
        fsldisplay.DisplayOpts.__init__(self, *args, **kwargs)

        self.overlayList.addListener('overlays',
                                     self.name,
                                     self.__overlayListChanged)
        
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

        if self.refImage is not 'none':
            return self.refImage
        return None
            

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
    

# The coordSpace property replicates the ImageOpts.transform
# property. But, where the ImageOpts.transform property
# defaults to 'pixdim' (so that volumes are displayed with
# scaled voxels by default), the coordSpace property needs to
# default to 'id' (because FIRST .vtk model coordinates are
# in terms of the source image voxel coordinates).
ModelOpts.coordSpace.setConstraint(None, 'default', 'id')
