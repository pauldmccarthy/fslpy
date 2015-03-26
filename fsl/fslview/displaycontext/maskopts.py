#!/usr/bin/env python
#
# maskdisplay.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import numpy as np


import props

import fsl.data.strings as strings
import display          as fsldisplay

class MaskOpts(fsldisplay.DisplayOpts):

    colour     = props.Colour()
    invert     = props.Boolean(default=False)
    threshold  = props.Bounds(
        ndims=1,
        labels=[strings.choices['VolumeOpts.displayRange.min'],
                strings.choices['VolumeOpts.displayRange.max']]) 

    def __init__(self, image, display, imageList, displayCtx, parent=None):

        if np.prod(image.shape) > 2 ** 30:
            sample = image.data[..., image.shape[-1] / 2]
            self.dataMin = float(sample.min())
            self.dataMax = float(sample.max())
        else:
            self.dataMin = float(image.data.min())
            self.dataMax = float(image.data.max())

        dRangeLen    = abs(self.dataMax - self.dataMin)
        dMinDistance = dRangeLen / 10000.0

        # This is a hack. Mask images are rendered
        # using GLMask, which inherits from GLVolume.
        # The latter assumes that a 'clippingRange'
        # attribute is present on Opts instances
        # (see GLVolume.clippingRange). So we're
        # adding a dummy attribute to make the
        # GLVolume rendering code happy.
        self.clippingRange = (self.dataMin - 1, self.dataMax + 1)

        self.threshold.xmin = self.dataMin - dMinDistance
        self.threshold.xmax = self.dataMax + dMinDistance
        self.threshold.xlo  = self.dataMin + dMinDistance
        self.threshold.xhi  = self.dataMax + dMinDistance 
        self.setConstraint('threshold', 'minDistance', dMinDistance)

        fsldisplay.DisplayOpts.__init__(self,
                                        image,
                                        display,
                                        imageList,
                                        displayCtx,
                                        parent)
