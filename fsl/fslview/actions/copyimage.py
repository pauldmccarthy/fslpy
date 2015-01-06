#!/usr/bin/env python
#
# copyimage.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import numpy               as np

import fsl.fslview.actions as actions
import fsl.data.image      as fslimage

class CopyImageAction(actions.Action):

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
        self.enabled = self._displayCtx.getSelectedImage() is not None
    
    
    def doAction(self):

        imageIdx = self._displayCtx.selectedImage
        image    = self._imageList[imageIdx]

        if image is None:
            return

        data  = np.copy(image.data)
        xform = image.voxToWorldMat
        name  = '{}_copy'.format(image.name)
        copy  = fslimage.Image(data, xform, name)

        # TODO copy display properties
        
        self._imageList.insert(imageIdx + 1, copy)
