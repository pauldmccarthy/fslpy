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
        
        fslpanel.FSLViewToolBar.__init__(self, parent, imageList, displayCtx)
        self.lightBoxPanel = lb

        self.screenshot = wx.Button(
            self, label=strings.actions[lb, 'screenshot'])
        self.colourBar  = wx.Button(
            self, label=strings.actions[lb, 'toggleColourBar'])

        self.zax            = props.makeWidget(self, lb, 'zax')
        self.sliceSpacing   = props.makeWidget(
            self, lb, 'sliceSpacing', spin=False, showLimits=False)
        self.zrange         = props.makeWidget(
            self, lb, 'zrange',       spin=False, showLimits=False)

        self.zoom = props.makeWidget(self,
                                     lb,
                                     'zoom',
                                     slider=True,
                                     spin=False,
                                     showLimits=False)


        self.more = wx.Button(self, label=strings.labels[self, 'more'])
        
        lb.getAction('screenshot').bindToWidget(
            self, wx.EVT_BUTTON, self.screenshot)
        lb.getAction('toggleColourBar').bindToWidget(
            self, wx.EVT_BUTTON, self.colourBar)
        
        self.more.Bind(wx.EVT_BUTTON, self._onMoreButton)

        def label(prop):
            return strings.properties[lb, prop]

        self.AddTool(self.screenshot)
        self.AddTool(self.colourBar)
        self.AddTool(self.zax,            label('zax'))
        self.AddTool(self.zoom,           label('zoom'))
        self.AddTool(self.zrange,         label('zrange'))
        self.AddTool(self.sliceSpacing,   label('sliceSpacing'))
        self.AddTool(self.more)

    def destroy(self):
        fslpanel.FSLViewToolBar.destroy(self)

    def _onMoreButton(self, ev):
        self.GetParent().toggleControlPanel(
            lightboxsettingspanel.LightBoxSettingsPanel,
            True,
            self.lightBoxPanel) 
