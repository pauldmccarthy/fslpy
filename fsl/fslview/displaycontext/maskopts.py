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
        fsldisplay.DisplayOpts.__init__(self,
                                        image,
                                        display,
                                        imageList,
                                        displayCtx,
                                        parent)

        if np.prod(image.shape) > 2 ** 30:
            sample = image.data[..., image.shape[-1] / 2]
            self.dataMin = float(sample.min())
            self.dataMax = float(sample.max())
        else:
            self.dataMin = float(image.data.min())
            self.dataMax = float(image.data.max())

        dRangeLen    = abs(self.dataMax - self.dataMin)
        dMinDistance = dRangeLen / 10000.0

        self.threshold.setMin(  0, self.dataMin - 0.5 * dRangeLen)
        self.threshold.setMax(  0, self.dataMax + 0.5 * dRangeLen)
        self.threshold.setRange(0, 0.1, self.dataMax + 0.1)
        self.setConstraint('threshold', 'minDistance', dMinDistance)        
