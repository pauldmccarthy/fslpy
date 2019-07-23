#!/usr/bin/env python
#
# test_image_roi.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import pytest

import numpy as np

import fsl.data.image as fslimage
import fsl.utils.image.roi as roi


def test_roi():

    # inshape, bounds, expected outshape, expected affine offset
    tests = [
        # 3D image, 3D roi
        ([10, 10, 10],     [(0, 10), (0, 10), (0, 10)], [10, 10, 10],     [0, 0, 0]),
        ([10, 10, 10],     [(1, 10), (1, 10), (1, 10)], [ 9,  9,  9],     [1, 1, 1]),
        ([10, 10, 10],     [(1,  9), (1,  9), (1,  9)], [ 8,  8,  8],     [1, 1, 1]),
        ([10, 10, 10],     [(3,  5), (3,  5), (3,  5)], [ 2,  2,  2],     [3, 3, 3]),
        ([10, 10, 10],     [(4,  5), (4,  5), (4,  5)], [ 1,  1,  1],     [4, 4, 4]),

        # 4D image, 3D roi
        ([10, 10, 10, 10], [(0, 10), (0, 10), (0, 10)], [10, 10, 10, 10], [0, 0, 0]),
        ([10, 10, 10, 10], [(1, 10), (1, 10), (1, 10)], [ 9,  9,  9, 10], [1, 1, 1]),
        ([10, 10, 10, 10], [(1,  9), (1,  9), (1,  9)], [ 8,  8,  8, 10], [1, 1, 1]),
        ([10, 10, 10, 10], [(3,  5), (3,  5), (3,  5)], [ 2,  2,  2, 10], [3, 3, 3]),
        ([10, 10, 10, 10], [(4,  5), (4,  5), (4,  5)], [ 1,  1,  1, 10], [4, 4, 4]),

        # 4D image, 4D roi
        ([10, 10, 10, 10], [(0, 10), (0, 10), (0, 10), (0, 10)], [10, 10, 10, 10], [0, 0, 0]),
        ([10, 10, 10, 10], [(1, 10), (1, 10), (1, 10), (1, 10)], [ 9,  9,  9,  9], [1, 1, 1]),
        ([10, 10, 10, 10], [(1,  9), (1,  9), (1,  9), (1,  9)], [ 8,  8,  8,  8], [1, 1, 1]),
        ([10, 10, 10, 10], [(3,  5), (3,  5), (3,  5), (3,  5)], [ 2,  2,  2,  2], [3, 3, 3]),
        ([10, 10, 10, 10], [(4,  5), (4,  5), (4,  5), (4,  5)], [ 1,  1,  1],     [4, 4, 4]),

        # expanding FOV
        ([10, 10, 10], [(-5, 15), ( 0, 10), ( 0, 10)], [20, 10, 10], [-5,  0,  0]),
        ([10, 10, 10], [(-5, 15), (-5, 15), ( 0, 10)], [20, 20, 10], [-5, -5,  0]),
        ([10, 10, 10], [(-5, 15), (-5, 10), (-5, 15)], [20, 15, 20], [-5, -5, -5]),
        ([10, 10, 10], [(-5, 15), ( 3, 7),  ( 0, 10)], [20,  4, 10], [-5,  3,  0]),
    ]

    for inshape, bounds, outshape, offset in tests:
        data  = np.random.randint(1, 10, inshape)
        image = fslimage.Image(data, xform=np.eye(4))

        result = roi.roi(image, bounds)

        expaff        = np.eye(4)
        expaff[:3, 3] = offset

        assert np.all(list(result.shape) == list(outshape))
        assert np.all(np.isclose(result.voxToWorldMat, expaff))

        oldslc = []
        newslc = []

        for (lo, hi), oldlen in zip(bounds, inshape):
            oldslc.append(slice(max(lo, 0), min(hi, oldlen)))

        if len(oldslc) < len(inshape):
            for d in inshape[len(oldslc):]:
                oldslc.append(slice(0, d))

        for (lo, hi), slc in zip(bounds, oldslc):
            if lo < 0:    newlo = -lo
            else:         newlo =  0

            oldlen = slc.stop - slc.start

            newslc.append(slice(newlo, newlo + oldlen))

        if len(newslc) > len(outshape):
            newslc = newslc[:len(outshape)]

        assert np.all(data[tuple(oldslc)] == result.data[tuple(newslc)])

    # Error on:
    #  - not enough bounds
    #  - too many bounds
    #  - hi >= lo
    data  = np.random.randint(1, 10, (10, 10, 10))
    image = fslimage.Image(data, xform=np.eye(4))
    with pytest.raises(ValueError): roi.roi(image, [(0, 10), (0, 10)])
    with pytest.raises(ValueError): roi.roi(image, [(0, 10), (0, 10), (0, 10), (0, 10)])
    with pytest.raises(ValueError): roi.roi(image, [(5, 5),  (0, 10), (0, 10)])
    with pytest.raises(ValueError): roi.roi(image, [(6, 5),  (0, 10), (0, 10)])
    with pytest.raises(ValueError): roi.roi(image, [(0, 10), (5,  5), (0, 10)])
    with pytest.raises(ValueError): roi.roi(image, [(0, 10), (6,  5), (0, 10)])
    with pytest.raises(ValueError): roi.roi(image, [(0, 10), (0, 10), (5,  5)])
    with pytest.raises(ValueError): roi.roi(image, [(0, 10), (0, 10), (6,  5)])
