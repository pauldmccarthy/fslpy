#!/usr/bin/env python
#
# orthodisplaytoolbar.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import fsl.fslview.panel as fslpanel


log = logging.getLogger(__name__)


class OrthoDisplayToolBar(fslpanel.FSLViewToolBar):

    
    def __init__(self, parent, imageList, displayCtx, orthoPanel):
        
        fslpanel.FSLViewToolBar.__init__(self, parent, imageList, displayCtx)
        self.orthoPanel = orthoPanel
        

    def destroy(self):
        fslpanel.FSLViewToolBar.destroy(self)
