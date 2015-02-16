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

    def __init__(self, parent, atlasPanel, atlasDesc):

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
        self.infoPanel.SetMinSize((-1, 100))

        # Atlas list, containing a list of atlases
        # that the user can choose from
        self.atlasPanel  = wx.Panel(self.notebook)
        self.atlasFilter = wx.TextCtrl(self.atlasPanel)
        self.atlasList   = elistbox.EditableListBox(
            self.atlasPanel,
            style=(elistbox.ELB_NO_ADD    | 
                   elistbox.ELB_NO_REMOVE |
                   elistbox.ELB_NO_MOVE))

        # Overlay panel, containing a list of regions,
        # allowing the user to add/remove overlays
        self.overlayPanel  = wx.Panel(self.notebook)
        
        self.notebook.AddPage(self.infoPanel,
                              strings.labels['AtlasPanel.infoPanel'])
        self.notebook.AddPage(self.atlasPanel,
                              strings.labels['AtlasPanel.atlasListPanel'])
        self.notebook.AddPage(self.overlayPanel,
                              strings.labels['AtlasPanel.overlayPanel'])

        self.notebook.ShowPage(0)

        # The info panel contains clickable links
        # for the currently displayed regions -
        # when a link is clicked, the location
        # is centred at the corresponding region
        self.infoPanel.Bind(wxhtml.EVT_HTML_LINK_CLICKED,
                            self._infoPanelLinkClicked)

        # Set up the atlas list, allowing the
        # user to choose which atlases information
        # (in the info panel) is shown for
        self.atlasSizer = wx.BoxSizer(wx.VERTICAL)
        self.atlasSizer.Add(self.atlasFilter, flag=wx.EXPAND)
        self.atlasSizer.Add(self.atlasList,   flag=wx.EXPAND, proportion=1)
        self.atlasPanel.SetSizer(self.atlasSizer)

        self.atlasFilter.Bind(wx.EVT_TEXT, self._onAtlasFilter)
        
        self.atlasDescs     = atlases.listAtlases()
        self.enabledAtlases = {}

        listItems = sorted(self.atlasDescs.items(), key=lambda (a, d): d.name)

        for i, (atlasID, desc) in enumerate(listItems):
            
            self.atlasList.Append(desc.name, atlasID)
            widget = AtlasListWidget(self.atlasList, self, desc)
            self.atlasList.SetItemWidget(i, widget)

        displayCtx.addListener('location', self._name, self._locationChanged)

        self.Layout()


    def _infoPanelLinkClicked(self, ev):

        showType, atlasID, labelIndex = ev.GetLinkInfo().GetHref().split()
        labelIndex                    = int(labelIndex)
        atlas                         = self.enabledAtlases[atlasID]
        label                         = atlas.desc.labels[labelIndex]

        log.debug('{}/{} ({}) clicked'.format(atlasID, label.name, showType))

        if showType == 'summary':
            self.toggleSummaryOverlay(atlasID)

        elif showType == 'prob':
            self.toggleOverlay(atlasID, labelIndex, False)
        
        elif showType == 'label':
            self.toggleOverlay(atlasID, labelIndex, True)


    def _onAtlasFilter(self, ev):
        filterStr = self.atlasFilter.GetValue().lower()
        self.atlasList.ApplyFilter(filterStr, ignoreCase=True)

    
    def enableAtlasInfo(self, atlasID):

        desc       = self.atlasDescs[atlasID]
        atlasImage = atlases.loadAtlas(desc)

        self.enabledAtlases[atlasID] = atlasImage

        self._locationChanged()

        
    def disableAtlasInfo(self, atlasID):

        self.enabledAtlases.pop(atlasID, None)
        self._locationChanged()

        
    def toggleSummaryOverlay(self, atlasID):

        overlayName = '{}/all'.format(atlasID)
        overlay     = self._imageList.find(overlayName)

        if overlay is not None:
            self._imageList.remove(overlay)
            log.debug('Removed summary overlay {}'.format(overlayName))
            
        else:
            overlay = self.enabledAtlases.get(atlasID, None)
            if overlay is None or \
               isinstance(overlay, atlases.ProbabilisticAtlas):
                overlay = atlases.loadAtlas(self.atlasDescs[atlasID], True)
                
            overlay.name = overlayName

            # Even though all the FSL atlases
            # are in MNI152 space, not all of
            # their sform_codes are correctly set
            overlay.nibImage.get_header().set_sform(
                None, code=constants.NIFTI_XFORM_MNI_152)
            
            self._imageList.append(overlay)
            log.debug('Added summary overlay {}'.format(overlayName))
            
            
    
    
    def toggleOverlay(self, atlasID, labelIndex, label):
        """
        """

        desc        = self.atlasDescs[atlasID]
        overlayName = '{}/{}'.format(atlasID, desc.labels[labelIndex].name)
        overlay     = self._imageList.find(overlayName)

        if overlay is not None:
            self._imageList.remove(overlay)
            log.debug('Removed overlay {}'.format(overlayName))

        else:
            atlas = self.enabledAtlases.get(atlasID, None)
            if atlas is None or \
               (label and isinstance(overlay, atlases.LabelAtlas)):
                atlas = atlases.loadAtlas(self.atlasDescs[atlasID], True)

            if label:
                if   desc.atlasType == 'probabilistic':
                    labelVal = labelIndex + 1
                elif desc.atlasType == 'label':
                    labelVal = labelIndex 
            
                mask = np.zeros(atlas.shape, dtype=np.uint8)
                mask[atlas.data == labelIndex] = labelVal
            else:
                mask = atlas.data[..., labelIndex]

            overlay = fslimage.Image(
                mask,
                header=atlas.nibImage.get_header(),
                name=overlayName)

            # See comment  in toggleSummaryOverlay
            overlay.nibImage.get_header().set_sform(
                None, code=constants.NIFTI_XFORM_MNI_152)

            if label:
                overlay.imageType = 'mask'

            self._imageList.append(overlay)
            log.debug('Added overlay {}'.format(overlayName))
            
            display = self._displayCtx.getDisplayProperties(overlay)

            if label:
                display.getDisplayOpts().colour = np.random.random(3)
            else:
                display.getDisplayOpts().cmap = 'hot'
 


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
