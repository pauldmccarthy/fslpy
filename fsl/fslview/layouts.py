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

from fsl.fslview.profiles.orthoviewprofile    import OrthoViewProfile
from fsl.fslview.profiles.orthoeditprofile    import OrthoEditProfile

from fsl.fslview.views.canvaspanel            import CanvasPanel
from fsl.fslview.views.orthopanel             import OrthoPanel
from fsl.fslview.views.lightboxpanel          import LightBoxPanel
from fsl.fslview.views.histogrampanel         import HistogramPanel

from fsl.fslview.controls.orthotoolbar        import OrthoToolBar
from fsl.fslview.controls.lightboxtoolbar     import LightBoxToolBar
from fsl.fslview.controls.imagedisplaytoolbar import ImageDisplayToolBar

from fsl.fslview.displaycontext               import Display
from fsl.fslview.displaycontext.volumeopts    import VolumeOpts
from fsl.fslview.displaycontext.maskopts      import MaskOpts
from fsl.fslview.displaycontext.vectoropts    import VectorOpts

from fsl.fslview.displaycontext.sceneopts     import SceneOpts
from fsl.fslview.displaycontext.orthoopts     import OrthoOpts
from fsl.fslview.displaycontext.lightboxopts  import LightBoxOpts


def widget(labelCls, name, *args, **kwargs):
    return props.Widget(name,
                        label=strings.properties[labelCls, name],
                        *args,
                        **kwargs)


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
    widget(CanvasPanel, 'syncImageOrder'),
    widget(CanvasPanel, 'syncLocation')))

SceneOptsLayout = props.VGroup((
    widget(SceneOpts, 'showCursor'),
    widget(SceneOpts, 'twoStageRender'),
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



########################################
# Image display property panels/toolbars
########################################


DisplayToolBarLayout = [
    widget(Display, 'name'),
    widget(Display, 'imageType'),
    widget(Display, 'alpha',      spin=False, showLimits=False),
    widget(Display, 'brightness', spin=False, showLimits=False),
    widget(Display, 'contrast',   spin=False, showLimits=False)]


VolumeOptsToolBarLayout = [
    widget(VolumeOpts, 'cmap'),
    actions.ActionButton(ImageDisplayToolBar, 'more')]


MaskOptsToolBarLayout = [
    widget(MaskOpts, 'colour'),
    actions.ActionButton(ImageDisplayToolBar, 'more')]


VectorOptsToolBarLayout = [
    widget(VectorOpts, 'displayMode'),
    actions.ActionButton(ImageDisplayToolBar, 'more')] 


DisplayLayout = props.VGroup(
    (widget(Display, 'name'),
     widget(Display, 'imageType'),
     widget(Display, 'resolution',    editLimits=False),
     widget(Display, 'transform'),
     widget(Display, 'interpolation'),
     widget(Display, 'volume',        editLimits=False),
     widget(Display, 'enabled'),
     widget(Display, 'alpha',         showLimits=False, editLimits=False),
     widget(Display, 'brightness',    showLimits=False, editLimits=False),
     widget(Display, 'contrast',      showLimits=False, editLimits=False)))


VolumeOptsLayout = props.VGroup(
    (widget(VolumeOpts, 'cmap'),
     widget(VolumeOpts, 'invert'),
     widget(VolumeOpts, 'clippingRange', slider=True)))


MaskOptsLayout = props.VGroup(
    (widget(MaskOpts, 'colour'),
     widget(MaskOpts, 'invert'),
     widget(MaskOpts, 'threshold')))


VectorOptsLayout = props.VGroup((
    widget(VectorOpts, 'displayMode'),
    props.HGroup((
        widget(VectorOpts, 'xColour'),
        widget(VectorOpts, 'yColour'),
        widget(VectorOpts, 'zColour')),
        vertLabels=True),
    props.HGroup((
        widget(VectorOpts, 'suppressX'),
        widget(VectorOpts, 'suppressY'),
        widget(VectorOpts, 'suppressZ')),
        vertLabels=True),
    widget(VectorOpts, 'modulate'),
    widget(VectorOpts, 'modThreshold')))


##########################
# Histogram toolbar/panels
##########################


# TODO add type-specific options here, to hide spin panels/limit
# buttons for the numeric sliders, when the props module supports it
HistogramToolBarLayout = [
    actions.ActionButton(HistogramPanel, 'screenshot'),
    props.Widget('dataRange', showLimits=False),
    props.Widget('nbins',
                 enabledWhen=lambda p: not p.autoHist,
                 spin=False, showLimits=False),
    props.Widget('autoHist')]


layouts = td.TypeDict({

    'CanvasPanel'   : CanvasPanelLayout,
    'OrthoPanel'    : OrthoPanelLayout,
    'LightBoxPanel' : LightBoxPanelLayout,

    'SceneOpts' : SceneOptsLayout,

    ('ImageDisplayToolBar', 'Display')    : DisplayToolBarLayout,
    ('ImageDisplayToolBar', 'VolumeOpts') : VolumeOptsToolBarLayout,
    ('ImageDisplayToolBar', 'MaskOpts')   : MaskOptsToolBarLayout,
    ('ImageDisplayToolBar', 'VectorOpts') : VectorOptsToolBarLayout,

    ('ImageDisplayPanel',   'Display')    : DisplayLayout,
    ('ImageDisplayPanel',   'VolumeOpts') : VolumeOptsLayout,
    ('ImageDisplayPanel',   'MaskOpts')   : MaskOptsLayout,
    ('ImageDisplayPanel',   'VectorOpts') : VectorOptsLayout, 

    'OrthoToolBar'    : OrthoToolBarLayout,
    'LightBoxToolBar' : LightBoxToolBarLayout,

    ('OrthoProfileToolBar', 'view') : OrthoProfileToolBarViewLayout,
    ('OrthoProfileToolBar', 'edit') : OrthoProfileToolBarEditLayout,
    
    'HistogramToolBar' : HistogramToolBarLayout,
})


locations = td.TypeDict({
    'LocationPanel'       : aui.AUI_DOCK_BOTTOM,
    'ImageListPanel'      : aui.AUI_DOCK_BOTTOM,
    'AtlasPanel'          : aui.AUI_DOCK_BOTTOM,
    'ImageDisplayToolBar' : aui.AUI_DOCK_TOP,
    
})
