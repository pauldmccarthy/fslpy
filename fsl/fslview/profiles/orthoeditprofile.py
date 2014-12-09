#!/usr/bin/env python
#
# orthoeditprofile.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)


def register(canvasPanel, imageList,  displayCtx):
    return OrthoEditProfile(canvasPanel, imageList,  displayCtx)


def deregister(orthoEditProf):
    orthoEditProf.deregister()


class OrthoEditProfile(object):

    def __init__(self, canvasPanel, imageList, displayCtx):
        self._canvasPanel = canvasPanel
        self._imageList   = imageList
        self._displayCtx  = displayCtx
        self._name        = '{}_{}'.format(self.__class__.__name__, id(self))

        self.register()

        
    def register(self):
        pass

    
    def deregister(self):
        pass    
