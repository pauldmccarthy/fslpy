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
        self._imageList.addImages()
