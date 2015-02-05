#!/usr/bin/env python
#
# layouts.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import props

import fsl.utils.typedict  as td

import fsl.data.strings as strings

from fsl.fslview.profiles.orthoviewprofile   import OrthoViewProfile
from fsl.fslview.profiles.orthoeditprofile   import OrthoEditProfile
from fsl.fslview.views.canvaspanel           import CanvasPanel
from fsl.fslview.views.orthopanel            import OrthoPanel
from fsl.fslview.views.lightboxpanel         import LightBoxPanel
from fsl.fslview.displaycontext              import Display
from fsl.fslview.displaycontext.volumeopts   import VolumeOpts
from fsl.fslview.displaycontext.maskopts     import MaskOpts
from fsl.fslview.displaycontext.vectoropts   import VectorOpts


def widget(name, labelCls, *args, **kwargs):
    return props.Widget(name,
                        label=strings.properties[labelCls, name],
                        *args,
                        **kwargs)


def actionButton(name, labelCls, *args, **kwargs):
    def callback(i, *a):
        i.run(name)
    return props.Button(name,
                        text=strings.actions[labelCls, name],
                        callback=callback)


OrthoEditProfileLayout = props.HGroup(
    (widget('mode',
            OrthoEditProfile),
     widget('selectionMode',
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
    (actionButton('resetZoom',    OrthoViewProfile),
     actionButton('centreCursor', OrthoViewProfile)),
    wrap=True,
    showLabels=False)

OrthoEditProfileActionLayout = props.HGroup(
    (actionButton('resetZoom',               OrthoEditProfile),
     actionButton('centreCursor',            OrthoEditProfile),
     actionButton('clearSelection',          OrthoEditProfile),
     actionButton('fillSelection',           OrthoEditProfile),
     actionButton('createMaskFromSelection', OrthoEditProfile),
     actionButton('createROIFromSelection',  OrthoEditProfile),
     actionButton('undo',                    OrthoEditProfile),
     actionButton('redo',                    OrthoEditProfile)),
    wrap=True,
    showLabels=False)


CanvasPanelActionLayout = props.HGroup(
    (widget('profile',
            CanvasPanel,
            visibleWhen=lambda i: len(i.getProp('profile').getChoices(i)) > 1),
     actionButton('screenshot',               CanvasPanel),
     actionButton('toggleColourBar',          CanvasPanel),
     actionButton('toggleImageList',          CanvasPanel),
     actionButton('toggleDisplayProperties',  CanvasPanel),
     actionButton('toggleLocationPanel',      CanvasPanel),
     actionButton('toggleCanvasProperties',   CanvasPanel)),
    wrap=True,
    showLabels=False)

CanvasPanelLayout = props.VGroup((
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


DisplayLayout = props.VGroup((
    widget('name',          Display),
    widget('imageType',     Display),
    widget('enabled',       Display),
    widget('resolution',    Display),
    widget('transform',     Display),
    widget('interpolation', Display),
    widget('alpha',         Display),
    widget('brightness',    Display),
    widget('contrast',      Display)))


VolumeOptsLayout = props.VGroup((
    widget('cmap',          VolumeOpts),
    widget('clipLow',       VolumeOpts),
    widget('clipHigh',      VolumeOpts),
    widget('displayRange',  VolumeOpts)))


MaskOptsLayout = props.VGroup((
    widget('colour',    MaskOpts),
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

    ('CanvasPanel',      'actions') : CanvasPanelActionLayout,
    ('OrthoPanel',       'props')   : OrthoPanelLayout,
    ('LightBoxPanel',    'props')   : LightBoxPanelLayout,

    'Display'    : DisplayLayout,
    'VolumeOpts' : VolumeOptsLayout,
    'MaskOpts'   : MaskOptsLayout,
    'VectorOpts' : VectorOptsLayout, 
})
