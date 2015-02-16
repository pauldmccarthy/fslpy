#!/usr/bin/env python
#
# atlaspanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import                    wx
import wx.html         as wxhtml
import wx.lib.newevent as wxevent
import numpy           as np

import pwidgets.elistbox             as elistbox
import pwidgets.notebook             as notebook

import fsl.utils.transform                    as transform
import fsl.data.image                         as fslimage
import fsl.data.atlases                       as atlases
import fsl.data.strings                       as strings
import fsl.data.constants                     as constants
import fsl.fslview.panel                      as fslpanel
import fsl.fslview.controls.atlasoverlaypanel as atlasoverlaypanel
import fsl.fslview.controls.atlasinfopanel    as atlasinfopanel


log = logging.getLogger(__name__)


class AtlasPanel(fslpanel.FSLViewPanel):


    def __init__(self, parent, imageList, displayCtx):

        fslpanel.FSLViewPanel.__init__(self, parent, imageList, displayCtx)

        self.atlasDescs     = sorted(atlases.listAtlases(),
                                     key=lambda d: d.name)
        self.enabledAtlases = {}

        self.notebook = notebook.Notebook(self)

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.notebook, flag=wx.EXPAND, proportion=1)
 
        self.SetSizer(self.sizer)

        # Temporary
        self.SetMaxSize((-1, 200))

        self.atlasInfoPanel = atlasinfopanel.AtlasInfoPanel(
            self.notebook, imageList, displayCtx, self)

        # Overlay panel, containing a list of regions,
        # allowing the user to add/remove overlays
        self.overlayPanel = atlasoverlaypanel.AtlasOverlayPanel(
            self.notebook, imageList, displayCtx, self)
        
        self.notebook.AddPage(self.infoPanel,
                              strings.labels[self.infoPanel])
        self.notebook.AddPage(self.overlayPanel,
                              strings.labels[self.overlayPanel])

        self.notebook.ShowPage(0)



        self.Layout()

    
    def enableAtlasInfo(self, atlasDesc):

        atlasImage = atlases.loadAtlas(atlasDesc)
        self.enabledAtlases[atlasDesc.atlasID] = atlasImage

        self._locationChanged()

        
    def disableAtlasInfo(self, atlasDesc):

        self.enabledAtlases.pop(atlasDesc.atlasID, None)
        self._locationChanged()

