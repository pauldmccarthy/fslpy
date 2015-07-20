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

from fsl.fslview.views                     import CanvasPanel
from fsl.fslview.views                     import OrthoPanel
from fsl.fslview.views                     import LightBoxPanel

from fsl.fslview.controls                  import OrthoToolBar
from fsl.fslview.controls                  import LightBoxToolBar
from fsl.fslview.controls                  import OverlayDisplayToolBar

from fsl.fslview.displaycontext            import Display
from fsl.fslview.displaycontext            import VolumeOpts
from fsl.fslview.displaycontext            import MaskOpts
from fsl.fslview.displaycontext            import VectorOpts
from fsl.fslview.displaycontext            import RGBVectorOpts
from fsl.fslview.displaycontext            import LineVectorOpts
from fsl.fslview.displaycontext            import ModelOpts
from fsl.fslview.displaycontext            import LabelOpts

from fsl.fslview.displaycontext            import SceneOpts
from fsl.fslview.displaycontext            import OrthoOpts
from fsl.fslview.displaycontext            import LightBoxOpts


def widget(labelCls, name, *args, **kwargs):

    label = strings.properties.get((labelCls, name), name)
    return props.Widget(name, label=label, *args, **kwargs)


########################################
# OrthoPanel related panels and toolbars
########################################


OrthoToolBarLayout = [
    actions.ActionButton(OrthoPanel,   'screenshot'),
    widget(              OrthoOpts,    'zoom', spin=False, showLimits=False),
    widget(              OrthoOpts,    'layout'),
    widget(              OrthoOpts,    'showXCanvas'),
    widget(              OrthoOpts,    'showYCanvas'),
    widget(              OrthoOpts,    'showZCanvas'),
    actions.ActionButton(OrthoToolBar, 'more')]


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


CanvasPanelLayout = props.VGroup((
    widget(CanvasPanel,
           'profile',
           visibleWhen=lambda i: len(i.getProp('profile').getChoices(i)) > 1), 
    widget(CanvasPanel, 'syncOverlayOrder'),
    widget(CanvasPanel, 'syncLocation')))

SceneOptsLayout = props.VGroup((
    widget(SceneOpts, 'showCursor'),
    widget(SceneOpts, 'performance', spin=False, showLimits=False),
    widget(SceneOpts, 'showColourBar'),
    widget(SceneOpts, 'colourBarLabelSide'),
    widget(SceneOpts, 'colourBarLocation')))


OrthoPanelLayout = props.VGroup((
    widget(OrthoOpts, 'layout'), 
    widget(OrthoOpts, 'zoom', spin=False, showLimits=False),
    widget(OrthoOpts, 'showLabels'),
    props.HGroup((widget(OrthoOpts, 'showXCanvas'),
                  widget(OrthoOpts, 'showYCanvas'),
                  widget(OrthoOpts, 'showZCanvas')))))


#######################################
# LightBoxPanel control panels/toolbars
#######################################

LightBoxToolBarLayout = [
    actions.ActionButton(LightBoxPanel, 'screenshot'),
    widget(              LightBoxOpts, 'zax'),
    
    widget(LightBoxOpts, 'sliceSpacing', spin=False, showLimits=False),
    widget(LightBoxOpts, 'zrange',       spin=False, showLimits=False),
    widget(LightBoxOpts, 'zoom',         spin=False, showLimits=False),
    actions.ActionButton(LightBoxToolBar, 'more')]


LightBoxPanelLayout = props.VGroup((
    widget(LightBoxOpts, 'zax'),
    widget(LightBoxOpts, 'zoom'),
    widget(LightBoxOpts, 'sliceSpacing'),
    widget(LightBoxOpts, 'zrange'),
    widget(LightBoxOpts, 'highlightSlice'),
    widget(LightBoxOpts, 'showGridLines')))



##########################################
# Overlay display property panels/toolbars
##########################################


DisplayToolBarLayout = [
    widget(Display, 'name'),
    widget(Display, 'overlayType'),
    widget(Display, 'alpha',      spin=False, showLimits=False),
    widget(Display, 'brightness', spin=False, showLimits=False),
    widget(Display, 'contrast',   spin=False, showLimits=False)]


VolumeOptsToolBarLayout = [
    widget(VolumeOpts, 'cmap'),
    actions.ActionButton(OverlayDisplayToolBar, 'more')]


MaskOptsToolBarLayout = [
    widget(MaskOpts, 'colour'),
    actions.ActionButton(OverlayDisplayToolBar, 'more')]


VectorOptsToolBarLayout = [
    widget(VectorOpts, 'modulate'),
    widget(VectorOpts, 'modThreshold', showLimits=False, spin=False),
    actions.ActionButton(OverlayDisplayToolBar, 'more')]

ModelOptsToolBarLayout = [
    widget(ModelOpts, 'colour'),
    widget(ModelOpts, 'outline'),
    widget(ModelOpts, 'outlineWidth', showLimits=False, spin=False),
    actions.ActionButton(OverlayDisplayToolBar, 'more')]

LabelOptsToolBarLayout = [
    widget(LabelOpts, 'lut'),
    widget(LabelOpts, 'outline'),
    widget(LabelOpts, 'outlineWidth', showLimits=False, spin=False),
    actions.ActionButton(OverlayDisplayToolBar, 'more')]


DisplayLayout = [
    widget(Display, 'name'),
    widget(Display, 'overlayType'),
    widget(Display, 'enabled'),
    widget(Display, 'alpha',         showLimits=False, editLimits=False),
    widget(Display, 'brightness',    showLimits=False, editLimits=False),
    widget(Display, 'contrast',      showLimits=False, editLimits=False)]


VolumeOptsLayout = [
    widget(VolumeOpts, 'resolution',    showLimits=False),
    widget(VolumeOpts, 'transform'),
    widget(VolumeOpts, 'volume',        showLimits=False),
    widget(VolumeOpts, 'interpolation'),
    widget(VolumeOpts, 'cmap'),
    widget(VolumeOpts, 'invert'),
    widget(VolumeOpts, 'invertClipping'),
    widget(VolumeOpts, 'displayRange',  showLimits=False, slider=True),
    widget(VolumeOpts, 'clippingRange', showLimits=False, slider=True)]


MaskOptsLayout = [
    widget(MaskOpts, 'resolution', showLimits=False),
    widget(MaskOpts, 'transform'),
    widget(MaskOpts, 'volume',     showLimits=False),
    widget(MaskOpts, 'colour'),
    widget(MaskOpts, 'invert'),
    widget(MaskOpts, 'threshold',  showLimits=False)]


RGBVectorOptsLayout = [
    widget(RGBVectorOpts, 'resolution',    showLimits=False),
    widget(RGBVectorOpts, 'transform'),
    widget(RGBVectorOpts, 'interpolation'),
    widget(RGBVectorOpts, 'xColour'),
    widget(RGBVectorOpts, 'yColour'),
    widget(RGBVectorOpts, 'zColour'),
    widget(RGBVectorOpts, 'suppressX'),
    widget(RGBVectorOpts, 'suppressY'),
    widget(RGBVectorOpts, 'suppressZ'),
    widget(RGBVectorOpts, 'modulate'),
    widget(RGBVectorOpts, 'modThreshold', showLimits=False, spin=False)]

LineVectorOptsLayout = [
    widget(LineVectorOpts, 'resolution',    showLimits=False),
    widget(LineVectorOpts, 'transform'),
    widget(LineVectorOpts, 'xColour'),
    widget(LineVectorOpts, 'yColour'),
    widget(LineVectorOpts, 'zColour'),
    widget(LineVectorOpts, 'suppressX'),
    widget(LineVectorOpts, 'suppressY'),
    widget(LineVectorOpts, 'suppressZ'),
    widget(LineVectorOpts, 'directed'),
    widget(LineVectorOpts, 'lineWidth', showLimits=False),
    widget(LineVectorOpts, 'modulate'),
    widget(LineVectorOpts, 'modThreshold', showLimits=False, spin=False)]


ModelOptsLayout = [
    widget(ModelOpts, 'colour'),
    widget(ModelOpts, 'outline'),
    widget(ModelOpts, 'outlineWidth', showLimits=False),
    widget(ModelOpts, 'refImage'),
    # widget(ModelOpts, 'showName'),
    widget(ModelOpts, 'coordSpace',
           visibleWhen=lambda o: o.refImage != 'none')]


LabelOptsLayout = [
    widget(LabelOpts, 'lut'),
    widget(LabelOpts, 'outline'),
    widget(LabelOpts, 'outlineWidth', showLimits=False),
    # widget(LabelOpts, 'showNames'),
    widget(LabelOpts, 'resolution', showLimits=False),
    widget(LabelOpts, 'transform'),
    widget(LabelOpts, 'volume',     showLimits=False)]



layouts = td.TypeDict({

    'CanvasPanel'   : CanvasPanelLayout,
    'OrthoPanel'    : OrthoPanelLayout,
    'LightBoxPanel' : LightBoxPanelLayout,

    'SceneOpts' : SceneOptsLayout,

    ('OverlayDisplayToolBar', 'Display')        : DisplayToolBarLayout,
    ('OverlayDisplayToolBar', 'VolumeOpts')     : VolumeOptsToolBarLayout,
    ('OverlayDisplayToolBar', 'MaskOpts')       : MaskOptsToolBarLayout,
    ('OverlayDisplayToolBar', 'VectorOpts')     : VectorOptsToolBarLayout,
    ('OverlayDisplayToolBar', 'ModelOpts')      : ModelOptsToolBarLayout,
    ('OverlayDisplayToolBar', 'LabelOpts')      : LabelOptsToolBarLayout,

    ('OverlayDisplayPanel',   'Display')        : DisplayLayout,
    ('OverlayDisplayPanel',   'VolumeOpts')     : VolumeOptsLayout,
    ('OverlayDisplayPanel',   'MaskOpts')       : MaskOptsLayout,
    ('OverlayDisplayPanel',   'RGBVectorOpts')  : RGBVectorOptsLayout,
    ('OverlayDisplayPanel',   'LineVectorOpts') : LineVectorOptsLayout,
    ('OverlayDisplayPanel',   'ModelOpts')      : ModelOptsLayout,
    ('OverlayDisplayPanel',   'LabelOpts')      : LabelOptsLayout, 

    'OrthoToolBar'    : OrthoToolBarLayout,
    'LightBoxToolBar' : LightBoxToolBarLayout,

    ('OrthoProfileToolBar', 'view') : OrthoProfileToolBarViewLayout,
    ('OrthoProfileToolBar', 'edit') : OrthoProfileToolBarEditLayout,
})


locations = td.TypeDict({
    'LocationPanel'       : aui.AUI_DOCK_BOTTOM,
    'OverlayListPanel'    : aui.AUI_DOCK_BOTTOM,
    'AtlasPanel'          : aui.AUI_DOCK_BOTTOM,
    'ImageDisplayToolBar' : aui.AUI_DOCK_TOP,
    
})
