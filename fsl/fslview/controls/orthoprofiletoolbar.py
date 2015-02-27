#!/usr/bin/env python
#
# orthoprofiletoolbar.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import props

import fsl.fslview.panel                     as fslpanel
import fsl.fslview.actions                   as actions
import fsl.data.strings                      as strings

from fsl.fslview.profiles.orthoviewprofile import OrthoViewProfile
from fsl.fslview.profiles.orthoeditprofile import OrthoEditProfile


log = logging.getLogger(__name__)


VIEW_TOOLS = [
    actions.ActionButton(OrthoViewProfile, 'resetZoom'),
    actions.ActionButton(OrthoViewProfile, 'centreCursor')]


# We cannot currently use the visibleWhen 
# feature, as toolbar labels won't be hidden.
EDIT_TOOLS = [
    props.Widget('mode'),
    actions.ActionButton(OrthoEditProfile, 'undo'),
    actions.ActionButton(OrthoEditProfile, 'redo'),
    actions.ActionButton(OrthoEditProfile, 'fillSelection'),
    actions.ActionButton(OrthoEditProfile, 'clearSelection'),
    actions.ActionButton(OrthoEditProfile, 'createMaskFromSelection'),
    actions.ActionButton(OrthoEditProfile, 'createROIFromSelection'),
    props.Widget('selectionCursorColour'),
    props.Widget('selectionOverlayColour'),    
    props.Widget('selectionSize',
                 enabledWhen=lambda p: p.mode in ['sel', 'desel']),
    props.Widget('selectionIs3D',
                 enabledWhen=lambda p: p.mode in ['sel', 'desel']),
    props.Widget('fillValue'),
    props.Widget('intensityThres',
                 enabledWhen=lambda p: p.mode == 'selint'),
    props.Widget('localFill',
                 enabledWhen=lambda p: p.mode == 'selint'),
    props.Widget('searchRadius',
                 enabledWhen=lambda p: p.mode == 'selint')]


class OrthoProfileToolBar(fslpanel.FSLViewToolBar):

    def __init__(self, parent, imageList, displayCtx, ortho):
        fslpanel.FSLViewToolBar.__init__(self, parent, imageList, displayCtx)

        self.orthoPanel = ortho

        ortho.addListener('profile', self._name, self._profileChanged)

        self.profileTool = props.makeWidget(self, ortho, 'profile')
        self.AddTool(self.profileTool, strings.properties[ortho, 'profile'])

        self._profileChanged()


    def destroy(self):
        fslpanel.FSLViewToolBar.destroy(self)
        self.orthoPanel.removeListener('profile', self._name)


    def _profileChanged(self, *a):

        profile = self.orthoPanel.profile

        if   profile == 'view':
            tools, labels = self._makeProfileTools(VIEW_TOOLS)
        elif profile == 'edit':
            tools, labels = self._makeProfileTools(EDIT_TOOLS)

        tools  = tools
        labels = labels

        self.ClearTools(destroy=True, startIdx=1)
        self.InsertTools(tools, labels, 1)

        
    def _makeProfileTools(self, toolSpecs):
            
        profile = self.orthoPanel.getCurrentProfile()

        tools  = []
        labels = []

        for toolSpec in toolSpecs:

            tool = props.buildGUI(self, profile, toolSpec)
            tools .append(tool)

            if isinstance(toolSpec, actions.ActionButton):
                labels.append(None)
            else:
                tool.SetLabel(strings.properties[profile, toolSpec.key])
                labels.append(strings.properties[profile, toolSpec.key])

        return tools, labels
