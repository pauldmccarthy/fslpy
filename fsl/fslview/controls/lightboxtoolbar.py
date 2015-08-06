#!/usr/bin/env python
#
# lightboxtoolbar.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import props

import fsl.fslview.toolbar as fsltoolbar
import fsl.fslview.actions as actions


class LightBoxToolBar(fsltoolbar.FSLViewToolBar):

    def __init__(self, parent, overlayList, displayCtx, lb):

        actionz = {'more' : self.showMoreSettings}
        
        fsltoolbar.FSLViewToolBar.__init__(
            self, parent, overlayList, displayCtx, actionz)
        self.lightBoxPanel = lb

        sceneOpts = lb.getSceneOptions()
        toolSpecs = [
            actions.ActionButton(lb, 'screenshot'),
            props  .Widget(      'zax'),
            props  .Widget(      'sliceSpacing', spin=False, showLimits=False),
            props  .Widget(      'zrange',       spin=False, showLimits=False),
            props  .Widget(      'zoom',         spin=False, showLimits=False),
            actions.ActionButton(self, 'more')]
        targets   = {'screenshot'   : lb,
                     'zax'          : sceneOpts,
                     'sliceSpacing' : sceneOpts,
                     'zrange'       : sceneOpts,
                     'zoom'         : sceneOpts,
                     'more'         : self}

        self.GenerateTools(toolSpecs, targets)

        
    def showMoreSettings(self, *a):
        import canvassettingspanel
        self.lightBoxPanel.togglePanel(
            canvassettingspanel.CanvasSettingsPanel,
            self.lightBoxPanel,
            floatPane=True) 
