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

    clippingRange = props.Bounds(
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

        self.clippingRange.xmin = self.dataMin - dMinDistance
        self.clippingRange.xmax = self.dataMax + dMinDistance
        
        # By default, the lowest values
        # in the image are clipped
        self.clippingRange.xlo  = self.dataMin + dMinDistance
        self.clippingRange.xhi  = self.dataMax + dMinDistance 

        self.setConstraint('clippingRange', 'minDistance', dMinDistance)

        fsldisplay.DisplayOpts.__init__(self,
                                        image,
                                        display,
                                        imageList,
                                        displayCtx,
                                        parent)
