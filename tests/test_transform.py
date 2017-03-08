#!/usr/bin/env python
#
# test_transform.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import numpy as np
import numpy.linalg as npla

import fsl.utils.transform as transform

def test_scaleOffsetXform():

    scales  = [1, 2, 3]
    offsets = [4, 5, 6]

    expected       = np.eye(4)
    expected[0, 0] = scales[ 0]
    expected[1, 1] = scales[ 1]
    expected[2, 2] = scales[ 2]
    expected[0, 3] = offsets[0]
    expected[1, 3] = offsets[1]
    expected[2, 3] = offsets[2]

    generated = transform.scaleOffsetXform(scales, offsets) 

    assert np.all(np.isclose(expected, generated))


    scale  = 5
    offset = 3

    expected       = np.eye(4)
    expected[0, 0] = scale
    expected[1, 1] = 1
    expected[2, 2] = 1
    expected[2, 2] = 1
    expected[0, 3] = offset

    generated = transform.scaleOffsetXform(scale, offset)
    assert np.all(np.isclose(expected, generated))


def test_invert():

    pass
