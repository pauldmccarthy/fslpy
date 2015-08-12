#!/usr/bin/env python
#
# orthoprofiletoolbar.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import wx

import props

import fsl.fslview.toolbar as fsltoolbar
import fsl.fslview.actions as actions
import fsl.fslview.icons   as icons
import fsl.data.strings    as strings

from fsl.fslview.profiles.orthoeditprofile import OrthoEditProfile


log = logging.getLogger(__name__)

# Some of the toolbar widgets are labelled 
_LABELS = {

    'selectionCursorColour'  : strings.properties[OrthoEditProfile,
                                                  'selectionCursorColour'],
    'selectionOverlayColour' : strings.properties[OrthoEditProfile,
                                                  'selectionOverlayColour'],
    'selectionSize'          : strings.properties[OrthoEditProfile,
                                                  'selectionSize'],
    'intensityThres'         : strings.properties[OrthoEditProfile,
                                                  'intensityThres'],
    'searchRadius'           : strings.properties[OrthoEditProfile,
                                                  'searchRadius'],
    'fillValue'              : strings.properties[OrthoEditProfile,
                                                  'fillValue'], 
}

_ICONS = {
    'view'                    : icons.findImageFile('eye24'),
    'edit'                    : icons.findImageFile('pencil24'),
    'selectionIs3D'           : [icons.findImageFile('selection3D24'),
                                 icons.findImageFile('selection2D24')],
    'clearSelection'          : icons.findImageFile('clear24'),
    'undo'                    : icons.findImageFile('undo24'),
    'redo'                    : icons.findImageFile('redo24'),
    'fillSelection'           : icons.findImageFile('fill24'),
    'createMaskFromSelection' : icons.findImageFile('createMask24'),
    'createROIFromSelection'  : icons.findImageFile('createROI24'),
    'limitToRadius'           : icons.findImageFile('radius24'),
    'localFill'               : icons.findImageFile('localsearch24'),
    'selint'                  : icons.findImageFile('selectByIntensity24'),
}

_TOOLBAR_SPECS  = {

    'profile' : props.Widget(
        'profile',
        icons={
            'view' : _ICONS['view'],
            'edit' : _ICONS['edit']}),

    'view' : {},

    'edit' : [
        props.Widget('selectionIs3D',
                     enabledWhen=lambda p: p.mode in ['sel', 'desel'],
                     icon=_ICONS['selectionIs3D'],
                     toggle=True),
        actions.ActionButton('clearSelection', icon=_ICONS['clearSelection']),
        actions.ActionButton('undo',           icon=_ICONS['undo']),
        actions.ActionButton('redo',           icon=_ICONS['redo']),
        actions.ActionButton('fillSelection',  icon=_ICONS['fillSelection']),
        actions.ActionButton('createMaskFromSelection',
                             icon=_ICONS['createMaskFromSelection']),
        actions.ActionButton('createROIFromSelection',
                             icon=_ICONS['createROIFromSelection']),

        props.Widget('selint', icon=_ICONS['selint']),
        props.Widget('limitToRadius',
                     icon=_ICONS['limitToRadius'],
                     enabledWhen=lambda p: p.mode == 'selint'),
        
        props.Widget('localFill',
                     icon=_ICONS['localFill'],
                     enabledWhen=lambda p: p.mode == 'selint'),
        
        props.Widget('selectionCursorColour',
                     label=_LABELS['selectionCursorColour']),
        props.Widget('selectionOverlayColour',
                     label=_LABELS['selectionOverlayColour']), 
        props.Widget('selectionSize',
                     enabledWhen=lambda p: p.mode in ['sel', 'desel'],
                     label=_LABELS['selectionSize']),
        
        props.Widget('fillValue', label=_LABELS['fillValue']),

        props.Widget('intensityThres',
                     label=_LABELS['intensityThres'],
                     enabledWhen=lambda p: p.mode == 'selint'),

        props.Widget('searchRadius',
                     label=_LABELS['searchRadius'],
                     enabledWhen=lambda p: p.mode == 'selint' and 
                                           p.limitToRadius)
    ]
}



class OrthoProfileToolBar(fsltoolbar.FSLViewToolBar):

    selint = props.Boolean(default=False)

    radius = props.Boolean(default=False)

    def __init__(self, parent, overlayList, displayCtx, ortho):
        fsltoolbar.FSLViewToolBar.__init__(self,
                                           parent,
                                           overlayList,
                                           displayCtx,
                                           24)

        self.orthoPanel = ortho

        self .addListener('selint',  self._name, self.__selintChanged)
        ortho.addListener('profile', self._name, self.__profileChanged)
        
        self.__profileChanged()


    def destroy(self):
        self.orthoPanel.removeListener('profile', self._name)
        fsltoolbar.FSLViewToolBar.destroy(self)


    def __selintChanged(self, *a):

        ortho = self.orthoPanel

        if ortho.profile != 'edit':
            return
        
        profile = ortho.getCurrentProfile()
        
        if self.selint: profile.mode = 'selint'
        else:           profile.mode = 'sel'


    def __profileChanged(self, *a):

        oldTools = self.GetTools()

        # See comment at bottom
        def destroyOldTools():
            for t in oldTools:
                t.Destroy()

        for t in oldTools:
            t.Show(False)

        self.ClearTools(destroy=False, postevent=False)
                
        ortho      = self.orthoPanel
        profile    = ortho.profile
        profileObj = ortho.getCurrentProfile()

        if profile == 'edit':
            self.disableNotification('selint')
            self.selint = profileObj.mode == 'selint'
            self.enableNotification('selint')

        specs = _TOOLBAR_SPECS[profile]

        tools = []

        for spec in specs:

            if spec.key == 'selint': target = self
            else:                    target = profileObj
            
            widget = props.buildGUI(self, target, spec)
            if spec.label is not None:
                widget = self.MakeLabelledTool(widget, spec.label)
                
            tools.append(widget)

        profileTool = props.buildGUI(self, ortho, _TOOLBAR_SPECS['profile'])

        tools.insert(0, profileTool)

        self.SetTools(tools)
        
        # Destroy old tools asynchronously, as
        # this method may have been called due
        # to an action on one of said old tools.
        wx.CallLater(1000, destroyOldTools) 
