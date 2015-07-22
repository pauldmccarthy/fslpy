#!/usr/bin/env python
#
# layouts.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import wx.lib.agw.aui as aui

import props

import fsl.utils.typedict  as td

import fsl.data.strings    as strings
import fsl.fslview.actions as actions

from fsl.fslview.profiles.orthoviewprofile import OrthoViewProfile
from fsl.fslview.profiles.orthoeditprofile import OrthoEditProfile


def widget(labelCls, name, *args, **kwargs):

    label = strings.properties.get((labelCls, name), name)
    return props.Widget(name, label=label, *args, **kwargs)


########################################
# OrthoPanel related panels and toolbars
########################################



OrthoProfileToolBarViewLayout = [
    actions.ActionButton(OrthoViewProfile, 'resetZoom'),
    actions.ActionButton(OrthoViewProfile, 'centreCursor')]


# We cannot currently use the visibleWhen 
# feature, as toolbar labels won't be hidden.
OrthoProfileToolBarEditLayout = [
    props.Widget('mode'),
    actions.ActionButton(OrthoViewProfile, 'resetZoom'),
    actions.ActionButton(OrthoViewProfile, 'centreCursor'),
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


layouts = td.TypeDict({

    ('OrthoProfileToolBar', 'view') : OrthoProfileToolBarViewLayout,
    ('OrthoProfileToolBar', 'edit') : OrthoProfileToolBarEditLayout,
})


locations = td.TypeDict({
    'LocationPanel'       : aui.AUI_DOCK_BOTTOM,
    'OverlayListPanel'    : aui.AUI_DOCK_BOTTOM,
    'AtlasPanel'          : aui.AUI_DOCK_BOTTOM,
    'ImageDisplayToolBar' : aui.AUI_DOCK_TOP,
})
