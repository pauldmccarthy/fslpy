#!/usr/bin/env python
#
# resample.py - The resample functino
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines the :func:`resample` function, which can be used
to resample an :class:`.Image` object to a different resolution.

The :func:`resampleToPixdims` and :func:`resampleToReference` functions
are convenience wrappers around :func:`resample`.

The :func:`applySmoothing` and :func:`calculateMatrix` functions are
sub-functions of :func:`resample`.
"""


import collections.abc     as abc

import numpy               as np
import scipy.ndimage       as ndimage

import fsl.utils.transform as transform


def resampleToPixdims(image, newPixdims, **kwargs):
    """Resample ``image`` so that it has the specified voxel dimensions.

    This is a wrapper around :func:`resample` - refer to its documenttion
    for details on the other arguments and the return values.

    :arg image:   :class:`.Image` to resample
    :arg pixdims: New voxel dimensions to resample ``image`` to.
    """
    newPixdims = np.array(newPixdims)
    oldShape   = np.array(image.shape)
    oldPixdims = np.array(image.pixdim)
    newShape   = oldShape * (oldPixdims / newPixdims)
    return resample(image, newShape, **kwargs)


def resampleToReference(image, reference, **kwargs):
    """Resample ``image`` into the space of the ``reference``.

    This is a wrapper around :func:`resample` - refer to its documenttion
    for details on the other arguments and the return values.

    :arg image:     :class:`.Image` to resample
    :arg reference: :class:`.Nifti` defining the space to resample ``image``
                    into
    """

    kwargs['mode']     = kwargs.get('mode', 'constant')
    kwargs['newShape'] = reference.shape
    kwargs['matrix']   = transform.concat(image.worldToVoxMat,
                                          reference.voxToWorldMat)
    return resample(image, **kwargs)


def resample(image,
             newShape,
             sliceobj=None,
             dtype=None,
             order=1,
             smooth=True,
             origin='centre',
             matrix=None,
             mode='nearest',
             cval=0):
    """Returns a copy of the data in the ``image``, resampled to the specified
    ``newShape``.

    The space that the image is resampled into can be defined in one of the
    following ways, in decreasing order of precedence:

      1. If a ``matrix`` is provided, it is applied to the voxel coordinates
         when retrieving values from the ``image``

      2. Otherwise the image is simply scaled according to the ratio calculated
         by ``image.shape / newShape``. In this case the ``origin`` argument
         may be used to adjust the alignemnt of the original and resampled
         voxel grids.

    See the ``scipy.ndimage.affine_transform`` function for more details,
    particularly on the ``order``, ``matrix``, ``mode`` and
    ``cval`` arguments.

    :arg newShape: Desired shape. May containg floating point values, in which
                   case the resampled image will have shape
                   ``round(newShape)``, but the voxel sizes will have scales
                   ``self.shape / newShape`` (unless ``matrix`` is specified).

    :arg sliceobj: Slice into this ``Image``. If ``None``, the whole
                   image is resampled, and it is assumed that it has the
                   same number of dimensions as  ``newShape``. A
                   :exc:`ValueError` is raised if this is not the case.

    :arg dtype:    ``numpy`` data type of the resampled data. If ``None``,
                   the :meth:`dtype` of this ``Image`` is used.

    :arg order:    Spline interpolation order, passed through to the
                   ``scipy.ndimage.affine_transform`` function - ``0``
                   corresponds to nearest neighbour interpolation, ``1``
                   (the default) to linear interpolation, and ``3`` to
                   cubic interpolation.

    :arg smooth:   If ``True`` (the default), the data is smoothed before
                   being resampled, but only along axes which are being
                   down-sampled (i.e. where ``newShape[i] < self.shape[i]``).

    :arg origin:   ``'centre'`` (the default) or ``'corner'``. ``'centre'``
                   resamples the image such that the centre of the corner
                   voxels of this image and the resampled data are
                   aligned. ``'corner'`` resamples the image such that
                   the corner of the corner voxels are aligned (and
                   therefore the voxel grids are aligned).
                   Ignored if ``offset`` or ``matrix`` is specified.

    :arg matrix:   Arbitrary affine transformation matrix to apply to the
                   voxel coordinates of ``image`` when resampling.

    :arg mode:     How to handle regions which are outside of the image FOV.
                   Defaults to `''nearest'``.

    :arg cval:     Constant value to use when ``mode='constant'``.

    :returns: A tuple containing:

               - A ``numpy`` array of shape ``newShape``, containing
                 an interpolated copy of the data in this ``Image``.

               - A ``numpy`` array of shape ``(4, 4)``, containing the
                 adjusted voxel-to-world transformation for the spatial
                 dimensions of the resampled data.
    """

    if sliceobj is None:     sliceobj = slice(None)
    if dtype    is None:     dtype    = image.dtype
    if origin   == 'center': origin   = 'centre'

    if origin not in ('centre', 'corner'):
        raise ValueError('Invalid value for origin: {}'.format(origin))

    data = np.array(image[sliceobj], dtype=dtype, copy=False)

    if len(data.shape) != len(newShape):
        raise ValueError('Data dimensions do not match new shape: '
                         'len({}) != len({})'.format(data.shape, newShape))

    # If matrix not provided, calculate
    # a scaling/offset matrix from the
    # old/new shape ratio and the origin
    # setting.
    if matrix is None:
        matrix = calculateMatrix(data.shape, newShape, origin)

    # calculateMatrix will return None
    # if it decides that the image
    # doesn't need to be resampled
    if matrix is None:
        return data, image.voxToWorldMat

    newShape = np.array(np.round(newShape), dtype=np.int)

    # Apply smoothing if requested,
    # and if not using nn interp
    if order > 0 and smooth:
        data = applySmoothing(data, matrix, newShape)

    # Do the resample thing
    data = ndimage.affine_transform(data,
                                    matrix,
                                    output_shape=newShape,
                                    order=order,
                                    mode=mode,
                                    cval=cval)

    # Construct an affine transform which
    # puts the resampled image into the
    # same world coordinate system as this
    # image. The calculateMatrix function
    # might not return a 4x4 matrix, so we
    # make sure it is valid.
    if matrix.shape != (4, 4):
        matrix = np.vstack((matrix[:3, :4], [0, 0, 0, 1]))
    matrix = transform.concat(image.voxToWorldMat, matrix)

    return data, matrix


def applySmoothing(data, matrix, newShape):
    """Called by the :func:`resample` function.

    If interpolating and smoothing, we apply a gaussian filter along axes with
    a resampling ratio greater than 1.1. We do this so that interpolation has
    an effect when down-sampling to a resolution where the voxel centres are
    aligned (as otherwise any interpolation regime will be equivalent to
    nearest neighbour). This more-or-less mimics the behaviour of FLIRT.

    See the ``scipy.ndimage.gaussian_filter`` function for more details.

    :arg data:     Data to be smoothed.
    :arg matrix:   Affine matrix to be used during resampling. The voxel
                   scaling factors are extracted from this.
    :arg newShape: Shape the data is to be resampled into.
    :returns:      A smoothed copy of ``data``.
    """

    ratio = transform.decompose(matrix[:3, :3])[0]

    if len(newShape) > 3:
        ratio = np.concatenate((
            ratio,
            [float(o) / float(s)
             for o, s in zip(data.shape[3:], newShape[3:])]))

    sigma                = np.array(ratio)
    sigma[ratio <  1.1]  = 0
    sigma[ratio >= 1.1] *= 0.425

    return ndimage.gaussian_filter(data, sigma)


def calculateMatrix(oldShape, newShape, origin):
    """Calculates an affine matrix to use for resampling.

    Called by :func:`resample`.  The matrix will contain scaling factors
    determined from the ``oldShape / newShape`` ratio, and an offset
    determined from the ``origin``.

    :arg oldShape: Shape of input data
    :arg newShape: Shape to resample data to
    :arg origin:   Voxel grid alignment - either ``'centre'`` or ``'corner'``
    :returns:      An affine matrix that can be passed to
                   ``scipy.ndimage.affine_transform``.
    """

    oldShape = np.array(oldShape, dtype=np.float)
    newShape = np.array(newShape, dtype=np.float)

    if np.all(np.isclose(oldShape, newShape)):
        return None

    # Otherwise we calculate a
    # scaling matrix from the
    # old/new shape ratio, and
    # specify an offset
    # according to the origin
    else:
        ratio = oldShape / newShape
        scale = np.diag(ratio)

        # Calculate an offset from the
        # origin - the default behaviour
        # (centre) causes the corner voxel
        # of the output to have the same
        # centre as the corner voxel of
        # the input. If the origin is
        # 'corner', we apply an offset
        # which effectively causes the
        # voxel grids of the input and
        # output to be aligned.
        if   origin == 'centre': offset = 0
        elif origin == 'corner': offset = list((ratio - 1) / 2)

        if not isinstance(offset, abc.Sequence):
            offset = [offset] * len(newShape)

        # ndimage.affine_transform will accept
        # a matrix of shape (ndim, ndim + 1)
        matrix = np.hstack((scale, np.atleast_2d(offset).T))

    return matrix
