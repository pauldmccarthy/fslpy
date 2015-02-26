#!/usr/bin/env python
#
# orthodisplaytoolbar.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import wx
import props

import fsl.data.strings  as strings
import fsl.fslview.panel as fslpanel


log = logging.getLogger(__name__)


class OrthoDisplayToolBar(fslpanel.FSLViewToolBar):

    
    def __init__(self, parent, imageList, displayCtx, ortho):
        
        fslpanel.FSLViewToolBar.__init__(self, parent, imageList, displayCtx)
        self.orthoPanel = ortho

        self.screenshot = wx.Button(
            self, label=strings.actions[ortho, 'screenshot'])
        self.colourBar  = wx.Button(
            self, label=strings.actions[ortho, 'toggleColourBar']) 

        self.profile = props.makeWidget(self, ortho, 'profile')
        self.zoom    = props.makeWidget(self,
                                        ortho,
                                        'zoom',
                                        slider=True,
                                        spin=False,
                                        showLimits=False)
        self.layout = props.makeWidget(self, ortho, 'layout')
        self.showX  = props.makeWidget(self, ortho, 'showXCanvas')
        self.showY  = props.makeWidget(self, ortho, 'showYCanvas')
        self.showZ  = props.makeWidget(self, ortho, 'showZCanvas')

        ortho.getAction('screenshot').bindToWidget(
            self, wx.EVT_BUTTON, self.screenshot)
        ortho.getAction('toggleColourBar').bindToWidget(
            self, wx.EVT_BUTTON, self.colourBar) 

        self.AddTool(self.screenshot)
        self.AddTool(self.colourBar)
        self.AddTool(self.profile, strings.properties[ortho, 'profile'])
        self.AddTool(self.layout,  strings.properties[ortho, 'layout'])
        self.AddTool(self.zoom,    strings.properties[ortho, 'zoom'])
        self.AddTool(self.showX,   strings.properties[ortho, 'showXCanvas'])
        self.AddTool(self.showY,   strings.properties[ortho, 'showYCanvas'])
        self.AddTool(self.showZ,   strings.properties[ortho, 'showZCanvas'])
        

    def destroy(self):
        fslpanel.FSLViewToolBar.destroy(self)
