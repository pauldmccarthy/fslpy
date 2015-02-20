#!/usr/bin/env python
#
# atlasinfopanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import wx
import wx.html             as wxhtml

import pwidgets.elistbox   as elistbox

import fsl.fslview.panel   as fslpanel
import fsl.data.atlases    as atlases
import fsl.data.strings    as strings
import fsl.data.constants  as constants
import fsl.utils.transform as transform


log = logging.getLogger(__name__)


class AtlasListWidget(wx.CheckBox):

    def __init__(self, parent, atlasInfoPanel, atlasID):

        wx.CheckBox.__init__(self, parent)

        self.atlasID        = atlasID
        self.atlasInfoPanel = atlasInfoPanel

        self.Bind(wx.EVT_CHECKBOX, self.onEnable)

        
    def onEnable(self, ev):

        if self.GetValue():
            self.atlasInfoPanel.enableAtlasInfo(self.atlasID)
        else:
            self.atlasInfoPanel.disableAtlasInfo(self.atlasID)


# Info panel, containing atlas-based regional
# proportions/labels for the current location

# Atlas list, containing a list of atlases
# that the user can choose from
class AtlasInfoPanel(fslpanel.FSLViewPanel):

    def __init__(self, parent, imageList, displayCtx, atlasPanel):
        fslpanel.FSLViewPanel.__init__(self, parent, imageList, displayCtx)

        self.enabledAtlases = {}
        self.atlasPanel     = atlasPanel
        self.contentPanel   = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self.infoPanel      = wxhtml.HtmlWindow(self.contentPanel)
        self.atlasList      = elistbox.EditableListBox(
            self.contentPanel,
            style=(elistbox.ELB_NO_ADD    | 
                   elistbox.ELB_NO_REMOVE |
                   elistbox.ELB_NO_MOVE))

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.contentPanel, flag=wx.EXPAND, proportion=1)
        self.SetSizer(self.sizer)

        self.contentPanel.SetMinimumPaneSize(50)
        self.contentPanel.SplitVertically(self.atlasList, self.infoPanel) 
        self.contentPanel.SetSashGravity(0.4)
        
        for i, atlasDesc in enumerate(atlases.listAtlases()):
            
            self.atlasList.Append(atlasDesc.name, atlasDesc.atlasID)
            widget = AtlasListWidget(self.atlasList, self, atlasDesc.atlasID)
            self.atlasList.SetItemWidget(i, widget)        

        # The info panel contains clickable links
        # for the currently displayed regions -
        # when a link is clicked, the location
        # is centred at the corresponding region
        self.infoPanel.Bind(wxhtml.EVT_HTML_LINK_CLICKED,
                            self._infoPanelLinkClicked)

        displayCtx.addListener('location',
                               self._name,
                               self._locationChanged)
        displayCtx.addListener('selectedImage',
                               self._name,
                               self._locationChanged)

        self._locationChanged()
        self.Layout()

        
    def destroy(self):
        """Must be called when this :class:`AtlasInfoPanel` is to be
        destroyed. De-registers various property listeners.
        """
        fslpanel.FSLViewPanel.destroy(self)

        self._displayCtx.removeListener('location',      self._name)
        self._displayCtx.removeListener('selectedImage', self._name)


    def enableAtlasInfo(self, atlasID):
        self.enabledAtlases[atlasID] = self.atlasPanel.loadAtlas(atlasID,
                                                                 False)
        self._locationChanged()

        
    def disableAtlasInfo(self, atlasID):
        self.enabledAtlases.pop(atlasID)
        self.atlasPanel.clearAtlas(atlasID, False)
        self._locationChanged()


    def _infoPanelLinkClicked(self, ev):

        showType, atlasID, labelIndex = ev.GetLinkInfo().GetHref().split()
        
        try:    labelIndex = int(labelIndex)
        except: labelIndex = None

        # showType is one of 'prob', 'label', or
        # 'summary'; the summary parameter controls
        # whether a probabilstic or label image
        # is loaded
        summary = showType != 'prob'

        self.atlasPanel.toggleOverlay(atlasID, labelIndex, summary)


    def _locationChanged(self, *a):
        
        image   = self._displayCtx.getSelectedImage()
        display = self._displayCtx.getDisplayProperties(image)
        loc     = self._displayCtx.location
        text    = self.infoPanel
        loc     = transform.transform([loc], display.displayToWorldMat)[0]

        if image.getXFormCode() != constants.NIFTI_XFORM_MNI_152:
            text.SetPage(strings.messages['AtlasInfoPanel.notMNISpace'])
            return

        if len(self.enabledAtlases) == 0:
            text.SetPage(strings.messages['AtlasInfoPanel.chooseAnAtlas'])
            return

        lines         = []
        titleTemplate = '<b>{}</b> (<a href="summary {} {}">Show/Hide</a>)'
        labelTemplate = '{} (<a href="label {} {}">Show/Hide</a>)'
        probTemplate  = '{:0.1f}% {} (<a href="prob {} {}">Show/Hide</a>)'

        for atlasID in self.enabledAtlases:

            atlas = self.enabledAtlases[atlasID]

            lines.append(titleTemplate.format(atlas.desc.name, atlasID, None))

            if isinstance(atlas, atlases.ProbabilisticAtlas):
                proportions = atlas.proportions(loc)

                for label, prop in zip(atlas.desc.labels, proportions):
                    if prop == 0.0:
                        continue
                    lines.append(probTemplate.format(prop,
                                                     label.name,
                                                     atlasID,
                                                     label.index,
                                                     atlasID,
                                                     label.index))
            
            elif isinstance(atlas, atlases.LabelAtlas):
                
                labelVal = atlas.label(loc)
                label    = atlas.desc.labels[int(labelVal)]
                lines.append(labelTemplate.format(label.name,
                                                  atlasID,
                                                  label.index,
                                                  atlasID,
                                                  label.index))

        text.SetPage('<br>'.join(lines))

        text.Refresh()
