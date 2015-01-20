#!/usr/bin/env python
#
# maskdisplay.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import numpy as np


import props

class MaskOpts(props.SyncableHasProperties):

    colour    = props.Colour()
    invert    = props.Boolean(default=False)
    threshold = props.Real(minval=0, maxval=1, default=1, editLimits=True)

    def __init__(self, image, parent=None):
        props.SyncableHasProperties.__init__(self, parent)

        if np.prod(image.shape) > 2 ** 30:
            sample = image.data[..., image.shape[-1] / 2]
            minval = float(sample.min())
            maxval = float(sample.max())
        else:
            minval = float(image.data.min())
            maxval = float(image.data.max())

        self.setConstraint('threshold', 'minval', minval)
        self.setConstraint('threshold', 'maxval', maxval)
