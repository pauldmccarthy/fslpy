#!/usr/bin/env python
#
# roi.py - Extract an ROI of an image.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :func:`roi` function, which can be used to extract
a region-of-interest from, or expand the field-of-view of, an :class:`.Image`.
"""


import numpy as np

import fsl.data.image       as fslimage
import fsl.transform.affine as affine


def _normaliseBounds(shape, bounds):
    """Adjust the given ``bounds`` so that it is compatible with the given
    ``shape``.

    Bounds must be specified for at least three dimensions - if the shape
    has more than three dimensions, additional bounds are added.

    A :exc:`ValueError` is raised if the provided bounds are invalid.

    :arg bounds: Sequence of ``(lo, hi)`` bounds - see :func:`roi`.
    :returns:    An adjusted sequence of bounds.
    """

    bounds = list(bounds)

    if len(bounds) < 3:
        raise ValueError('')

    if len(bounds) > len(shape):
        raise ValueError('')

    for b in bounds:
        if len(b) != 2 or b[0] >= b[1]:
            raise ValueError('')

    if len(bounds) < len(shape):
        for s in shape[len(bounds):]:
            bounds.append((0, s))

    return bounds


def roi(image, bounds):
    """Extract an ROI from the given ``image`` according to the given
    ``bounds``.

    This function can also be used to pad, or expand the field-of-view, of an
    image, by passing in negative low bound values, or high bound values which
    are larger than the image shape. The padded region will contain zeroes.

    :arg image:  :class:`.Image` object

    :arg bounds: Must be a sequence of tuples, containing the low/high bounds
                 for each voxel dimension, where the low bound is *inclusive*,
                 and the high bound is *exclusive*. For 4D images, the bounds
                 for the fourth dimension are optional.

    :returns:    A new :class:`.Image` object containing the region specified
                 by the ``bounds``.
    """

    bounds = _normaliseBounds(image.shape, bounds)

    newshape = [hi - lo for lo, hi in bounds]
    oldslc   = []
    newslc   = []

    # Figure out how to slice the input image
    # data array, and the corresponding slice
    # in the output data array.
    for (lo, hi), oldlen, newlen in zip(bounds, image.shape, newshape):

        oldlo = max(lo, 0)
        oldhi = min(hi, oldlen)
        newlo = max(0, -lo)
        newhi = newlo + (oldhi - oldlo)

        oldslc.append(slice(oldlo, oldhi))
        newslc.append(slice(newlo, newhi))

    oldslc = tuple(oldslc)
    newslc = tuple(newslc)

    # Copy the ROI into the new data array
    newdata         = np.zeros(newshape, dtype=image.dtype)
    newdata[newslc] = image.data[oldslc]

    # Create a new affine for the ROI,
    # with an appropriate offset along
    # each spatial dimension
    oldaff = image.voxToWorldMat
    offset = [lo for lo, hi in bounds[:3]]
    offset = affine.scaleOffsetXform([1, 1, 1], offset)
    newaff = affine.concat(oldaff, offset)

    return fslimage.Image(newdata,
                          xform=newaff,
                          header=image.header,
                          name=image.name + '_roi')
