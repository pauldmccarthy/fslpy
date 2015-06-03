#!/usr/bin/env python
#
# labelopts.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import props

import volumeopts

import fsl.fslview.colourmaps as fslcm


class LabelOpts(volumeopts.ImageOpts):

    
    lut          = props.Choice()
    outline      = props.Boolean(default=False)
    outlineWidth = props.Real(minval=0, maxval=1, default=0.25, clamped=True)
    showNames    = props.Boolean(default=False)


    def __init__(self, overlay, *args, **kwargs):

        luts  = fslcm.getLookupTables()
        names = [lut.lutName() for lut in luts]

        self.getProp('lut').setChoices(luts, names, self)
        
        # TODO create a copy of this LUT? If the user
        # modifies a LUT for a specific image, do we
        # want those modfications to be propagated to
        # other images which also use the same LUT?
        # Because that's what's happening currently.
        self.lut = luts[0]

        volumeopts.ImageOpts.__init__(self, overlay, *args, **kwargs)
