#!/usr/bin/env python
#
# orthotoolbar.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import fsl.fslview.panel                       as fslpanel
import fsl.fslview.controls.orthosettingspanel as orthosettingspanel


log = logging.getLogger(__name__)


class OrthoToolBar(fslpanel.FSLViewToolBar):

    
    def __init__(self, parent, imageList, displayCtx, ortho):

        import fsl.fslview.layouts as layouts

        actionz = {'more' : self.showMoreSettings}
        
        fslpanel.FSLViewToolBar.__init__(
            self, parent, imageList, displayCtx, actionz)
        self.orthoPanel = ortho

        toolSpecs = layouts.layouts[self]
        targets   = {s : self if s.key == 'more' else ortho for s in toolSpecs}

        self.GenerateTools(toolSpecs, targets)
        

    def destroy(self):
        fslpanel.FSLViewToolBar.destroy(self)


    def showMoreSettings(self, *a):
        self.GetParent().togglePanel(
            orthosettingspanel.OrthoSettingsPanel, True, self.orthoPanel) 
