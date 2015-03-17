#!/usr/bin/env python
#
# orthotoolbar.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import fsl.fslview.toolbar                     as fsltoolbar
import fsl.fslview.controls.orthosettingspanel as orthosettingspanel


log = logging.getLogger(__name__)


class OrthoToolBar(fsltoolbar.FSLViewToolBar):

    
    def __init__(self, parent, imageList, displayCtx, ortho):

        import fsl.fslview.layouts as layouts

        actionz = {'more' : self.showMoreSettings}
        
        fsltoolbar.FSLViewToolBar.__init__(
            self, parent, imageList, displayCtx, actionz)
        self.orthoPanel = ortho

        orthoOpts = ortho.getSceneOptions()

        toolSpecs = layouts.layouts[self]
        targets    = {'screenshot'  : ortho,
                      'zoom'        : orthoOpts,
                      'layout'      : orthoOpts,
                      'showXCanvas' : orthoOpts,
                      'showYCanvas' : orthoOpts,
                      'showZCanvas' : orthoOpts,
                      'more'        : self}

        self.GenerateTools(toolSpecs, targets)
        

    def destroy(self):
        fsltoolbar.FSLViewToolBar.destroy(self)


    def showMoreSettings(self, *a):
        self.orthoPanel.togglePanel(
            orthosettingspanel.OrthoSettingsPanel, True, self.orthoPanel) 
