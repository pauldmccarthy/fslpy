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

        icns = {
            'screenshot'  : icons.findImageFile('camera'),
            'showXCanvas' : icons.findImageFile('sagittalSlice'),
            'showYCanvas' : icons.findImageFile('coronalSlice'),
            'showZCanvas' : icons.findImageFile('axialSlice'),
            'more'        : icons.findImageFile('gear'),

            'layout' : {
                'horizontal' : icons.findImageFile('horizontalLayout'),
                'vertical'   : icons.findImageFile('verticalLayout'),
                'grid'       : icons.findImageFile('gridLayout'),
            }
        }

        toolSpecs = [

            actions.ActionButton(self, 'more', icon=icns['more']),
            actions.ActionButton(ortho, 'screenshot', icon=icns['screenshot']),
            props  .Widget('showXCanvas', icon=icns['showXCanvas']),
            props  .Widget('showYCanvas', icon=icns['showYCanvas']),
            props  .Widget('showZCanvas', icon=icns['showZCanvas']),
            props  .Widget('layout', icons=icns['layout']), 
            props  .Widget('zoom', spin=False, showLimits=False),

 
        ]
        
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
