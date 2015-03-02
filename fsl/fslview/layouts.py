#!/usr/bin/env python
#
# layouts.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import wx

import props

import fsl.utils.typedict  as td

import fsl.data.strings    as strings
import fsl.fslview.actions as actions

from fsl.fslview.profiles.orthoviewprofile   import OrthoViewProfile
from fsl.fslview.profiles.orthoeditprofile   import OrthoEditProfile
from fsl.fslview.views.canvaspanel           import CanvasPanel
from fsl.fslview.views.orthopanel            import OrthoPanel
from fsl.fslview.views.lightboxpanel         import LightBoxPanel
from fsl.fslview.views.histogrampanel        import HistogramPanel
from fsl.fslview.controls.orthotoolbar       import OrthoToolBar
from fsl.fslview.displaycontext              import Display
from fsl.fslview.displaycontext.volumeopts   import VolumeOpts
from fsl.fslview.displaycontext.maskopts     import MaskOpts
from fsl.fslview.displaycontext.vectoropts   import VectorOpts


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
    actions.ActionButton(OrthoPanel,   'toggleColourBar'),
    widget(              OrthoPanel,   'zoom', spin=False, showLimits=False),
    widget(              OrthoPanel,   'layout'),
    widget(              OrthoPanel,   'showXCanvas'),
    widget(              OrthoPanel,   'showYCanvas'),
    widget(              OrthoPanel,   'showZCanvas'),
    actions.ActionButton(OrthoToolBar, 'more')]


OrthoEditProfileLayout = props.HGroup(
    (widget(OrthoEditProfile, 'mode'),
     widget(OrthoEditProfile,
            'selectionSize',
            visibleWhen=lambda p: p.mode in ['sel', 'desel']),
     widget(OrthoEditProfile,
            'selectionIs3D',  
            visibleWhen=lambda p: p.mode in ['sel', 'desel']),
     widget(OrthoEditProfile,
            'fillValue'),
     widget(OrthoEditProfile,
            'intensityThres',
            visibleWhen=lambda p: p.mode == 'selint'),
     widget(OrthoEditProfile,
            'localFill',
            visibleWhen=lambda p: p.mode == 'selint'),
     widget(OrthoEditProfile,
            'searchRadius',
            visibleWhen=lambda p: p.mode == 'selint'),
     widget(OrthoEditProfile, 'selectionCursorColour'),
     widget(OrthoEditProfile, 'selectionOverlayColour')),
    wrap=True,
    vertLabels=True,
)

OrthoViewProfileLayout = props.HGroup(
    (widget(OrthoViewProfile, 'mode'), ),
    wrap=True,
    vertLabels=True)

OrthoViewProfileActionLayout = props.HGroup(
    (actions.ActionButton(OrthoViewProfile, 'resetZoom'),
     actions.ActionButton(OrthoViewProfile, 'centreCursor')),
    wrap=True,
    showLabels=False)

OrthoEditProfileActionLayout = props.HGroup(
    (actions.ActionButton(OrthoEditProfile, 'resetZoom'),
     actions.ActionButton(OrthoEditProfile, 'centreCursor'),
     actions.ActionButton(OrthoEditProfile, 'clearSelection'),
     actions.ActionButton(OrthoEditProfile, 'fillSelection'),
     actions.ActionButton(OrthoEditProfile, 'createMaskFromSelection'),
     actions.ActionButton(OrthoEditProfile, 'createROIFromSelection'),
     actions.ActionButton(OrthoEditProfile, 'undo'),
     actions.ActionButton(OrthoEditProfile, 'redo')),
    wrap=True,
    showLabels=False)


CanvasPanelLayout = props.VGroup((
    widget(CanvasPanel,
           'profile',
           visibleWhen=lambda i: len(i.getProp('profile').getChoices(i)) > 1), 
    widget(CanvasPanel, 'syncImageOrder'),
    widget(CanvasPanel, 'syncLocation'),
    widget(CanvasPanel, 'syncVolume'),
    widget(CanvasPanel, 'colourBarLabelSide'),
    widget(CanvasPanel, 'colourBarLocation')))


OrthoPanelLayout = props.VGroup((
    widget(OrthoPanel, 'layout'), 
    widget(OrthoPanel, 'zoom'),
    props.HGroup((widget(OrthoPanel, 'showCursor'),
                  widget(OrthoPanel, 'showLabels'))),
    props.HGroup((widget(OrthoPanel, 'showXCanvas'),
                  widget(OrthoPanel, 'showYCanvas'),
                  widget(OrthoPanel, 'showZCanvas')))))

LightBoxPanelLayout = props.VGroup((
    widget(LightBoxPanel, 'zax'),
    widget(LightBoxPanel, 'zoom'),
    widget(LightBoxPanel, 'sliceSpacing'),
    widget(LightBoxPanel, 'zrange'),
    props.HGroup((widget(LightBoxPanel, 'showCursor'),
                  widget(LightBoxPanel, 'highlightSlice'),
                  widget(LightBoxPanel, 'showGridLines')))))



DisplayLayout = props.VGroup(
    (widget(Display, 'name'),
     widget(Display, 'imageType'),
     widget(Display, 'resolution',    editLimits=False),
     widget(Display, 'transform'),
     widget(Display, 'interpolation'),
     widget(Display, 'volume',        editLimits=False),
     widget(Display, 'syncVolume'),
     widget(Display, 'enabled'),
     widget(Display, 'alpha',         showLimits=False, editLimits=False),
     widget(Display, 'brightness',    showLimits=False, editLimits=False),
     widget(Display, 'contrast',      showLimits=False, editLimits=False)))


VolumeOptsLayout = props.VGroup(
    (widget(VolumeOpts, 'cmap'),
     widget(VolumeOpts, 'displayRange'),
     widget(VolumeOpts, 'clipLow'),
     widget(VolumeOpts, 'clipHigh')))


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

    ('OrthoViewProfile', 'props')   : OrthoViewProfileLayout,
    ('OrthoEditProfile', 'props')   : OrthoEditProfileLayout,
    ('OrthoViewProfile', 'actions') : OrthoViewProfileActionLayout,
    ('OrthoEditProfile', 'actions') : OrthoEditProfileActionLayout,

    'CanvasPanel'   : CanvasPanelLayout,
    'OrthoPanel'    : OrthoPanelLayout,
    'LightBoxPanel' : LightBoxPanelLayout,

    'Display'    : DisplayLayout,
    'VolumeOpts' : VolumeOptsLayout,
    'MaskOpts'   : MaskOptsLayout,
    'VectorOpts' : VectorOptsLayout,

    'OrthoToolBar' : OrthoToolBarLayout,


    ('OrthoProfileToolBar', 'view') : OrthoProfileToolBarViewLayout,
    ('OrthoProfileToolBar', 'edit') : OrthoProfileToolBarEditLayout,
    
    'HistogramToolBar' : HistogramToolBarLayout,
})


minSizes = td.TypeDict({
    'AtlasInfoPanel'        : (300, 100),
    'AtlasOverlayPanel'     : (300, 100),
    'AtlasPanel'            : (300, 100),
    'ImageListPanel'        : (150, -1),
    'ImageDisplayPanel'     : (200,  200),
    'OrthoSettingsPanel'    : (200,  200),
    'LightBoxSettingsPanel' : (200,  200),
    'LocationPanel'         : (-1, -1),
})
