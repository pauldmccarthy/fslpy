#!/usr/bin/env python
#
# orthotoolbar.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import props

import fsl.fslview.toolbar as fsltoolbar
import fsl.fslview.icons   as icons
import fsl.fslview.actions as actions


class OrthoToolBar(fsltoolbar.FSLViewToolBar):

    
    def __init__(self, parent, overlayList, displayCtx, ortho):

        actionz = {'more' : self.showMoreSettings}
        
        fsltoolbar.FSLViewToolBar.__init__(
            self, parent, overlayList, displayCtx, actionz)
        self.orthoPanel = ortho

        orthoOpts = ortho.getSceneOptions()

        toolSpecs = [
            actions.ActionButton(ortho, 'screenshot'),
            props  .Widget('zoom', spin=False, showLimits=False),
            props  .Widget('layout'),
            props  .Widget('showXCanvas',
                           icon=icons.findImageFile('showxcanvas', 32)[0]),
            props  .Widget('showYCanvas',
                           icon=icons.findImageFile('showycanvas', 32)[0]),
            props  .Widget('showZCanvas',
                           icon=icons.findImageFile('showzcanvas', 32)[0]),
            actions.ActionButton(self,
                                 'more',
                                 icon=icons.findImageFile('gear', 32)[0])]
        
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
        self.orthoPanel.togglePanel(canvassettingspanel.CanvasSettingsPanel,
                                    self.orthoPanel,
                                    floatPane=True)
