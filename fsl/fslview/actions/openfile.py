#!/usr/bin/env python
#
# openfileaction.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import fsl.fslview.actions as actions

class OpenFileAction(actions.Action):
    def doAction(self):
        
        if self._imageList.addImages():
            self._displayCtx.selectedImage = self._displayCtx.imageOrder[-1]
