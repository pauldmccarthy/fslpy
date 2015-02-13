#!/usr/bin/env python
#
# atlaspanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import            wx
import wx.html as wxhtml
import numpy   as np

import pwidgets.elistbox             as elistbox
import pwidgets.notebook             as notebook

import fsl.utils.transform           as transform
import fsl.data.image                as fslimage
import fsl.data.atlases              as atlases
import fsl.data.strings              as strings
import fsl.data.constants            as constants
import fsl.fslview.panel             as fslpanel


log = logging.getLogger(__name__)


class AtlasListWidget(wx.Panel):

    def __init__(self, parent, atlasDesc, atlasPanel):

        wx.Panel.__init__(self, parent)

        self.atlasDesc  = atlasDesc
        self.atlasPanel = atlasPanel
        self.enableBox  = wx.CheckBox(self)

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.enableBox, flag=wx.EXPAND)

        self.enableBox.Bind(wx.EVT_CHECKBOX, self.onEnable)

    def onEnable(self, ev):

        if self.enableBox.GetValue():
            self.atlasPanel.enableAtlasInfo(self.atlasDesc.atlasID)
        else:
            self.atlasPanel.disableAtlasInfo(self.atlasDesc.atlasID)
                    


class AtlasPanel(fslpanel.FSLViewPanel):


    def __init__(self, parent, imageList, displayCtx):

        fslpanel.FSLViewPanel.__init__(self, parent, imageList, displayCtx)

        self.notebook = notebook.Notebook(self)

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.notebook, flag=wx.EXPAND, proportion=1)
 
        self.SetSizer(self.sizer)

        # Info panel, containing atlas-based regional
        # proportions/labels for the current location
        self.infoPanel = wxhtml.HtmlWindow(self.notebook)

        # Atlas list, containing a list of atlases
        # that the user can choose from
        self.atlasList = elistbox.EditableListBox(
            self.notebook,
            style=(elistbox.ELB_NO_ADD    | 
                   elistbox.ELB_NO_REMOVE |
                   elistbox.ELB_NO_MOVE))

        # Overlay panel, containing a list of regions,
        # allowing the user to add/remove overlays
        self.overlayPanel = wx.Panel(self.notebook)
        
        self.notebook.AddPage(self.infoPanel,
                              strings.labels['AtlasPanel.infoPanel'])
        self.notebook.AddPage(self.atlasList,
                              strings.labels['AtlasPanel.atlasListPanel'])
        self.notebook.AddPage(self.overlayPanel,
                              strings.labels['AtlasPanel.overlayPanel'])

        # The info panel contains clickable links
        # for the currently displayed regions -
        # when a link is clicked, the location
        # is centred at the corresponding region
        self.infoPanel.Bind(wxhtml.EVT_HTML_LINK_CLICKED,
                            self._infoPanelLinkClicked)


        # Set up the list of atlases to choose from
        self.atlasDescs     = atlases.listAtlases()
        self.enabledAtlases = {}

        listItems = sorted(self.atlasDescs.items(), key=lambda (a, d): d.name)

        for i, (atlasID, desc) in enumerate(listItems):
            
            self.atlasList.Append(desc.name, atlasID)
            widget = AtlasListWidget(self.atlasList, desc, self)
            self.atlasList.SetItemWidget(i, widget)

        displayCtx.addListener('location', self._name, self._locationChanged)


    def _infoPanelLinkClicked(self, ev):

        atlasID, labelIndex = ev.GetLinkInfo().GetHref().split()
        labelIndex          = int(labelIndex)
        atlas               = self.enabledAtlases[atlasID]
        label               = atlas.desc.labels[labelIndex]

        log.debug('{}/{} clicked'.format(atlasID, label.name)) 

        if isinstance(atlas, atlases.ProbabilisticAtlas):
            pass
        
        elif isinstance(atlas, atlases.LabelAtlas):
            self.toggleLabelOverlay(atlasID, labelIndex)


        
    def enableAtlasInfo(self, atlasID):

        desc       = self.atlasDescs[atlasID]
        atlasImage = atlases.loadAtlas(desc)

        self.enabledAtlases[atlasID] = atlasImage

        self._locationChanged()

        
    def disableAtlasInfo(self, atlasID):

        self.enabledAtlases.pop(atlasID, None)
        self._locationChanged()

        
    def toggleSummaryOverlay(self, atlasID):
        pass

    
    def toggleProbabilisticOverlay(self, atlasID, labelIndex):
        pass

    
    def toggleLabelOverlay(self, atlasID, labelIndex):

        desc        = self.atlasDescs[atlasID]
        overlayName = '{}/{}'.format(atlasID, desc.labels[labelIndex].name)
        overlay     = self._imageList.find(overlayName)

        if overlay is not None:
            self._imageList.remove(overlay)

            log.debug('Removing overlay {}'.format(overlayName))

        else:
            atlas = self.enabledAtlases.get(atlasID, None)
            if atlas is None:
                atlas = atlases.loadAtlas(self.atlasDescs[atlasID], True)

            if   desc.atlasType == 'probabilistic': labelVal = labelIndex + 1
            elif desc.atlasType == 'label':         labelVal = labelIndex 
            
            mask = np.zeros(atlas.shape, dtype=np.uint8)
            mask[atlas.data == labelIndex] = labelVal

            overlay = fslimage.Image(
                mask,
                atlas.voxToWorldMat,
                name=overlayName)
            overlay.imageType = 'mask'

            log.debug('Adding overlay {}'.format(overlayName))

            self._imageList.append(overlay)
            
            display = self._displayCtx.getDisplayProperties(overlay)
            display.getDisplayOpts().colour = np.random.random(3)
            

 


    def _locationChanged(self, *a):
        image   = self._displayCtx.getSelectedImage()
        display = self._displayCtx.getDisplayProperties(image)
        loc     = self._displayCtx.location
        text    = self.infoPanel

        loc = transform.transform([loc], display.displayToWorldMat)[0]

        if image.getXFormCode() != constants.NIFTI_XFORM_MNI_152:
            text.SetPage(strings.messages['atlaspanel.unknownLocation'])
            return

        lines = []

        labelTemplate = """{}
        (<a href="{} {}">Show/Hide</a>)
        """
        probTemplate = """
        {:0.2f}% {}
        (<a href="{} {}">Show/Hide</a>)
        """

        for atlasID, atlas in self.enabledAtlases.items():

            lines.append('<b>{}</b>'.format(atlas.desc.name))

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
                label    = atlas.desc.labels[labelVal]
                lines.append(labelTemplate.format(label.name,
                                                  atlasID,
                                                  label.index,
                                                  atlasID,
                                                  label.index))

        text.SetPage('<br>'.join(lines))
