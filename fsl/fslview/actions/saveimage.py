#!/usr/bin/env python
#
# savefile.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import fsl.fslview.actions as actions

class SaveImageAction(actions.Action):

    def __init__(self, *args, **kwargs):
        actions.Action.__init__(self, *args, **kwargs)        

        self._displayCtx.addListener('selectedImage',
                                     self._name,
                                     self._selectedImageChanged)
        self._imageList .addListener('images',
                                     self._name,
                                     self._selectedImageChanged)

        self._selectedImageChanged()

        
    def _selectedImageChanged(self, *a):
        
        image = self._displayCtx.getSelectedImage()
        
        self.enabled = (image is not None) and (not image.saved)

        for i in self._imageList:
            i.removeListener('saved', self._name)
            
            if i is image:
                i.addListener('saved', self._name, self._imageSaveStateChanged)
 

    def _imageSaveStateChanged(self, *a):
        image        = self._displayCtx.getSelectedImage()
        self.enabled = image.saved

        
    def doAction(self):
        pass
