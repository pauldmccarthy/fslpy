#!/usr/bin/env python
#
# orthotoolbar.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import props

import fsl.data.strings                        as strings
import fsl.fslview.actions                     as actions
import fsl.fslview.panel                       as fslpanel
import fsl.fslview.controls.orthosettingspanel as orthosettingspanel


log = logging.getLogger(__name__)


class OrthoToolBar(fslpanel.FSLViewToolBar):

    
    def __init__(self, parent, imageList, displayCtx, ortho):

        import fsl.fslview.layouts as layouts

        actionz = {'more' :  self.showMoreSettings}
        
        fslpanel.FSLViewToolBar.__init__(
            self, parent, imageList, displayCtx, actionz)
        self.orthoPanel = ortho

        toolSpecs = layouts.layouts[self]

        for toolSpec in toolSpecs:
            if toolSpec.key == 'more':
                tool = props.buildGUI(self, self,  toolSpec)
            else: 
                tool = props.buildGUI(self, ortho, toolSpec)

            if isinstance(toolSpec, actions.ActionButton):
                label = None
            else:
                label = strings.properties[ortho, toolSpec.key]

            self.AddTool(tool, label)
        

    def destroy(self):
        fslpanel.FSLViewToolBar.destroy(self)


    def showMoreSettings(self, *a):
        self.GetParent().togglePanel(
            orthosettingspanel.OrthoSettingsPanel, True, self.orthoPanel) 
