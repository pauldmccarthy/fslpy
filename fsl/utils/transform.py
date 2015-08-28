#!/usr/bin/env python
#
# transform.py - Functions for working with affine transformation matrices.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions related to 3D image transformations and
spaces. The following functions are provided:

.. autosummary::
   :nosignatures:

   transform
   scaleOffsetXform
   invert
   concat
   axisBounds
"""

import numpy        as np
import numpy.linalg as linalg
import collections


def invert(x):
    """Inverts the given matrix using ``numpy.linalg.inv``. """
    return linalg.inv(x)


def concat(x1, x2):
    """Combines the two matrices (returns the dot product)."""
    return np.dot(x1, x2)


def scaleOffsetXform(scales, offsets):
    """Creates and returns an affine transformation matrix which encodes
    the specified scale(s) and offset(s).

    
    :arg scales:  A tuple of up to three values specifying the scale factors
                  for each dimension. If less than length 3, is padded with
                  ``1.0``.

    :arg offsets: A tuple of up to three values specifying the offsets for
                  each dimension. If less than length 3, is padded with
                  ``0.0``.

    :returns:     A ``numpy.float32`` array of size :math:`4 \\times 4`.
    """

    if not isinstance(scales,  collections.Sequence): scales  = [scales]
    if not isinstance(offsets, collections.Sequence): offsets = [offsets]

    lens = len(scales)
    leno = len(offsets)

    if lens < 3: scales  = scales  + [1.0] * (3 - lens)
    if leno < 3: offsets = offsets + [0.0] * (3 - leno)

    xform = np.eye(4, dtype=np.float32)

    xform[0, 0] = scales[0]
    xform[1, 1] = scales[1]
    xform[2, 2] = scales[2]

    xform[3, 0] = offsets[0]
    xform[3, 1] = offsets[1]
    xform[3, 2] = offsets[2]

    return xform


def axisBounds(shape, xform, axes=None, origin='centre'):
    """Returns the ``(lo, hi)`` bounds of the specified axis/axes in the world
    coordinate system defined by ``xform``.
    
    If the ``origin`` parameter is set to  ``centre`` (the default),
    this function assumes that voxel indices correspond to the voxel
    centre. For example, the voxel at ``(4, 5, 6)`` covers the space:
    
      ``[3.5 - 4.5, 4.5 - 5.5, 5.5 - 6.5]``
    
    So the bounds of the specified shape extends from the corner at

      ``(-0.5, -0.5, -0.5)``

    to the corner at

      ``(shape[0] - 0.5, shape[1] - 0.5, shape[1] - 0.5)``

    If the ``origin`` parameter is set to ``corner``, this function
    assumes that voxel indices correspond to the voxel corner. In this
    case, a voxel  at ``(4, 5, 6)`` covers the space:
    
      ``[4 - 5, 5 - 6, 6 - 7]``
    
    So the bounds of the specified shape extends from the corner at

      ``(0, 0, 0)``

    to the corner at

      ``(shape[0], shape[1]5, shape[1])``.

    
    :arg shape:  The ``(x, y, z)`` shape of the data.

    :arg xform:  Transformation matrix which transforms voxel coordinates
                 to the world coordinate system.

    :arg axes:   The world coordinate system axis bounds to calculate.

    :arg origin: Either ``'centre'`` or ``'origin'``

    :returns:    A list of tuples, one for each axis specified in the ``axes``
                 argument. Each tuple contains the ``(lo, hi)`` bounds of the
                 corresponding world coordinate system axis.
    """

    origin = origin.lower()

    # lousy US spelling
    if origin == 'center':
        origin = 'centre'

    if origin not in ('centre', 'corner'):
        raise ValueError('Invalid origin value: {}'.format(origin))

    scalar = False

    if axes is None:
        axes = [0, 1, 2]
        
    elif not isinstance(axes, collections.Iterable):
        scalar = True
        axes   = [axes]
    
    x, y, z = shape[:3]

    points = np.zeros((8, 3), dtype=np.float32)

    if origin == 'centre':
        x0 = -0.5
        y0 = -0.5
        z0 = -0.5
        x -=  0.5
        y -=  0.5
        z -=  0.5
    else:
        x0 = 0
        y0 = 0
        z0 = 0

    points[0, :] = [x0, y0, z0]
    points[1, :] = [x0, y0,  z]
    points[2, :] = [x0,  y, z0]
    points[3, :] = [x0,  y,  z]
    points[4, :] = [x,  y0, z0]
    points[5, :] = [x,  y0,  z]
    points[6, :] = [x,   y, z0]
    points[7, :] = [x,   y,  z]

    tx = transform(points, xform)

    lo = tx[:, axes].min(axis=0)
    hi = tx[:, axes].max(axis=0)

    if scalar: return (lo[0], hi[0])
    else:      return (lo,    hi)


        
def transform(p, xform, axes=None):
    """Transforms the given set of points ``p`` according to the given affine
    transformation ``xform``. 

    
    :arg p:     A sequence or array of points of shape :math:`N \\times  3`.

    :arg xform: An affine transformation matrix with which to transform the
                points in ``p``.

    :arg axes:  If you are only interested in one or two axes, and the source
                axes are orthogonal to the target axes (see the note below),
                you may pass in a 1D, ``N*1``, or ``N*2`` array as ``p``, and
                use this argument to specify which axis/axes that the data in
                ``p`` correspond to.

    :returns:   The points in ``p``, transformed by ``xform``, as a ``numpy``
                array with the same data type as the input.


    .. note:: The ``axes`` argument should only be used if the source
              coordinate system (the points in ``p``) axes are orthogonal
              to the target coordinate system (defined by the ``xform``).

              In other words, you can only use the ``axes`` argument if
              the ``xform`` matrix consists solely of translations and
              scalings.
    """

    p = _fillPoints(p, axes)
    t = np.dot(xform[:3, :3].T, p.T).T  + xform[3, :3]

    if axes is not None:
        t = t[:, axes]

    if t.size == 1: return t[0]
    else:           return t


def _fillPoints(p, axes):
    """Used by the :func:`transform` function. Turns the given array p into
    a ``N*3`` array of ``x,y,z`` coordinates. The array p may be a 1D array,
    or an ``N*2`` or ``N*3`` array.
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
