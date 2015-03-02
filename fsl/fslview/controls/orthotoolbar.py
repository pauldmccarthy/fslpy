#!/usr/bin/env python
#
# orthotoolbar.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import wx
import props

import fsl.data.strings                        as strings
import fsl.fslview.panel                       as fslpanel
import fsl.fslview.controls.orthosettingspanel as orthosettingspanel


log = logging.getLogger(__name__)


class OrthoToolBar(fslpanel.FSLViewToolBar):

    
    def __init__(self, parent, imageList, displayCtx, ortho):
        
        fslpanel.FSLViewToolBar.__init__(self, parent, imageList, displayCtx)
        self.orthoPanel = ortho

        self.screenshot = wx.Button(
            self, label=strings.actions[ortho, 'screenshot'])
        self.colourBar  = wx.Button(
            self, label=strings.actions[ortho, 'toggleColourBar']) 

        # You need to update the props.build/widgets,
        # so you can include these type-specific
        # options in ViewItem specifications
        self.zoom   = props.makeWidget(self,
                                       ortho,
                                       'zoom',
                                       slider=True,
                                       spin=False,
                                       showLimits=False)
        
        self.layout = props.makeWidget(self, ortho, 'layout')
        self.showX  = props.makeWidget(self, ortho, 'showXCanvas')
        self.showY  = props.makeWidget(self, ortho, 'showYCanvas')
        self.showZ  = props.makeWidget(self, ortho, 'showZCanvas')
        
        self.more   = wx.Button(self, label=strings.labels[self, 'more'])

        ortho.getAction('screenshot').bindToWidget(
            self, wx.EVT_BUTTON, self.screenshot)
        ortho.getAction('toggleColourBar').bindToWidget(
            self, wx.EVT_BUTTON, self.colourBar)

        self.more.Bind(wx.EVT_BUTTON, self._onMoreButton)

        self.AddTool(self.screenshot)
        self.AddTool(self.colourBar)
        self.AddTool(self.layout,  strings.properties[ortho, 'layout'])
        self.AddTool(self.zoom,    strings.properties[ortho, 'zoom'])
        self.AddTool(self.showX,   strings.properties[ortho, 'showXCanvas'])
        self.AddTool(self.showY,   strings.properties[ortho, 'showYCanvas'])
        self.AddTool(self.showZ,   strings.properties[ortho, 'showZCanvas'])
        self.AddTool(self.more)
        

    def destroy(self):
        fslpanel.FSLViewToolBar.destroy(self)


    def _onMoreButton(self, ev):
        self.GetParent().togglePanel(
            orthosettingspanel.OrthoSettingsPanel, True, self.orthoPanel) 
