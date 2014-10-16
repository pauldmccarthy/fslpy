#!/usr/bin/env python
#
# openfileaction.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os
import os.path as op

import logging
log = logging.getLogger(__name__)

import fsl.fslview.action as action

class OpenStandardAction(action.Action):
    def __init__(self, menuItem, displayCtx, imageList):
        action.Action.__init__(self, menuItem, displayCtx, imageList)
        
        # disable the 'add standard' menu
        # item if $FSLDIR is not set
        fsldir = os.environ.get('FSLDIR', None)

        if fsldir is not None:
            self._stddir = op.join(fsldir, 'data', 'standard')
        else:
            self._stddir = None
            self.disable()
        
        
    def doAction(self, *args):
        if self._imageList.addImages(self._stddir, addToEnd=False):
            self._displayCtx.selectedImage = 0
