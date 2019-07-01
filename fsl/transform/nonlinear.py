#!/usr/bin/env python
#
# nonlinear.py - Functions/classes for non-linear transformations.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains data structures and functions for working with
FNIRT-style nonlinear transformations.


The :class:`DisplacementField` and :class:`CoefficientField` can be used to
load and interact with FNIRT transformation images. The following utility
functions are also available:

.. autosummary::
   :nosignatures:

   detectDisplacementType
   convertDisplacementType
   convertDisplacementSpace
   coefficientFieldToDisplacementField
"""


import              logging
import itertools as it

import numpy as np

import fsl.utils.memoize as memoize
import fsl.data.image    as fslimage

from . import               affine


log = logging.getLogger(__name__)


class NonLinearTransform(fslimage.Image):
    """Class which represents a nonlinear transformation. This is just a base
    class for the :class:`DisplacementField` and :class:`CoefficientField`
    classes.


    A nonlinear transformation is an :class:`.Image` which contains
    some mapping between a source image coordinate system and a reference image
    coordinate system.


    In FSL, non-linear transformations are defined in terms of the reference
    image coordinate system.  At a given location in the reference image
    space, the non-linear mapping at that location can be used to calculate
    the corresponding location in the source image space. Therefore, these
    non-linear transformation effectively encode a transformation *from* the
    reference image *to* the source image.
    """


    def __init__(self,
                 image,
                 src,
                 ref,
                 srcSpace=None,
                 refSpace=None,
                 **kwargs):
        """Create a ``NonLinearTransform``.

        :arg image:    A string containing the name of an image file to load,
                       or a :mod:`numpy` array, or a :mod:`nibabel` image
                       object.

        :arg src:      :class:`.Nifti` representing the source image.

        :arg ref:      :class:`.Nifti` representing the reference image.

        :arg srcSpace: Coordinate system in the source image that this
                       ``NonLinearTransform`` maps to. Defaults to ``'fsl'``.

        :arg refSpace: Coordinate system in the reference image that this
                       ``NonLinearTransform`` maps from. Defaults to ``'fsl'``.

        All other arguments are passed through to :meth:`.Image.__init__`.
        """

        if srcSpace is None: srcSpace = 'fsl'
        if refSpace is None: refSpace = 'fsl'

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


    def transform(self, coords, from_=None, to=None):
        """Transform coordinates from the reference image space to the source
        image space. Implemented by sub-classes.

        :arg coords: A sequence of XYZ coordinates, or ``numpy`` array of shape
                     ``(n, 3)`` containing ``n`` sets of coordinates in the
                     reference space.
        :arg from_:  Reference image space that ``coords`` are defined in
        :arg to:     Source image space to transform ``coords`` into
        :returns    ``coords``, transformed into the source image space
        """
        raise NotImplementedError()


class DisplacementField(NonLinearTransform):
    """Class which represents a displacement field which, at each voxel,
    contains an absolute or relative displacement between a source space and a
    reference space.
    """


    def __init__(self, image, src, ref=None, **kwargs):
        """Create a ``DisplacementField``.

        :arg ref:      Optional. If not provided, it is assumed that the
                       reference is defined in the same space as ``image``.

        :arg dispType: Either ``'absolute'`` or ``'relative'``, indicating
                       the type of this displacement field. If not provided,
                       will be inferred via the :func:`detectDisplacementType`
                       function.

        All other arguments are passed through to
        :meth:`NonLinearTransform.__init__`.
        """

        if ref is None:
            ref = self

        dispType = kwargs.pop('dispType',  None)

        if dispType not in (None, 'relative', 'absolute'):
            raise ValueError('Invalid value for dispType: {}'.format(dispType))

        NonLinearTransform.__init__(self, image, src, ref, **kwargs)

        if not self.sameSpace(self.ref):
            raise ValueError('Invalid reference image: {}'.format(self.ref))

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
        :returns     ``coords``, transformed into the source image space
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


class CoefficientField(NonLinearTransform):
    """Class which represents a cubic B-spline coefficient field generated by
    FNIRT.

    The :meth:`displacements` method can be used to calculate relative
    displacements for a set of reference space voxel coordinates.


    A FNIRT coefficient field typically contains a *premat*, a global affine
    transformation from the source space to the reference space, which was
    used as the starting point for the non-linear optimisation performed by
    FNIRT.

    This affine must be provided when creating a ``CoefficientField``, and is
    subsequently accessed via the :meth:`srcToRefMat` or :meth:`premat`
    attributes.
    """


    def __init__(self,
                 image,
                 src,
                 ref,
                 srcSpace,
                 refSpace,
                 fieldType,
                 knotSpacing,
                 srcToRefMat,
                 fieldToRefMat,
                 **kwargs):
        """Create a ``CoefficientField``.

        :arg fieldType:     Must be ``'cubic'``

        :arg knotSpacing:   A tuple containing the spline knot spacings along
                            each axis.

        :arg srcToRefMat:   Initial global affine transformation from the
                            source image to the reference image. This is
                            assumed to be a FLIRT-style matrix, i.e. it
                            transforms from source image FSL coordinates
                            into reference image FSL coordinates (scaled
                            voxels).

        :arg fieldToRefMat: Affine transformation which can transform reference
                            image voxel coordinates into coefficient field
                            voxel coordinates.

        See the :class:`NonLinearTransform` class for details on the other
        arguments.
        """

        if fieldType not in ('cubic',):
            raise ValueError('Unsupported field type: {}'.format(fieldType))

        NonLinearTransform.__init__(self,
                                    image,
                                    src,
                                    ref,
                                    srcSpace,
                                    refSpace,
                                    **kwargs)

        self.__fieldType     = fieldType
        self.__knotSpacing   = tuple(knotSpacing)
        self.__srcToRefMat   = np.copy(srcToRefMat)
        self.__fieldToRefMat = np.copy(fieldToRefMat)
        self.__refToFieldMat = affine.invert(self.__fieldToRefMat)


    @property
    def fieldType(self):
        """Return the type of the coefficient field, currently always
        ``'cubic'``.
        """
        return self.__fieldType


    @property
    def srcToRefMat(self):
        """Return an initial global affine transformation from the source
        image to the reference image.
        """
        return np.copy(self.__srcToRefMat)


    @property
    def knotSpacing(self):
        """Return a tuple containing spline knot spacings along the x, y, and
        z axes.
        """
        return self.__knotSpacing


    @property
    def fieldToRefMat(self):
        """Return an affine transformation which can transform coefficient
        field voxel coordinates into reference image voxel coordinates.
        """
        return np.copy(self.__fieldToRefMat)


    @property
    def refToFieldMat(self):
        """Return an affine transformation which can transform reference
        image voxel coordinates into coefficient field voxel coordinates.
        """
        return np.copy(self.__refToFieldMat)


    @memoize.Instanceify(memoize.memoize)
    def asDisplacementField(self, dispType='relative', premat=True):
        """Convert this ``CoefficientField`` to a :class:`DisplacementField`.
        """
        return coefficientFieldToDisplacementField(self, dispType, premat)


    def transform(self, coords, from_=None, to=None, premat=True):
        """Overrides :meth:`NonLinearTransform.transform`. Transforms the
        given ``coords`` from the reference image space into the source image
        space.

        :arg coords: A sequence of XYZ coordinates, or ``numpy`` array of shape
                     ``(n, 3)`` containing ``n`` sets of coordinates in the
                     reference space.

        :arg from_:  Reference image space that ``coords`` are defined in

        :arg to:     Source image space to transform ``coords`` into

        :returns    ``coords``, transformed into the source image space

        :arg premat: If ``True``, the inverse :meth:`srcToRefMat` is applied
                     to the coordinates after the displacements have been
                     addd.
        """
        df = self.asDisplacementField(premat=premat)
        return df.transform(coords, from_, to)


    def displacements(self, coords):
        """Calculate the relative displacemenets for the given coordinates.

        :arg coords: ``(N, 3)`` array of reference image voxel coordinates.
        :return:      A ``(N, 3)`` array  of relative displacements to the
                      source image for ``coords``
        """

        if self.fieldType != 'cubic':
            raise NotImplementedError()

        # See
        #   https://www.cs.jhu.edu/~cis/cista/746/papers/\
        #     RueckertFreeFormBreastMRI.pdf
        #   https://www.fmrib.ox.ac.uk/datasets/techrep/tr07ja2/tr07ja2.pdf

        # Cubic b-spline basis functions
        def b0(u):
            return ((1 - u) ** 3) / 6

        def b1(u):
            return (3 * (u ** 3) - 6 * (u ** 2) + 4) / 6

        def b2(u):
            return (-3 * (u ** 3) + 3 * (u ** 2)  + 3 * u + 1) / 6

        def b3(u):
            return (u ** 3) / 6

        b = [b0, b1, b2, b3]

        fdata      = self.data
        nx, ny, nz = self.shape[:3]
        ix, iy, iz = self.ref.shape[:3]

        # Convert the given voxel coordinates
        # into the corresponding coefficient
        # field voxel coordinates
        x, y, z    = coords.T
        i, j, k    = affine.transform(coords, self.refToFieldMat).T

        # i, j, k: coefficient field indices
        # u, v, w: position of the ref voxel
        #          on the current spline
        u = np.remainder(i, 1)
        v = np.remainder(j, 1)
        w = np.remainder(k, 1)
        i = np.floor(i).astype(np.int)
        j = np.floor(j).astype(np.int)
        k = np.floor(k).astype(np.int)

        disps = np.zeros(coords.shape)

        for l, m, n in it.product(range(4), range(4), range(4)):
            il   = i + l
            jm   = j + m
            kn   = k + n
            mask = (il >= 0)  & \
                   (il <  nx) & \
                   (jm >= 0)  & \
                   (jm <  ny) & \
                   (kn >= 0)  & \
                   (kn <  nz)

            il = il[mask]
            jm = jm[mask]
            kn = kn[mask]
            uu = u[ mask]
            vv = v[ mask]
            ww = w[ mask]

            cx, cy, cz = fdata[il, jm, kn, :].T
            c          = b[l](uu) * b[m](vv) * b[n](ww)

            disps[mask, 0] += c * cx
            disps[mask, 1] += c * cy
            disps[mask, 2] += c * cz

        return disps


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


def coefficientFieldToDisplacementField(field,
                                        dispType='relative',
                                        premat=True):
    """Convert a :class:`CoefficientField` into a :class:`DisplacementField`.

    :arg field:    :class:`CoefficientField` to convert

    :arg dispType: The type of displcaement field - either ``'relative'`` (the
                   default) or ``'absolute'``.

    :arg premat:   If ``True`` (the default), the :meth:`srcToRefMat` is
                   encoded into the displacements.

    :return:       :class:`DisplacementField` calculated from ``field``.
    """

    # Generate coordinates for every
    # voxel in the reference image
    ix, iy, iz = field.ref.shape[:3]
    x,  y,  z  = np.meshgrid(np.arange(ix),
                             np.arange(iy),
                             np.arange(iz), indexing='ij')
    x          = x.flatten()
    y          = y.flatten()
    z          = z.flatten()
    xyz        = np.vstack((x, y, z)).T

    # There are three spaces to consider here:
    #
    #  - ref space:         Reference image scaled voxels ("fsl" space)
    #
    #  - aligned-src space: Source image scaled voxels, after the
    #                       source image has been linearly aligned to
    #                       the reference via the field.srcToRefMat
    #                       This will typically be equivalent to ref
    #                       space
    #
    #  - orig-src space:    Source image scaled voxels, in the coordinate
    #                       system of the original source image, without
    #                       linear alignment to the reference image

    # The displacements method will
    # return relative displacements
    # from ref space to aligned-src
    # space.
    disps   = field.displacements(xyz).reshape((ix, iy, iz, 3))
    rdfield = DisplacementField(disps,
                                src=field.src,
                                ref=field.ref,
                                srcSpace=field.srcSpace,
                                refSpace=field.refSpace,
                                header=field.ref.header,
                                dispType='relative')

    if (dispType == 'relative') and (not premat):
        return rdfield

    # Convert to absolute - the
    # displacements will now be
    # absolute coordinates in
    # aligned-src space
    disps = convertDisplacementType(rdfield)

    # Apply the premat if requested -
    # this will transform the coordinates
    # from aligned-src to orig-src space.
    if premat:

        # We apply the premat in the same way
        # that fnirtfileutils does - applying
        # the inverse affine to every ref space
        # voxel coordinate, then adding it to
        # the existing displacements.
        shape    = disps.shape
        disps    = disps.reshape(-1, 3)
        refToSrc = affine.invert(field.srcToRefMat)
        premat   = affine.concat(refToSrc - np.eye(4),
                                 field.ref.getAffine('voxel', 'fsl'))
        disps    = disps + affine.transform(xyz, premat)
        disps    = disps.reshape(shape)

        # note that convertwarp applies a premat
        # differently - its method is equivalent
        # to directly transforming the existing
        # absolute displacements, i.e.:
        #
        #   disps = affine.transform(disps, refToSrc)

    adfield = DisplacementField(disps,
                                src=field.src,
                                ref=field.ref,
                                srcSpace=field.srcSpace,
                                refSpace=field.refSpace,
                                header=field.ref.header,
                                dispType='absolute')

    # Not either return absolute displacements,
    # or convert back to relative displacements
    if dispType == 'absolute':
        return adfield
    else:
        return DisplacementField(convertDisplacementType(adfield),
                                 src=field.src,
                                 ref=field.ref,
                                 srcSpace=field.srcSpace,
                                 refSpace=field.refSpace,
                                 header=field.ref.header,
                                 dispType='relative')
