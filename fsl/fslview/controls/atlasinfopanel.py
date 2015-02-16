#!/usr/bin/env python
#
# atlasinfopanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import wx
import wx.html           as wxhtml

import pwidgets.elistbox as elistbox

import fsl.fslview.panel as fslpanel
import fsl.data.atlases  as atlases


log = logging.getLogger(__name__)



class AtlasListWidget(wx.Panel):

    def __init__(self, parent, atlasPanel, atlasID):

        wx.Panel.__init__(self, parent)

        self.atlasID    = atlasID
        self.atlasPanel = atlasPanel
        self.enableBox  = wx.CheckBox(self)

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.enableBox, flag=wx.EXPAND)

        self.enableBox.Bind(wx.EVT_CHECKBOX, self.onEnable)

        
    def onEnable(self, ev):

        if self.enableBox.GetValue():
            self.atlasPanel.enableAtlasInfo(self.atlasID)
        else:
            self.atlasPanel.disableAtlasInfo(self.atlasID)


# TODO
# 
# Actions to show/hide atlas overlays are managed by the AtlasPanel,
# which provides methods to do so, and maintains the state required
# to track whether an overlay is enabled/disabled. Thec
# AtlasInfoPanel and AtlasOverlayPanel  implement the GUI
# functionality, and the event handling needed to allow the user
# to toggle atlas information/overlays on/off, but management
# of the in-memory atlas images is handled by the AtlasPanel.


# Info panel, containing atlas-based regional
# proportions/labels for the current location

# Atlas list, containing a list of atlases
# that the user can choose from
class AtlasInfoPanel(fslpanel.FSLViewPanel):

    def __init__(self, parent, imageList, displayCtx, atlasPanel):
        fslpanel.FSLViewPanel.__init__(self, parent, imageList, displayCtx)


        self.atlasPanel   = atlasPanel
        self.contentPanel = wx.SplitterWindow(self)
        self.infoPanel    = wxhtml.HtmlWindow(self.notebook)
        
        self.atlasList    = elistbox.EditableListBox(
            self,
            style=(elistbox.ELB_NO_ADD    | 
                   elistbox.ELB_NO_REMOVE |
                   elistbox.ELB_NO_MOVE))

        for i, atlasDesc in enumerate(atlases.listAtlases()):
            
            self.atlasList.Append(atlasDesc.name, atlasDesc.atlasID)
            widget = AtlasListWidget(self.atlasList, atlasPanel, atlasDesc)
            self.atlasList.SetItemWidget(i, widget)        

        # The info panel contains clickable links
        # for the currently displayed regions -
        # when a link is clicked, the location
        # is centred at the corresponding region
        self.infoPanel.Bind(wxhtml.EVT_HTML_LINK_CLICKED,
                            self._infoPanelLinkClicked)

        displayCtx.addListener('location', self._name, self._locationChanged)


    def _infoPanelLinkClicked(self, ev):

        showType, atlasID, labelIndex = ev.GetLinkInfo().GetHref().split()
        labelIndex                    = int(labelIndex)
        atlas                         = self.enabledAtlases[atlasID]
        label                         = atlas.desc.labels[labelIndex]

        log.debug('{}/{} ({}) clicked'.format(atlasID, label.name, showType))

        if showType == 'summary':
            self.overlayPanel.toggleSummaryOverlay(atlas.desc)

        elif showType == 'prob':
            self.overlayPanel.toggleOverlay(atlas.desc, labelIndex, False)
        
        elif showType == 'label':
            self.overlayPanel.toggleOverlay(atlas.desc, labelIndex, True)


    def _locationChanged(self, *a):
        
        image   = self._displayCtx.getSelectedImage()
        display = self._displayCtx.getDisplayProperties(image)
        loc     = self._displayCtx.location
        text    = self.infoPanel
        loc     = transform.transform([loc], display.displayToWorldMat)[0]

        if len(self.enabledAtlases) == 0:
            text.SetPage(strings.messages['atlaspanel.chooseAnAtlas'])
            return

        if image.getXFormCode() != constants.NIFTI_XFORM_MNI_152:
            text.SetPage(strings.messages['atlaspanel.notMNISpace'])
            return

        lines = []


        titleTemplate = '<b>{}</b> (<a href="summary {} {}">Show/Hide</a>)'
        labelTemplate = '{} (<a href="label {} {}">Show/Hide</a>)'
        probTemplate  = '{:0.2f}% {} (<a href="prob {} {}">Show/Hide</a>)'

        for atlasID, atlas in self.enabledAtlases.items():

            lines.append(titleTemplate.format(atlas.desc.name, atlasID, 0))

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
 
