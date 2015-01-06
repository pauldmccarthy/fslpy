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
    
    def doAction(self):

        imageIdx = self._displayCtx.selectedImage
        image    = self._imageList[imageIdx]

        if image is None:
            return

        data  = np.copy(image.data)
        xform = image.voxToWorldMat
        name  = '{}_copy'.format(image.name)
        copy  = fslimage.Image(data, xform, name)

        self._imageList.insert(imageIdx + 1, copy)
