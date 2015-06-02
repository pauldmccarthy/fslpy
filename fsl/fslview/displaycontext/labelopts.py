#!/usr/bin/env python
#
# labelopts.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import props

import volumeopts

import fsl.fslview.lookuptables as lookuptables


class LabelOpts(volumeopts.ImageOpts):

    
    lut          = props.Choice()
    outline      = props.Boolean(default=False)
    outlineWidth = props.Real(minval=0, maxval=1, default=0.25, clamped=True)
    showNames    = props.Boolean(default=False)


    def __init__(self, overlay, *args, **kwargs):

        luts  = lookuptables.all_luts
        names = [lut.lutName() for lut in luts]

        self.getProp('lut').setChoices(luts, names, self)

        self.lut = luts[0]

        volumeopts.ImageOpts.__init__(self, overlay, *args, **kwargs)
