#!/usr/bin/env python
#
# __init__.py - Functions for working with linear and non-linear FSL
#               transformations.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains functions for working with linear and non-linear FSL
transformations.
"""


from .affine import (  # noqa
    invert,
    concat,
    veclength,
    normalise,
    scaleOffsetXform,
    compose,
    decompose,
    rotMatToAffine,
    rotMatToAxisAngles,
    axisAnglesToRotMat,
    axisBounds,
    transform,
    transformNormal,
    rmsdev)
from .flirt  import (  # noqa
    fromFlirt,
    toFlirt,
    flirtMatrixToSform,
    sformToFlirtMatrix)
