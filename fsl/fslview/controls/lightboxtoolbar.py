#!/usr/bin/env python
#
# lightboxtoolbar.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import wx

import props

import fsl.data.strings                           as strings
import fsl.fslview.panel                          as fslpanel
import fsl.fslview.controls.lightboxsettingspanel as lightboxsettingspanel


log = logging.getLogger(__name__)


class LightBoxToolBar(fslpanel.FSLViewToolBar):

    def __init__(self, parent, imageList, displayCtx, lb):

        import fsl.fslview.layouts as layouts

        actionz = {'more' : self.showMoreSettings}
        
        fslpanel.FSLViewToolBar.__init__(
            self, parent, imageList, displayCtx, actionz)
        self.lightBoxPanel = lb

        toolSpecs = layouts.layouts[self]
        targets   = {s : self if s.key == 'more' else lb for s in toolSpecs}

        self.GenerateTools(toolSpecs, targets)


    def destroy(self):
        fslpanel.FSLViewToolBar.destroy(self)

    def showMoreSettings(self, ev):
        self.GetParent().togglePanel(
            lightboxsettingspanel.LightBoxSettingsPanel,
            True,
            self.lightBoxPanel) 
