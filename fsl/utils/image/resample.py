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

The :func:`applySmoothing` function is a sub-function of :func:`resample`.
"""


import numpy                as np
import scipy.ndimage        as ndimage

import fsl.transform.affine as affine


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


def resampleToReference(image, reference, matrix=None, **kwargs):
    """Resample ``image`` into the space of the ``reference``.

    This is a wrapper around :func:`resample` - refer to its documenttion
    for details on the other arguments and the return values.

    When resampling to a reference image, resampling will only be applied
    along the spatial (first three) dimensions.

    :arg image:     :class:`.Image` to resample
    :arg reference: :class:`.Nifti` defining the space to resample ``image``
                    into
    :arg matrix:    Optional world-to-world affine alignment matrix
    """

    oldShape = list(image.shape)
    newShape = list(reference.shape[:3])

    if matrix is None:
        matrix = np.eye(4)

    # If the input image is >3D, pad the
    # new shape so that we only resample
    # along the first 3 dimensions.
    if len(newShape) < len(oldShape):
        newShape = newShape + oldShape[len(newShape):]

    # Align the two images together
    # via their vox-to-world affines,
    # and the world-to-world affine
    # if provided
    matrix = affine.concat(image.worldToVoxMat,
                           affine.invert(matrix),
                           reference.voxToWorldMat)

    # If the input image is >3D, we
    # have to adjust the resampling
    # matrix to take into account the
    # additional dimensions (see scipy.
    # ndimage.affine_transform)
    if len(newShape) > 3:
        rotmat  = matrix[:3, :3]
        offsets = matrix[:3,  3]
        matrix  = np.eye(len(newShape) + 1)
        matrix[:3, :3] = rotmat
        matrix[:3, -1] = offsets

    kwargs['mode']     = kwargs.get('mode', 'constant')
    kwargs['newShape'] = newShape
    kwargs['matrix']   = matrix

    data = resample(image, **kwargs)[0]

    # The image is now in the same space
    # as the reference, so it inherits
    # ref's voxel-to-world affine
    return data, reference.voxToWorldMat


def resample(image,
             newShape,
             sliceobj=None,
             dtype=None,
             order=1,
             smooth=True,
             origin=None,
             matrix=None,
             mode=None,
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

    .. note:: If a custom resampling ``matrix`` is specified, the adjusted
              voxel-to-world afffine cannot be calculated by this function,
              so ``None`` will be returned instead.

    :arg image:    :class:`.Image` object to resample

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
                 dimensions of the resampled data, or ``None`` if a ``matrix``
                 was provided.
    """

    if sliceobj is None:     sliceobj = slice(None)
    if dtype    is None:     dtype    = image.dtype
    if origin   is None:     origin   = 'centre'
    if mode     is None:     mode     = 'nearest'
    if origin   == 'center': origin   = 'centre'

    ownMatrix = matrix is None

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
        matrix = affine.rescale(data.shape, newShape, origin)

    # same shape and identity matrix? the
    # image doesn't need to be resampled
    if np.all(np.isclose(data.shape, newShape)) and \
       np.all(np.isclose(matrix, np.eye(len(newShape) + 1))):
        return data, image.voxToWorldMat

    newShape = np.array(np.round(newShape), dtype=int)

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
    # image. We may be working with >3D data,
    # so here we discard the non-spatial
    # parts of the resampling matrix
    if matrix.shape != (4, 4):
        rotmat         = matrix[:3, :3]
        offsets        = matrix[:3, -1]
        matrix         = np.eye(4)
        matrix[:3, :3] = rotmat
        matrix[:3, -1] = offsets

    # We can only adjust the v2w affine if
    # the input space and resampling space
    # are aligned (e.g. if we're just
    # resampling to different dimensions).
    # We can't assume this when a custom
    # matrix is specified, so we just give
    # up and return None.
    if ownMatrix: matrix = affine.concat(image.voxToWorldMat, matrix)
    else:         matrix = None

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

    ratio = affine.decompose(matrix[:3, :3])[0]

    if len(newShape) > 3:
        ratio = np.concatenate((
            ratio,
            [float(o) / float(s)
             for o, s in zip(data.shape[3:], newShape[3:])]))

    sigma                = np.array(ratio)
    sigma[ratio <  1.1]  = 0
    sigma[ratio >= 1.1] *= 0.425

    return ndimage.gaussian_filter(data, sigma)
