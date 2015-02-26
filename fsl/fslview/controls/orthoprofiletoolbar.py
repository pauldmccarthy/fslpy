#!/usr/bin/env python
#
# orthoprofiletoolbar.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import wx

import props

import fsl.fslview.panel as fslpanel
import fsl.data.strings  as strings


log = logging.getLogger(__name__)


class OrthoProfileToolBar(fslpanel.FSLViewToolBar):

    def __init__(self, parent, imageList, displayCtx, ortho):
        fslpanel.FSLViewToolBar.__init__(self, parent, imageList, displayCtx)

        self.orthoPanel = ortho

        ortho.addListener('profile', self._name, self._profileChanged)

        self._profile = None
        self._profileChanged()


    def destroy(self):
        fslpanel.FSLViewToolBar.destroy(self)
        self.orthoPanel.removeListener('profile', self._name)


    def _profileChanged(self, *a):

        profile = self.orthoPanel.profile

        if   profile == 'view': tools, labels = self._makeViewProfileTools()
        elif profile == 'edit': tools, labels = self._makeEditProfileTools()

        self.SetTools(tools, labels, destroy=True)

            
    def _makeViewProfileTools(self):
        
        profile = self.orthoPanel.getCurrentProfile()

        actions = ['resetZoom', 'centreCursor']

        tools  = []
        labels = []

        for action in actions:
            
            tool = wx.Button(self, label=strings.actions[profile, action])
            profile.getAction(action).bindToWidget(self, wx.EVT_BUTTON, tool)
            
            tools .append(tool)
            labels.append(None)

        return tools, labels

    
    def _makeEditProfileTools(self):
        profile = self.orthoPanel.getCurrentProfile()

        actions = ['undo',
                   'redo',
                   'fillSelection',
                   'clearSelection',
                   'createMaskFromSelection',
                   'createROIFromSelection']

        props = []

        tools  = []
        labels = []        
        for action in actions:
            
            tool = wx.Button(self, label=strings.actions[profile, action])
            profile.getAction(action).bindToWidget(self, wx.EVT_BUTTON, tool)
            
            tools .append(tool)
            labels.append(None)

        return tools, labels
