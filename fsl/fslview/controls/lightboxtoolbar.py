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

    def __init__(self, parent, imageList, displayCtx, lb):

        import fsl.fslview.layouts as layouts

        actionz = {'more' : self.showMoreSettings}
        
        fsltoolbar.FSLViewToolBar.__init__(
            self, parent, imageList, displayCtx, actionz)
        self.lightBoxPanel = lb

        toolSpecs = layouts.layouts[self]
        targets   = {s : self if s.key == 'more' else lb for s in toolSpecs}

        self.GenerateTools(toolSpecs, targets)


    def destroy(self):
        fsltoolbar.FSLViewToolBar.destroy(self)

    def showMoreSettings(self, *a):
        self.lightBoxPanel.togglePanel(
            lightboxsettingspanel.LightBoxSettingsPanel,
            True,
            self.lightBoxPanel) 
