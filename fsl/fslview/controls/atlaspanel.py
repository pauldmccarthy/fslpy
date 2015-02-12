#!/usr/bin/env python
#
# atlaspanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import wx

import pwidgets.elistbox             as elistbox
import pwidgets.notebook             as notebook

import fsl.utils.transform           as transform
import fsl.data.atlases              as atlases
import fsl.data.strings              as strings
import fsl.fslview.widgets.swappanel as swappanel
import fsl.fslview.panel             as fslpanel


log = logging.getLogger(__name__)


class AtlasListWidget(wx.Panel):

    def __init__(self, parent, atlasDesc, imageList, displayCtx, listBox):

        wx.Panel.__init__(self, parent)

        self.atlasDesc = atlasDesc

        self.enableBox = wx.CheckBox(self)

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.enableBox, flag=wx.EXPAND)


class AtlasPanel(fslpanel.FSLViewPanel):


    # actions
    def addSummaryOverlay(      self): pass
    def addProbabilisticOverlay(self): pass
    def addLabelOverlay(        self): pass


    def __init__(self, parent, imageList, displayCtx):

        fslpanel.FSLViewPanel.__init__(self, parent, imageList, displayCtx)

        self.notebook = notebook.Notebook(self)

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.notebook, flag=wx.EXPAND, proportion=1)
 
        self.SetSizer(self.sizer)

        # Info panel, containing atlas-based regional
        # proportions/labels for the current location
        self.infoPanel = wx.TextCtrl(self.notebook, style=(wx.TE_MULTILINE |
                                                           wx.TE_READONLY))

        # Atlas list, containing a list of atlases
        # that the user can choose from
        self.atlasList = elistbox.EditableListBox(
            self.atlasListPanel,
            style=(elistbox.ELB_NO_ADD    | 
                   elistbox.ELB_NO_REMOVE |
                   elistbox.ELB_NO_MOVE))

        # Overlay panel, containing a list of regions,
        # allowing the user to add/remove overlays
        self.overlayPanel = wx.Panel(self.notebook)
        
        self.notebook.Add(self.infoPanel,
                          strings.labels['AtlasPanel.infoPanel'])
        self.notebook.Add(self.atlasListPanel,
                          strings.labels['AtlasPanel.atlasListPanel'])
        self.notebook.Add(self.overlayPanel,
                          strings.labels['AtlasPanel.overlayPanel'])
