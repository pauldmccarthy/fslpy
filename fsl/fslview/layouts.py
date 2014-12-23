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

layouts = td.TypeDict({

    'OrthoViewProfile' : OrthoViewProfileLayout,
    'OrthoEditProfile' : OrthoEditProfileLayout
})
    
