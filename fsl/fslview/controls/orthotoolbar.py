#!/usr/bin/env python
#
# orthotoolbar.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import fsl.fslview.toolbar as fsltoolbar


class OrthoToolBar(fsltoolbar.FSLViewToolBar):

    
    def __init__(self, parent, overlayList, displayCtx, ortho):

        import fsl.fslview.layouts as layouts

        actionz = {'more' : self.showMoreSettings}
        
        fsltoolbar.FSLViewToolBar.__init__(
            self, parent, overlayList, displayCtx, actionz)
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

        
    def showMoreSettings(self, *a):
        import canvassettingspanel
        self.orthoPanel.togglePanel(
            canvassettingspanel.CanvasSettingsPanel, True, self.orthoPanel) 
