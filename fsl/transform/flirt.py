#!/usr/bin/env python
#
# flirt.py - Functions for working with FLIRT matrices.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains functions for working with FLIRT affine transformation
matrices. The following functions are available:

.. autosummary::
   :nosignatures:

   readFlirt
   writeFlirt
   fromFlirt
   toFlirt
   flirtMatrixToSform
   sformToFlirtMatrix



FLIRT transformation matrices are affine matrices of shape ``(4, 4)`` which
encode a linear transformation from a source image to a reference image. FLIRT
matrices are defined in terms of *FSL coordinates*, which is a coordinate
system where voxels are scaled by pixdims, and with a left-right flip if the
image ``sform`` has a positive determinant.


FLIRT matrices thus encode a transformation from source image FSL coordinates
to reference image FSL coordinates.
"""


import numpy as np

from .affine import concat


def readFlirt(fname):
    """Reads a FLIRT matrix from a file. """
    return np.loadtxt(fname)


def writeFlirt(xform, fname):
    """Writes the given FLIRT matrix to a file. """
    np.savetxt(fname, xform, fmt='%1.15g')


def fromFlirt(xform, src, ref, from_='voxel', to='world'):
    """Convert a FLIRT affine matrix into another affine.

    Given a FLIRT matrix, and the source and reference images with which the
    FLIRT matrix is associated, converts the matrix into an affine matrix
    which can transform coordinates from the source image ``from_`` coordinate
    system to the reference image ``to`` coordinate system.

    The ``from_`` and ``to`` arguments specify the desired spaces that the
    returned affine should transform between. The default values
    (``from_='voxel'`` and ``to='world'`` will generate an affine which
    transforms from voxels in the source image to world-coordinates in the
    reference image.

    Valid values for the ``from_`` and ``to`` arguments are:

     - ``voxel``: The voxel coordinate system
     - ``fsl``: The FSL coordiante system (voxels scaled by pixdims, with the
       X axis inverted if the image sform/qform has a positive determinant)
     - ``world``  The world coordinate system

    See the :class:`.Nifti` class documentation and the
    :meth:`.Nifti.getAffine` method for more details.

    :arg xform: ``numpy`` array of shape ``(4, 4)`` containing a FLIRT
                transformation matrix.
    :arg src:   :class:`.Nifti` object, the ``xform`` source image
    :arg ref:   :class:`.Nifti` object, the ``xform`` reference image
    :arg from_: Desired source coordinate system
    :arg to:    Desired reference coordinate system
    :returns:   ``numpy`` array of shape ``(4, 4)`` containing a matrix
                encoding a transformation from the source ``from_`` to
                the reference ``to`` coordinate systems.
    """
    premat  = src.getAffine(from_, 'fsl')
    postmat = ref.getAffine('fsl', to)
    return concat(postmat, xform, premat)


def toFlirt(xform, src, ref, from_='voxel', to='world'):
    """Convert an affine matrix into a FLIRT matrix.

    :returns:   ``numpy`` array of shape ``(4, 4)`` containing a matrix
                encoding a transformation from the source ``from_`` to
                the reference ``to`` coordinate systems.
    :arg src:   :class:`.Nifti` object, the ``xform`` source image
    :arg ref:   :class:`.Nifti` object, the ``xform`` reference image
    :arg from_: ``xform`` source coordinate system
    :arg to:    ``xform`` target coordinate system
    :returns:   A ``numpy`` array of shape ``(4, 4)`` containing a FLIRT
                transformation matrix from ``src`` to ``ref``.
    """
    premat  = src.getAffine('fsl', from_)
    postmat = ref.getAffine(to, 'fsl')
    return concat(postmat, xform, premat)


def flirtMatrixToSform(flirtMat, srcImage, refImage):
    """Converts the given ``FLIRT`` transformation matrix into a
    transformation from the source image voxel coordinate system to
    the reference image world coordinate system.

    To construct a transformation from source image voxel coordinates into
    reference image world coordinates, we need to combine the following:

      1. Source voxels -> Source scaled voxels
      2. Source scaled voxels -> Reference scaled voxels (the FLIRT matrix)
      3. Reference scaled voxels -> Reference voxels
      4. Reference voxels -> Reference world (the reference image sform)

    :arg flirtMat: A ``(4, 4)`` transformation matrix
    :arg srcImage: Source :class:`.Image`
    :arg refImage: Reference :class:`.Image`
    """
    return fromFlirt(flirtMat, srcImage, refImage, 'voxel', 'world')


def sformToFlirtMatrix(srcImage, refImage, srcXform=None):
    """Under the assumption that the given ``srcImage`` and ``refImage`` share a
    common world coordinate system (defined by their
    :attr:`.Nifti.voxToWorldMat` attributes), this function will calculate and
    return a transformation matrix from the ``srcImage`` FSL coordinate system
    to the ``refImage`` FSL coordinate system, that can be saved to disk and
    used with FLIRT, to resample the source image to the space of the
    reference image.

    :arg srcImage: Source :class:`.Image`
    :arg refImage: Reference :class:`.Image`
    :arg srcXform: Optionally used in place of the ``srcImage``
                   :attr:`.Nifti.voxToWorldMat`
    """

    srcScaledVoxToVoxMat = srcImage.scaledVoxToVoxMat
    srcVoxToWorldMat     = srcImage.voxToWorldMat
    refWorldToVoxMat     = refImage.worldToVoxMat
    refVoxToScaledVoxMat = refImage.voxToScaledVoxMat

    if srcXform is not None:
        srcVoxToWorldMat = srcXform

    return concat(refVoxToScaledVoxMat,
                  refWorldToVoxMat,
                  srcVoxToWorldMat,
                  srcScaledVoxToVoxMat)
