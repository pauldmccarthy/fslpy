#!/usr/bin/env python
#
# lightboxtoolbar.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import fsl.fslview.toolbar                        as fsltoolbar
import fsl.fslview.controls.lightboxsettingspanel as lightboxsettingspanel


log = logging.getLogger(__name__)


class LightBoxToolBar(fsltoolbar.FSLViewToolBar):

    def __init__(self, parent, overlayList, displayCtx, lb):

        import fsl.fslview.layouts as layouts

        actionz = {'more' : self.showMoreSettings}
        
        fsltoolbar.FSLViewToolBar.__init__(
            self, parent, overlayList, displayCtx, actionz)
        self.lightBoxPanel = lb

        sceneOpts = lb.getSceneOptions()

        toolSpecs = layouts.layouts[self]

        # TODO this is dodgy - there needs to be a
        # way to have this automatically set up.
        #
        # 1. Add the ability to associate arbitrary
        #    data with a toolspec (modify props.ViewItem
        #    to allow a value to be set)
        #
        # 2. Update layouts.widget and actions.ActionButton
        #    to set that value to the target class
        #
        # 3. Here, loop through the toolspecs, check
        #    the target class, and set the instance
        #    appropriately
        targets   = {'screenshot'   : lb,
                     'zax'          : sceneOpts,
                     'sliceSpacing' : sceneOpts,
                     'zrange'       : sceneOpts,
                     'zoom'         : sceneOpts,
                     'more'         : self}

        self.GenerateTools(toolSpecs, targets)


    def destroy(self):
        fsltoolbar.FSLViewToolBar.destroy(self)

    def showMoreSettings(self, *a):
        self.lightBoxPanel.togglePanel(
            lightboxsettingspanel.LightBoxSettingsPanel,
            True,
            self.lightBoxPanel) 
