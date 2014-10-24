#!/usr/bin/env python
#
# transform.py - Functions for working with affine transformation matrices.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions related to 3D image transformations and
spaces.
"""

import numpy        as np
import numpy.linalg as linalg
import collections


def invert(x):
    """Inverts the given matrix. """
    return linalg.inv(x)


def concat(x1, x2):
    """Combines the two matrices (returns the dot product)."""
    return np.dot(x1, x2)


def axisBounds(shape, xform, axis):
    """Returns the (lo, hi) bounds of the specified axis."""
    x, y, z = shape[:3]

    x -= 0.5
    y -= 0.5
    z -= 0.5

    points = np.zeros((8, 3), dtype=np.float32)

    points[0, :] = [-0.5, -0.5, -0.5]
    points[1, :] = [-0.5, -0.5,  z]
    points[2, :] = [-0.5,  y,   -0.5]
    points[3, :] = [-0.5,  y,    z]
    points[4, :] = [x,    -0.5, -0.5]
    points[5, :] = [x,    -0.5,  z]
    points[6, :] = [x,     y,   -0.5]
    points[7, :] = [x,     y,    z]

    tx = transform(points, xform)

    lo = tx[:, axis].min()
    hi = tx[:, axis].max()

    return (lo, hi)


def axisLength(shape, xform, axis):
    """Return the length, in real world units, of the specified axis.
    """
        
    points          = np.zeros((2, 3), dtype=np.float32)
    points[:]       = [-0.5, -0.5, -0.5]
    points[1, axis] = shape[axis] - 0.5 

    tx = transform(points, xform)

    # euclidean distance between each boundary point
    return sum((tx[0, :] - tx[1, :]) ** 2) ** 0.5 

        
def transform(p, xform, axes=None):
    """Transforms the given set of points ``p`` according to the given affine
    transformation ``x``. The transformed points are returned as a
    :class:``numpy.float64`` array.
    """

    p = _fillPoints(p, axes)
    t = np.zeros((len(p), 3), dtype=np.float64)

    x = p[:, 0]
    y = p[:, 1]
    z = p[:, 2]

    t[:, 0] = x * xform[0, 0] + y * xform[1, 0] + z * xform[2, 0] + xform[3, 0]
    t[:, 1] = x * xform[0, 1] + y * xform[1, 1] + z * xform[2, 1] + xform[3, 1]
    t[:, 2] = x * xform[0, 2] + y * xform[1, 2] + z * xform[2, 2] + xform[3, 2]

    if axes is None: axes = [0, 1, 2]

    tx = np.array(t[:, axes], dtype=np.float64)

    if tx.size == 1: return tx[0]
    else:            return tx


def _fillPoints(p, axes):
    """Used by the :func:`transform` function. Turns the given array p into
    a N*3 array of x,y,z coordinates. The array p may be a 1D array, or an
    N*2 or N*3 array.
    """

    if not isinstance(p, collections.Iterable): p = [p]
    
    p = np.array(p)

    if axes is None: return p

    if not isinstance(axes, collections.Iterable): axes = [axes]

    if p.ndim == 1:
        p = p.reshape((len(p), 1))

    if p.ndim != 2:
        raise ValueError('Points array must be either one or two '
                         'dimensions')

    if len(axes) != p.shape[1]:
        raise ValueError('Points array shape does not match specified '
                         'number of axes')

    newp = np.zeros((len(p), 3), dtype=p.dtype)

    for i, ax in enumerate(axes):
        newp[:, ax] = p[:, i]

    return newp
