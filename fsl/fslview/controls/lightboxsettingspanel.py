#!/usr/bin/env python
#
# lightboxsettingspanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import wx

import props

import fsl.fslview.panel as fslpanel


log = logging.getLogger(__name__)


class LightBoxSettingsPanel(fslpanel.FSLViewPanel):

    def __init__(self, parent, overlayList, displayCtx, lb):
        fslpanel.FSLViewPanel.__init__(self, parent, overlayList, displayCtx)

        import fsl.fslview.layouts as layouts

        self.panel = wx.ScrolledWindow(self)
        self.panel.SetScrollRate(0, 5)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        self.sizer.Add(self.panel, flag=wx.EXPAND, proportion=1)

        self.canvasSettings = props.buildGUI(
            self.panel, lb, layouts.layouts['CanvasPanel'])
        
        self.divider1 = wx.StaticLine(
            self.panel, size=(-1, -1), style=wx.LI_HORIZONTAL)
        
        self.sceneSettings = props.buildGUI(
            self.panel,
            lb.getSceneOptions(),
            layouts.layouts['SceneOpts']) 

        self.divider2 = wx.StaticLine(
            self.panel, size=(-1, -1), style=wx.LI_HORIZONTAL)

        self.lightBoxSettings = props.buildGUI(
            self.panel,
            lb.getSceneOptions(),
            layouts.layouts['LightBoxPanel'])

        self.panelSizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.panelSizer)

        flags = wx.wx.EXPAND | wx.ALIGN_CENTRE | wx.ALL
        
        self.panelSizer.Add(self.canvasSettings,    border=20, flag=flags)
        self.panelSizer.Add(self.divider1,                     flag=flags)
        self.panelSizer.Add(self.sceneSettings,     border=20, flag=flags)
        self.panelSizer.Add(self.divider2,                     flag=flags)
        self.panelSizer.Add(self.lightBoxSettings,  border=20, flag=flags)

        self.sizer     .Layout()
        self.panelSizer.Layout()

        size = self.panelSizer.GetMinSize()

        self.SetMinSize((size[0], size[1] / 3.0))
