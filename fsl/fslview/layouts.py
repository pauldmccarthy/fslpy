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

import fsl.fslview.strings as strings

from fsl.fslview.profiles.orthoviewprofile import OrthoViewProfile
from fsl.fslview.profiles.orthoeditprofile import OrthoEditProfile
from fsl.fslview.views.canvaspanel         import CanvasPanel


OrthoEditProfileLayout = props.HGroup(
    (props.Widget('mode',           label=strings.labels[OrthoEditProfile, 'mode']),
     props.Widget('selectionMode',  label=strings.labels[OrthoEditProfile, 'selectionMode']),
     props.Widget('selectionSize',  label=strings.labels[OrthoEditProfile, 'selectionSize'],  visibleWhen=lambda p: p.mode in ['sel', 'desel', 'selint']),
     props.Widget('selectionIs3D',  label=strings.labels[OrthoEditProfile, 'selectionIs3D'],  visibleWhen=lambda p: p.mode in ['sel', 'desel', 'selint']),
     props.Widget('fillValue',      label=strings.labels[OrthoEditProfile, 'fillValue']),
     props.Widget('intensityThres', label=strings.labels[OrthoEditProfile, 'intensityThres'], visibleWhen=lambda p: p.mode == 'selint'),
     props.Widget('localFill',      label=strings.labels[OrthoEditProfile, 'localFill'],      visibleWhen=lambda p: p.mode == 'selint'),
     props.Widget('searchRadius',   label=strings.labels[OrthoEditProfile, 'searchRadius'],   visibleWhen=lambda p: p.mode == 'selint')),
    wrap=True,
    vertLabels=True,
)

OrthoViewProfileLayout = props.HGroup(('mode', ))



CanvasPanelActionLayout = props.HGroup(
    (props.Button('screenshot',              text=strings.labels[CanvasPanel, 'screenshot'],              callback=CanvasPanel.screenshot),
     props.Button('toggleColourBar',         text=strings.labels[CanvasPanel, 'toggleColourBar'],         callback=CanvasPanel.toggleColourBar),
     props.Button('toggleImageList',         text=strings.labels[CanvasPanel, 'toggleImageList'],         callback=CanvasPanel.toggleImageList),
     props.Button('toggleDisplayProperties', text=strings.labels[CanvasPanel, 'toggleDisplayProperties'], callback=CanvasPanel.toggleDisplayProperties),
     props.Button('toggleLocationPanel',     text=strings.labels[CanvasPanel, 'toggleLocationPanel'],     callback=CanvasPanel.toggleLocationPanel),
     props.Button('toggleCanvasProperties',  text=strings.labels[CanvasPanel, 'toggleCanvasProperties'],  callback=CanvasPanel.toggleCanvasProperties)),
    wrap=True,
    showLabels=False)




layouts = td.TypeDict({

    'OrthoViewProfile'         : OrthoViewProfileLayout,
    'OrthoEditProfile'         : OrthoEditProfileLayout,

    ('CanvasPanel', 'actions') : CanvasPanelActionLayout,
#    ('CanvasPanel', 'props')   : CanvasPanelTopLayout,
})
