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
    some mapping from a source image coordinate system to a reference image
    coordinate system.
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

        :arg src:      :class:`.Nifti` representing the sourceimage

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

        if not (isinstance(src, (fslimage.Nifti, type(None))) and
                isinstance(ref,  fslimage.Nifti)):
            raise ValueError('Invalid source/reference: {} -> {}'.format(
                src, ref))

        if srcSpace not in ('fsl', 'voxel', 'world') or \
           refSpace not in ('fsl', 'voxel', 'world'):
            raise ValueError('Invalid source/reference space: {} -> {}'.format(
                srcSpace, refSpace))

        fslimage.Image.__init__(self, image, **kwargs)

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
    contains an absolute or relative displacement from a source space to a
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


    def transform(self, coords):
        raise NotImplementedError()


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
    v2fsl      = field.getAffine('voxel', field.srcSpace)
    coords     = np.meshgrid(np.arange(dx),
                             np.arange(dy),
                             np.arange(dz), indexing='ij')
    coords     = np.array(coords).transpose((1, 2, 3, 0))
    coords     = affine.transform(coords.reshape((-1, 3)), v2fsl)
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
    :arg from_: New source image coordinate system
    :arg to:    New reference image coordinate system

    :returns:   A new :class:`DisplacementField` which transforms from
                the source ``from_`` coordinate system to the reference ``to``
                coordinate system.
    """

    # Get the field in absolute
    # coordinates if necessary
    fieldcoords = field.data
    if field.relative: srccoords = convertDisplacementType(field)
    else:              srccoords = fieldcoords

    # Now transform those source
    # coordinates from the original
    # source space to the source
    # space specified by "from_"
    srcmat    = field.src.getAffine(field.srcSpace, from_)
    srccoords = srccoords.reshape((-1, 3))
    srccoords = affine.transform(srccoords, srcmat)

    # If we have been asked to return
    # an absolute displacement, the
    # reference "to" coordinate system
    #  is irrelevant - we're done.
    if field.absolute:
        fieldcoords = srccoords

    # Otherwise our displacement field
    # will contain relative displacements
    # betwee the reference image "to"
    # coordinate system and the source
    # image "from_" coordinate system.
    # We need to re-calculate the relative
    # displacements from source "from_"
    # space into reference "to" space.
    else:
        refmat      = field.ref.getAffine(field.refSpace, to)
        refcoords   = fieldcoords.reshape((-1, 3))
        refcoords   = affine.transform(refcoords, refmat)
        fieldcoords = srccoords - refcoords

    return DisplacementField(
        fieldcoords.reshape(field.shape),
        header=field.header,
        src=field.src,
        ref=field.ref,
        srcSpace=from_,
        refSpace=to,
        dispType=field.displacementType)
