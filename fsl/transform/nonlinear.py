#!/usr/bin/env python
#
# nonlinear.py - Functions/classes for non-linear transformations.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains data structures and functions for working with
FNIRT-style nonlinear transformations.


The :class:`DeformationField` and :class:`CoefficientField` can be used to
load and interact with FNIRT-style transformation images. The following
utility functions are also available:


.. autosummary::
   :nosignatures:

   detectDeformationType
   convertDeformationType
   convertDeformationSpace
   applyDeformation
   coefficientFieldToDeformationField
"""


import                                logging
import itertools                   as it

import numpy                       as np
import scipy.ndimage.interpolation as ndinterp

import fsl.utils.memoize           as memoize
import fsl.data.image              as fslimage
import fsl.utils.image.resample    as resample
from . import                         affine


log = logging.getLogger(__name__)


class NonLinearTransform(fslimage.Image):
    """Class which represents a nonlinear transformation. This is just a base
    class for the :class:`DeformationField` and :class:`CoefficientField`
    classes.


    A nonlinear transformation is an :class:`.Image` which contains
    some mapping between a source image coordinate system and a reference image
    coordinate system.


    In FSL, non-linear transformations are defined in terms of the reference
    image coordinate system.  At a given location in the reference image
    space, the non-linear mapping at that location can be used to calculate
    the corresponding location in the source image space. Therefore, these
    non-linear transformation effectively encode a transformation *from* the
    reference image *to* the (unwarped) source image.
    """


    def __init__(self,
                 image,
                 src,
                 ref,
                 srcSpace=None,
                 refSpace=None,
                 **kwargs):
        """Create a ``NonLinearTransform``. See the :meth:`.Nifti.getAffine`
        method for an overview of the values that ``srcSpace`` and ``refSpace``
        may take.

        :arg image:       A string containing the name of an image file to
                          load, or a :mod:`numpy` array, or a :mod:`nibabel`
                          image object.

        :arg src:         :class:`.Nifti` representing the source image.

        :arg ref:         :class:`.Nifti` representing the reference image.

        :arg srcSpace:    Coordinate system in the source image that this
                          ``NonLinearTransform`` maps to. Defaults to
                          ``'fsl'``.

        :arg refSpace:    Coordinate system in the reference image that this
                          ``NonLinearTransform`` maps from. Defaults to
                          ``'fsl'``.

        All other arguments are passed through to :meth:`.Image.__init__`.
        """

        # TODO Could make more general by replacing
        # srcSpace and refSpace with src/ref affines,
        # which transform tofrom (e.g.) source/ref
        # voxels to/from the space required by the
        # deformation field

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

        See the :meth:`.Nifti.getAffine` method for an overview of the values
        that ``from_`` and ``to`` may take.

        :arg coords: A sequence of XYZ coordinates, or ``numpy`` array of shape
                     ``(n, 3)`` containing ``n`` sets of coordinates in the
                     reference space.

        :arg from_:  Reference image space that ``coords`` are defined in

        :arg to:     Source image space to transform ``coords`` into

        :returns:    The corresponding coordinates in the source image space.
        """
        raise NotImplementedError()


class DeformationField(NonLinearTransform):
    """Class which represents a deformation (a.k.a. warp) field which, at each
    voxel, contains either:

      - a relative displacement from the reference image space to the source
        image space, or
      - absolute coordinates in the source space


    It is assumed that the a ``DeformationField`` is aligned with the
    reference image in their world coordinate systems (i.e. their ``sform``
    affines project the reference image and the deformation field into
    alignment).
    """


    def __init__(self, image, src, ref=None, **kwargs):
        """Create a ``DisplacementField``.

        :arg ref:     Optional. If not provided, it is assumed that the
                      reference is defined in the same space as ``image``.

        :arg defType: Either ``'absolute'`` or ``'relative'``, indicating
                      the type of this displacement field. If not provided,
                      will be inferred via the :func:`detectDeformationType`
                      function.

        All other arguments are passed through to
        :meth:`NonLinearTransform.__init__`.
        """

        if ref is None:
            ref = self

        defType = kwargs.pop('defType', None)

        if defType not in (None, 'relative', 'absolute'):
            raise ValueError('Invalid value for defType: {}'.format(defType))

        NonLinearTransform.__init__(self, image, src, ref, **kwargs)

        self.__defType = defType


    @property
    def deformationType(self):
        """The type of this ``DeformationField`` - ``'absolute'`` or
        ``'relative'``.
        """
        if self.__defType is None:
            self.__defType = detectDeformationType(self)
        return self.__defType


    @property
    def absolute(self):
        """``True`` if this ``DeformationField`` contains absolute
        coordinates.
        """
        return self.deformationType == 'absolute'


    @property
    def relative(self):
        """``True`` if this ``DeformationField`` contains relative
        displacements.
        """
        return self.deformationType == 'relative'


    def transform(self, coords, from_=None, to=None):
        """Transform the given XYZ coordinates from the reference image space
        to the source image space.

        :arg coords: A sequence of XYZ coordinates, or ``numpy`` array of shape
                     ``(n, 3)`` containing ``n`` sets of coordinates in the
                     reference space.

        :arg from_:  Reference image space that ``coords`` are defined in

        :arg to:     Source image space to transform ``coords`` into

        :returns:    ``coords``, transformed into the source image space
        """

        if from_ is None: from_ = self.refSpace
        if to    is None: to    = self.srcSpace

        coords   = np.asanyarray(coords)
        outshape = coords.shape
        coords   = coords.reshape((-1, 3))

        # We may need to pre-transform the
        # coordinates so they are in the
        # same reference image space as the
        # displacements
        if from_ != self.refSpace:
            xform  = self.ref.getAffine(from_, self.refSpace)
            coords = affine.transform(coords, xform)

        # We also need to get the coordinates
        # in field voxels, so we can look up
        # the displacements/coordinates. We
        # can get this through the assumption
        # that field and ref are aligned in
        # the world coordinate system
        xform = affine.concat(self    .getAffine('world',       'voxel'),
                              self.ref.getAffine(self.refSpace, 'world'))

        if np.all(np.isclose(xform, np.eye(4))):
            voxels = coords
        else:
            voxels = affine.transform(coords, xform)

        # Mask out the coordinates
        # that are out of bounds of
        # the deformation field
        voxels  = np.round(voxels).astype(np.int)
        voxmask = (voxels >= [0, 0, 0]) & (voxels < self.shape[:3])
        voxmask = voxmask.all(axis=1)
        voxels  = voxels[voxmask]

        xs, ys, zs = voxels.T

        if self.absolute: disps = self.data[xs, ys, zs, :]
        else:             disps = self.data[xs, ys, zs, :] + coords[voxmask]

        # Make sure the coordinates are in
        # the requested source image space
        if to != self.srcSpace:
            xform = self.src.getAffine(self.srcSpace, to)
            disps = affine.transform(disps, xform)

        # Nans for input coordinates which
        # were outside of the field
        outcoords          = np.full(coords.shape, np.nan)
        outcoords[voxmask] = disps

        return outcoords.reshape(outshape)


class CoefficientField(NonLinearTransform):
    """Class which represents a B-spline coefficient field generated by FNIRT.

    The :meth:`displacements` method can be used to calculate relative
    displacements for a set of reference space voxel coordinates.


    A FNIRT nonlinear transformation often contains a *premat*, a global
    affine transformation from the source space to the reference space, which
    was calculated with FLIRT, and used as the starting point for the
    non-linear optimisation performed by FNIRT.


    This affine may be provided when creating a ``CoefficientField`` as the
    ``srcToRefMat`` argument to :meth:`__init__`, and is subsequently accessed
    via the :meth:`srcToRefMat` attribute.
    """


    def __init__(self,
                 image,
                 src,
                 ref,
                 srcSpace=None,
                 refSpace=None,
                 fieldType='cubic',
                 knotSpacing=None,
                 fieldToRefMat=None,
                 srcToRefMat=None,
                 **kwargs):
        """Create a ``CoefficientField``.

        :arg fieldType:     Must currently be ``'cubic'``

        :arg knotSpacing:   A tuple containing the spline knot spacings along
                            each axis.

        :arg fieldToRefMat: Affine transformation which can transform reference
                            image voxel coordinates into coefficient field
                            voxel coordinates.

        :arg srcToRefMat:   Optional initial global affine transformation from
                            the source image to the reference image. This is
                            assumed to be a FLIRT-style matrix, i.e. it
                            transforms from source image ``srcSpace``
                            coordinates into reference image ``refSpace``
                            coordinates (typically ``'fsl'`` coordinates, i.e.
                            scaled voxels potentially with a left-right flip).

        See the :class:`NonLinearTransform` class for details on the other
        arguments.
        """

        if fieldType not in ('cubic',):
            raise ValueError('Unsupported field type: {}'.format(fieldType))

        if srcToRefMat   is not None: srcToRefMat   = np.copy(srcToRefMat)
        if fieldToRefMat is     None: fieldToRefMat = np.eye(4)

        NonLinearTransform.__init__(self,
                                    image,
                                    src,
                                    ref,
                                    srcSpace,
                                    refSpace,
                                    **kwargs)

        self.__fieldType     = fieldType
        self.__knotSpacing   = tuple(knotSpacing)
        self.__refToSrcMat   = None
        self.__srcToRefMat   = srcToRefMat
        self.__fieldToRefMat = np.copy(fieldToRefMat)
        self.__refToFieldMat = affine.invert(self.__fieldToRefMat)

        if srcToRefMat is not None:
            self.__refToSrcMat = affine.invert(srcToRefMat)


    @property
    def fieldType(self):
        """Return the type of the coefficient field, currently always
        ``'cubic'``.
        """
        return self.__fieldType


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


    @property
    def srcToRefMat(self):
        """Return the initial source-to-reference affine, or ``None`` if
        there isn't one.
        """
        return self.__srcToRefMat


    @property
    def refToSrcMat(self):
        """Return the inverse of the initial source-to-reference affine, or
        ``None`` if there isn't one.
        """
        return self.__refToSrcMat


    @memoize.Instanceify(memoize.memoize)
    def asDeformationField(self, defType='relative', premat=True):
        """Convert this ``CoefficientField`` to a :class:`DeformationField`.

        This method is a wrapper around
        :func:`coefficientFieldToDeformationField`
        """
        return coefficientFieldToDeformationField(self, defType, premat)


    def transform(self, coords, from_=None, to=None, premat=True):
        """Overrides :meth:`NonLinearTransform.transform`. Transforms the
        given ``coords`` from the reference image space into the source image
        space.

        :arg coords: A sequence of XYZ coordinates, or ``numpy`` array of shape
                     ``(n, 3)`` containing ``n`` sets of coordinates in the
                     reference space.

        :arg from_:  Reference image space that ``coords`` are defined in

        :arg to:     Source image space to transform ``coords`` into

        :arg premat: If ``True``, the inverse :meth:`srcToRefMat` is applied
                     to the coordinates after the displacements have been
                     added.

        :returns:    ``coords``, transformed into the source image space
        """
        df = self.asDeformationField(premat=premat)
        return df.transform(coords, from_, to)


    def displacements(self, coords):
        """Calculate the relative displacements for the given coordinates.

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

        # Convert the given voxel coordinates
        # into the corresponding coefficient
        # field voxel coordinates
        i, j, k = affine.transform(coords, self.refToFieldMat).T

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


def detectDeformationType(field):
    """Attempt to automatically determine whether a deformation field is
    specified in absolute or relative coordinates.

    :arg field: A :class:`DeformationField`

    :returns:   ``'absolute'`` if it looks like ``field`` contains absolute
                coordinates, ``'relative'`` otherwise.
    """

    # This test is based on the assumption
    # that a deformation field containing
    # absolute coordinates will have a
    # greater standard deviation than one
    # which contains relative coordinates.
    absdata = field[:]
    reldata = convertDeformationType(field, 'relative')
    stdabs  = absdata.std(axis=(0, 1, 2)).sum()
    stdrel  = reldata.std(axis=(0, 1, 2)).sum()

    if stdabs > stdrel: return 'absolute'
    else:               return 'relative'


def convertDeformationType(field, defType=None):
    """Convert a deformation field between storing absolute coordinates or
    relative displacements.

    :arg field:   A :class:`DeformationField` instance
    :arg defType: Either ``'absolute'`` or ``'relative'``. If not provided,
                  the opposite type to ``field.deformationType`` is used.
    :returns:     A ``numpy.array`` containing the adjusted deformation field.
    """

    if defType is None:
        if field.deformationType == 'absolute': defType = 'relative'
        else:                                   defType = 'absolute'

    if defType not in ('absolute', 'relative'):
        raise ValueError('defType must be "absolute" or "relative" '
                         '("{}" passed)'.format(defType))

    # Regardless of the conversion direction,
    # we need the coordinates of every voxel
    # in the reference coordinate system.
    dx, dy, dz = field.shape[:3]
    xform      = affine.concat(field.ref.getAffine('world', field.refSpace),
                               field    .getAffine('voxel', 'world'))

    coords     = np.meshgrid(np.arange(dx),
                             np.arange(dy),
                             np.arange(dz), indexing='ij')
    coords     = np.array(coords).transpose((1, 2, 3, 0))
    coords     = affine.transform(coords.reshape((-1, 3)), xform)
    coords     = coords.reshape((dx, dy, dz, 3))

    # If converting from relative to absolute,
    # we just add the coordinates to (what is
    # assumed to be) the relative shift. Or,
    # to convert from absolute to relative,
    # we subtract the reference image voxels.
    if defType == 'absolute': return field.data + coords
    else:                     return field.data - coords


def convertDeformationSpace(field, from_, to):
    """Adjust the source and/or reference spaces of the given deformation
    field. See the :meth:`.Nifti.getAffine` method for the valid values for
    the ``from_`` and ``to`` arguments.

    :arg field: A :class:`DeformationField` instance
    :arg from_: New reference image coordinate system
    :arg to:    New source image coordinate system

    :returns:   A new :class:`DeformationField` which transforms between
                the reference ``from_`` coordinate system and the source ``to``
                coordinate system.
    """

    if field.srcSpace == to and field.refSpace == from_:
        return field

    # Get the field in absolute coordinates
    # if necessary - these are our source
    # coordinates in the original "to" space.
    fieldcoords = field.data
    if field.relative: srccoords = convertDeformationType(field)
    else:              srccoords = fieldcoords

    srccoords = srccoords.reshape((-1, 3))

    # Now transform those source coordinates
    # from the original source space to the
    # source space specified by "to"
    if to != field.srcSpace:

        srcmat    = field.src.getAffine(field.srcSpace, to)
        srccoords = affine.transform(srccoords, srcmat)

    # If we have been asked to return
    # absolute coordinates, the
    # reference "from_" coordinate
    # system is irrelevant - we're done.
    if field.absolute:
        fieldcoords = srccoords

    # Otherwise our deformation field
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

        xform = affine.concat(
            field.ref.getAffine('world', from_),
            field    .getAffine('voxel', 'world'))

        if not np.all(np.isclose(xform, np.eye(4))):
            refcoords = affine.transform(refcoords, xform)

        fieldcoords = srccoords - refcoords

    return DeformationField(
        fieldcoords.reshape(field.shape),
        header=field.header,
        src=field.src,
        ref=field.ref,
        srcSpace=to,
        refSpace=from_,
        defType=field.deformationType)


def applyDeformation(image,
                     field,
                     ref=None,
                     order=1,
                     mode=None,
                     cval=None,
                     premat=None):
    """Applies a :class:`DeformationField` to an :class:`.Image`.

    The image is transformed into the space of the field's reference image
    space. See the ``scipy.ndimage.interpolation.map_coordinates`` function
    for details on the ``order``, ``mode`` and ``cval`` options.

    If an alternate reference image is provided via the ``ref`` argument,
    the deformation field is resampled into its space, and then applied to
    the input image. It is therefore assumed that an alternate ``ref`` is
    aligned in world coordinates with the field's actual reference image.

    :arg image:  :class:`.Image` to be transformed

    :arg field:  :class:`DeformationField` to use

    :arg ref:    Alternate reference image - if not provided, ``field.ref``
                 is used

    :arg order:  Spline interpolation order, passed through to the
                 ``scipy.ndimage.affine_transform`` function - ``0``
                 corresponds to nearest neighbour interpolation, ``1``
                 (the default) to linear interpolation, and ``3`` to
                 cubic interpolation.

    :arg mode:   How to handle regions which are outside of the image FOV.
                 Defaults to `''nearest'``.

    :arg cval:   Constant value to use when ``mode='constant'``.

    :arg premat: Optional affine transform which can be used if ``image`` is
                 not in the same space as ``field.src``. Assumed to transform
                 from ``image`` **voxel** coordinates into ``field.src``
                 **voxel** coordinates.

    :return:     ``numpy.array`` containing the transformed image data.
    """

    if order is None: order = 1
    if mode  is None: mode  = 'nearest'
    if cval  is None: cval  = 0
    if ref   is None: ref   = field.ref

    # We need the field to contain
    # absolute source image voxel
    # coordinates
    field = convertDeformationSpace(field, 'voxel', 'voxel')
    if field.deformationType != 'absolute':
        field = DeformationField(convertDeformationType(field, 'absolute'),
                                 header=field.header,
                                 src=field.src,
                                 ref=field.ref,
                                 srcSpace='voxel',
                                 refSpace='voxel',
                                 defType='absolute')

    # If the field is not voxel-aligned
    # to the reference, we need to
    # resample the field itself into the
    # reference image space (assumed to
    # be world-aligned). If field and ref
    # are not not world  aligned, regions
    # of the field outside of the
    # reference image space will contain
    # -1s, so will be detected as out of
    # bounds by map_coordinates below.
    #
    # This will potentially result in
    # truncation at the field boundaries,
    # but there's nothing we can do about
    # that.
    src = field.src

    if not field.sameSpace(ref):
        field = resample.resampleToReference(field,
                                             ref,
                                             order=order,
                                             mode='constant',
                                             cval=-1)[0]
    else:
        field = field.data

    # If the input image is in a
    # different space to the field
    # source space, we need to
    # adjust the resampling matrix.
    # We assume world-world alignment
    # between the original source
    # and the image to be resampled
    if (premat is not None) or (not image.sameSpace(src)):
        if premat is None:
            premat = affine.concat(image.getAffine('world', 'voxel'),
                                   src  .getAffine('voxel', 'world'))
        else:
            premat = affine.invert(premat)
        shape = field.shape
        field = field.reshape((-1, 3))
        field = affine.transform(field, premat)
        field = field.reshape(shape)

    field = field.transpose((3, 0, 1, 2))
    return ndinterp.map_coordinates(image.data,
                                    field,
                                    order=order,
                                    mode=mode,
                                    cval=cval)


def coefficientFieldToDeformationField(field, defType='relative', premat=True):
    """Convert a :class:`CoefficientField` into a :class:`DeformationField`.

    :arg field:   :class:`CoefficientField` to convert

    :arg defType: The type of deformation field - either ``'relative'`` (the
                  default) or ``'absolute'``.

    :arg premat:  If ``True`` (the default), the :meth:`srcToRefMat` is
                  encoded into the deformation field.

    :return:      :class:`DeformationField` calculated from ``field``.
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
    rdfield = DeformationField(disps,
                               header=field.ref.header,
                               src=field.src,
                               ref=field.ref,
                               srcSpace=field.srcSpace,
                               refSpace=field.refSpace,
                               defType='relative')

    if (defType == 'relative') and (not premat):
        return rdfield

    # Convert to absolute - the
    # deformations will now be
    # absolute coordinates in
    # aligned-src space
    disps = convertDeformationType(rdfield)

    # Apply the premat if requested -
    # this will transform the coordinates
    # from aligned-src to orig-src space.
    if premat and field.srcToRefMat is not None:

        # We apply the premat in the same way
        # that fnirtfileutils does - applying
        # the inverse affine to every ref space
        # voxel coordinate, then adding it to
        # the existing displacements.
        shape  = disps.shape
        disps  = disps.reshape(-1, 3)
        premat = affine.concat(field.refToSrcMat - np.eye(4),
                               field.ref.getAffine('voxel', 'fsl'))
        disps  = disps + affine.transform(xyz, premat)
        disps  = disps.reshape(shape)

        # note that convertwarp applies a premat
        # differently - its method is equivalent
        # to directly transforming the existing
        # absolute displacements, i.e.:
        #
        #   disps = affine.transform(disps, refToSrc)

    adfield = DeformationField(disps,
                               header=field.ref.header,
                               src=field.src,
                               ref=field.ref,
                               srcSpace=field.srcSpace,
                               refSpace=field.refSpace,
                               defType='absolute')

    # Not either return absolute displacements,
    # or convert back to relative displacements
    if defType == 'absolute':
        return adfield
    else:
        return DeformationField(convertDeformationType(adfield),
                                src=field.src,
                                ref=field.ref,
                                srcSpace=field.srcSpace,
                                refSpace=field.refSpace,
                                header=field.ref.header,
                                defType='relative')
