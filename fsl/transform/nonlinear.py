#!/usr/bin/env python
#
# nonlinear.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains data structures and functions for working with
nonlinear transformations.
"""


import numpy as np

import fsl.data.image as fslimage

from . import affine


class NonLinearTransform(fslimage.Image):
    """Class which represents a nonlinear transformation. This is just a base
    class for the :class:`DisplacementField` and :class:`CoefficientField`
    classes.


    A nonlinear transformation is an :class:`.Image` which contains
    some mapping between a source image coordinate system and a reference image
    coordinate system.


    In FSL, non-linear transformations are defined in the same space as the
    reference image. At a given location in the reference image space, the
    non-linear mapping at that location can be used to calculate the
    corresponding location in the source image space. Therefore, these
    non-linear transformation effectively encode a transformation *from* the
    reference image *to* the source image.
    """


    def __init__(self,
                 image,
                 src,
                 ref=None,
                 srcSpace=None,
                 refSpace=None,
                 **kwargs):
        """Create a ``NonLinearTransform``.

        :arg image:    A string containing the name of an image file to load,
                       or a :mod:`numpy` array, or a :mod:`nibabel` image
                       object.

        :arg src:      :class:`.Nifti` representing the source image.

        :arg ref:      :class:`.Nifti` representing the reference image.
                       If not provided, it is assumed that this
                       ``NonLinearTransform`` is defined in the same
                       space as the reference.

        :arg srcSpace: Coordinate system in the source image that this
                       ``NonLinearTransform`` maps from. Defaults to ``'fsl'``.

        :arg refSpace: Coordinate system in the reference image that this
                       ``NonLinearTransform`` maps to. Defaults to ``'fsl'``.

        All other arguments are passed through to :meth:`.Image.__init__`.
        """

        if ref      is None: ref      = self
        if srcSpace is None: srcSpace = 'fsl'
        if refSpace is None: refSpace = 'fsl'

        if srcSpace not in ('fsl', 'voxel', 'world') or \
           refSpace not in ('fsl', 'voxel', 'world'):
            raise ValueError('Invalid source/reference space: {} -> {}'.format(
                srcSpace, refSpace))

        fslimage.Image.__init__(self, image, **kwargs)

        # Displacement fields must be
        # defined in the same space
        # as the reference image
        if not self.sameSpace(ref):
            raise ValueError('Invalid reference image: {}'.format(ref))

        self.__src      = fslimage.Nifti(src.header.copy())
        self.__ref      = fslimage.Nifti(ref.header.copy())
        self.__srcSpace = srcSpace
        self.__refSpace = refSpace


    @property
    def src(self):
        """Return a reference to the :class:`.Nifti` instance representing
        the source image.
        """
        return self.__src


    @property
    def ref(self):
        """Return a reference to the :class:`.Nifti` instance representing
        the reference image.
        """
        return self.__ref


    @property
    def srcSpace(self):
        """Return the source image coordinate system this
        ``NonLinearTransform`` maps from - see :meth:`.Nifti.getAffine`.
        """
        return self.__srcSpace


    @property
    def refSpace(self):
        """Return the reference image coordinate system this
        ``NonLinearTransform`` maps to - see :meth:`.Nifti.getAffine`.
        """
        return self.__refSpace


class DisplacementField(NonLinearTransform):
    """Class which represents a displacement field which, at each voxel,
    contains an absolute or relative displacement between a source space and a
    reference space.
    """


    def __init__(self, *args, **kwargs):
        """Create a ``DisplacementField``.

        :arg dispType: Either ``'absolute'`` or ``'relative'``, indicating
                       the type of this displacement field. If not provided,
                       will be inferred via the :func:`detectDisplacementType`
                       function.

        All other arguments are passed through to
        :meth:`NonLinearTransform.__init__`.
        """

        dispType = kwargs.pop('dispType',  None)

        if dispType not in (None, 'relative', 'absolute'):
            raise ValueError('Invalid value for dispType: {}'.format(dispType))

        NonLinearTransform.__init__(self, *args, **kwargs)

        self.__dispType = dispType


    @property
    def displacementType(self):
        """The type of this ``DisplacementField`` - ``'absolute'`` or
        ``'relative'``.
        """
        if self.__dispType is None:
            self.__dispType = detectDisplacementType(self)
        return self.__dispType


    @property
    def absolute(self):
        """``True`` if this ``DisplacementField`` contains absolute
        displacements.
        """
        return self.displacementType == 'absolute'


    @property
    def relative(self):
        """``True`` if this ``DisplacementField`` contains relative
        displacements.
        """
        return self.displacementType == 'relative'


    def transform(self, coords, from_=None, to=None):
        """Transform the given XYZ coordinates from the reference image space
        to the source image space.

        :arg coords: A sequence of XYZ coordinates, or ``numpy`` array of shape
                     ``(n, 3)`` containing ``n`` sets of coordinates in the
                     reference space.
        :arg from_:  Reference image space that ``coords`` are defined in
        :arg to:     Source image space to transform ``coords`` into
        :returns    ``coords``, transformed into the source image space
        """

        if from_ is None: from_ = self.refSpace
        if to    is None: to    = self.srcSpace

        coords = np.asanyarray(coords)

        # We may need to pre-transform the
        # coordinates so they are in the
        # same reference image space as the
        # displacements
        if from_ != self.refSpace:
            xform  = self.ref.getAffine(from_, self.refSpace)
            coords = affine.transform(coords, xform)

        # We also need to make sure that the
        # coordinates are in voxels, so we
        # can look up the displacements
        if self.refSpace != 'voxel':
            xform  = self.ref.getAffine(self.refSpace, 'voxel')
            voxels = affine.transform(coords, xform)
        else:
            voxels = coords

        # Mask out the coordinates
        # that are out of bounds
        voxels  = np.round(voxels).astype(np.int)
        voxmask = (voxels >= [0, 0, 0]) & (voxels < self.shape[:3])
        voxmask = voxmask.all(axis=1)
        voxels  = voxels[voxmask]

        xs, ys, zs = voxels.T

        if self.absolute: disps = self.data[xs, ys, zs, :]
        else:             disps = self.data[xs, ys, zs, :] + coords[voxmask]

        # Make sure the coordinates
        # are in the requested
        # source image space
        if to != self.srcSpace:
            xform = self.src.getAffine(self.srcSpace, to)
            disps = affine.transform(disps, xform)

        # Nans for input coordinates
        # which were outside of the
        # field
        outcoords          = np.full(coords.shape, np.nan)
        outcoords[voxmask] = disps

        return outcoords


def detectDisplacementType(field):
    """Attempt to automatically determine whether a displacement field is
    specified in absolute or relative coordinates.

    :arg field: A :class:`DisplacementField`

    :returns:   ``'absolute'`` if it looks like ``field`` contains absolute
                displacements, ``'relative'`` otherwise.
    """

    # This test is based on the assumption
    # that a displacement field containing
    # absolute coordinates will have a
    # greater standard deviation than one
    # which contains relative coordinates.
    absdata = field[:]
    reldata = convertDisplacementType(field, 'relative')
    stdabs  = absdata.std(axis=(0, 1, 2)).sum()
    stdrel  = reldata.std(axis=(0, 1, 2)).sum()

    if stdabs > stdrel: return 'absolute'
    else:               return 'relative'


def convertDisplacementType(field, dispType=None):
    """Convert a displacement field between storing absolute and relative
    displacements.

    :arg field:    A :class:`DisplacementField` instance
    :arg dispType: Either ``'absolute'`` or ``'relative'``. If not provided,
                   the opposite type to ``field.displacementType`` is used.
    :returns:      A ``numpy.array`` containing the adjusted displacement
                   field.
    """

    if dispType is None:
        if field.displacementType == 'absolute': dispType = 'relative'
        else:                                    dispType = 'absolute'

    # Regardless of the conversion direction,
    # we need the coordinates of every voxel
    # in the reference FSL coordinate system.
    dx, dy, dz = field.shape[:3]
    xform      = field.getAffine('voxel', field.refSpace)

    coords     = np.meshgrid(np.arange(dx),
                             np.arange(dy),
                             np.arange(dz), indexing='ij')
    coords     = np.array(coords).transpose((1, 2, 3, 0))
    coords     = affine.transform(coords.reshape((-1, 3)), xform)
    coords     = coords.reshape((dx, dy, dz, 3))

    # If converting from relative to absolute,
    # we just add the voxel coordinates to
    # (what is assumed to be) the relative shift.
    # Or, to convert from absolute to relative,
    # we subtract the reference image voxels.
    if   dispType == 'absolute': return field.data + coords
    elif dispType == 'relative': return field.data - coords


def convertDisplacementSpace(field, from_, to):
    """Adjust the source and/or reference spaces of the given displacement
    field. See the :meth:`.Nifti.getAffine` method for the valid values for
    the ``from_`` and ``to`` arguments.

    :arg field: A :class:`DisplacementField` instance
    :arg from_: New reference image coordinate system
    :arg to:    New source image coordinate system

    :returns:   A new :class:`DisplacementField` which transforms between
                the reference ``from_`` coordinate system and the source ``to``
                coordinate system.
    """

    # Get the field in absolute coordinates
    # if necessary - these are our source
    # coordinates in the original "to" space.
    fieldcoords = field.data
    if field.relative: srccoords = convertDisplacementType(field)
    else:              srccoords = fieldcoords

    srccoords = srccoords.reshape((-1, 3))

    # Now transform those source coordinates
    # from the original source space to the
    # source space specified by "to"
    if to != field.srcSpace:

        srcmat    = field.src.getAffine(field.srcSpace, to)
        srccoords = affine.transform(srccoords, srcmat)

    # If we have been asked to return
    # an absolute displacement, the
    # reference "from_" coordinate
    # system is irrelevant - we're done.
    if field.absolute:
        fieldcoords = srccoords

    # Otherwise our displacement field
    # will contain relative displacements
    # between the reference image "from_"
    # coordinate system and the source
    # image "to" coordinate system. We
    # need to re-calculate the relative
    # displacements between the new
    # reference "from_" space and source
    # "to" space.
    else:
        refcoords = np.meshgrid(np.arange(field.shape[0]),
                                np.arange(field.shape[1]),
                                np.arange(field.shape[2]), indexing='ij')
        refcoords = np.array(refcoords)
        refcoords = refcoords.transpose((1, 2, 3, 0)).reshape((-1, 3))

        if from_ != 'voxel':
            refmat    = field.ref.getAffine('voxel', from_)
            refcoords = affine.transform(refcoords, refmat)

        fieldcoords = srccoords - refcoords

    return DisplacementField(
        fieldcoords.reshape(field.shape),
        header=field.header,
        src=field.src,
        ref=field.ref,
        srcSpace=to,
        refSpace=from_,
        dispType=field.displacementType)
