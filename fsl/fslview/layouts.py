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
from fsl.fslview.displaycontext              import Display
from fsl.fslview.displaycontext.volumeopts   import VolumeOpts
from fsl.fslview.displaycontext.maskopts     import MaskOpts
from fsl.fslview.displaycontext.vectoropts   import VectorOpts


def widget(name, labelCls, *args, **kwargs):
    return props.Widget(name,
                        label=strings.properties[labelCls, name],
                        *args,
                        **kwargs)


OrthoEditProfileLayout = props.HGroup(
    (widget('mode',
            OrthoEditProfile),
     widget('selectionSize',
            OrthoEditProfile,
            visibleWhen=lambda p: p.mode in ['sel', 'desel']),
     widget('selectionIs3D',  OrthoEditProfile,
            visibleWhen=lambda p: p.mode in ['sel', 'desel']),
     widget('fillValue',
            OrthoEditProfile),
     widget('intensityThres',
            OrthoEditProfile,
            visibleWhen=lambda p: p.mode == 'selint'),
     widget('localFill',
            OrthoEditProfile,
            visibleWhen=lambda p: p.mode == 'selint'),
     widget('searchRadius',
            OrthoEditProfile,
            visibleWhen=lambda p: p.mode == 'selint'),
     widget('selectionCursorColour',  OrthoEditProfile),
     widget('selectionOverlayColour', OrthoEditProfile)),
    wrap=True,
    vertLabels=True,
)

OrthoViewProfileLayout = props.HGroup(
    (widget('mode', OrthoViewProfile), ),
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
    widget('profile',
           CanvasPanel,
           visibleWhen=lambda i: len(i.getProp('profile').getChoices(i)) > 1), 
    widget('syncImageOrder',     CanvasPanel),
    widget('syncLocation',       CanvasPanel),
    widget('syncVolume',         CanvasPanel),
    widget('colourBarLabelSide', CanvasPanel),
    widget('colourBarLocation',  CanvasPanel)))


OrthoPanelLayout = props.VGroup((
    widget('layout',     OrthoPanel), 
    widget('zoom',       OrthoPanel),
    props.HGroup((widget('showCursor', OrthoPanel),
                  widget('showLabels', OrthoPanel))),
    props.HGroup((widget('showXCanvas', OrthoPanel),
                  widget('showYCanvas', OrthoPanel),
                  widget('showZCanvas', OrthoPanel)))))

LightBoxPanelLayout = props.VGroup((
    widget('zax',            LightBoxPanel),
    widget('zoom',           LightBoxPanel),
    widget('sliceSpacing',   LightBoxPanel),
    widget('zrange',         LightBoxPanel),
    props.HGroup((widget('showCursor',     LightBoxPanel),
                  widget('highlightSlice', LightBoxPanel),
                  widget('showGridLines',  LightBoxPanel)))))


HistogramPanelLayout = props.VGroup((
    widget('dataRange', HistogramPanel),
    widget('autoHist',  HistogramPanel),
    widget('nbins',     HistogramPanel,
           enabledWhen=lambda hp: not hp.autoHist)))


DisplayLayout = props.VGroup(
    (widget('name',          Display),
     widget('imageType',     Display),
     widget('resolution',    Display),
     widget('transform',     Display),
     widget('interpolation', Display),
     widget('volume',        Display),
     widget('syncVolume',    Display),
     widget('enabled',       Display),
     widget('alpha',         Display),
     widget('brightness',    Display),
     widget('contrast',      Display)))


VolumeOptsLayout = props.VGroup(
    (widget('cmap',         VolumeOpts),
     widget('displayRange', VolumeOpts),
     widget('clipLow',      VolumeOpts),
     widget('clipHigh',     VolumeOpts)))


MaskOptsLayout = props.VGroup(
    (widget('colour',    MaskOpts),
     widget('invert',    MaskOpts),
     widget('threshold', MaskOpts)))


VectorOptsLayout = props.VGroup((
    widget('displayMode',   VectorOpts),
    props.HGroup((
        widget('xColour',   VectorOpts),
        widget('yColour',   VectorOpts),
        widget('zColour',   VectorOpts)),
        vertLabels=True),
    props.HGroup((
        widget('suppressX', VectorOpts),
        widget('suppressY', VectorOpts),
        widget('suppressZ', VectorOpts)),
        vertLabels=True),
    widget('modulate',      VectorOpts),
    widget('modThreshold',  VectorOpts)))


layouts = td.TypeDict({

    ('OrthoViewProfile', 'props')   : OrthoViewProfileLayout,
    ('OrthoEditProfile', 'props')   : OrthoEditProfileLayout,
    ('OrthoViewProfile', 'actions') : OrthoViewProfileActionLayout,
    ('OrthoEditProfile', 'actions') : OrthoEditProfileActionLayout,

    'CanvasPanel'      : CanvasPanelLayout,
    'OrthoPanel'       : OrthoPanelLayout,
    'LightBoxPanel'    : LightBoxPanelLayout,
    'HistogramPanel'   : HistogramPanelLayout,

    'Display'    : DisplayLayout,
    'VolumeOpts' : VolumeOptsLayout,
    'MaskOpts'   : MaskOptsLayout,
    'VectorOpts' : VectorOptsLayout, 
})


minSizes = td.TypeDict({
    'AtlasInfoPanel'      : (300, 100),
    'AtlasOverlayPanel'   : (300, 100),
    'AtlasPanel'          : (300, 100),
    'ImageListPanel'      : (150, -1),
    'ImageDisplayPanel'   : (200,  200),
    'OrthoSettingsPanel'  : (200,  200), 
    'LocationPanel'       : (-1, -1),
})
