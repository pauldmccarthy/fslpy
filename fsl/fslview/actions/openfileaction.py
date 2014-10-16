#!/usr/bin/env python
#
# openfileaction.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import fsl.fslview.action as action

class OpenFileAction(action.Action):
    def doAction(self, *args):
        
        if self._imageList.addImages():
            self._displayCtx.selectedImage = len(self._imageList) - 1
