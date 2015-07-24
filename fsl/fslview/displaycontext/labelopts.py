#!/usr/bin/env python
#
# labelopts.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import props

import volumeopts

import fsl.fslview.colourmaps as fslcm


luts  = fslcm.getLookupTables()
names = [l.name for l in luts]

class LabelOpts(volumeopts.ImageOpts):

    lut          = props.Choice(luts, names)
    outline      = props.Boolean(default=False)
    outlineWidth = props.Real(minval=0, maxval=1, default=0.25, clamped=True)
    showNames    = props.Boolean(default=False)


    def __init__(self, overlay, *args, **kwargs):
        volumeopts.ImageOpts.__init__(self, overlay, *args, **kwargs)
