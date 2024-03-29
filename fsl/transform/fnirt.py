#!/usr/bin/env python
#
# fnirt.py - Functions for working with FNIRT non-linear transformations.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains functions for working with FNIRT non-linear
transformations. The following functions are available:

.. autosummary::
   :nosignatures:

   readFnirt
   toFnirt
   fromFnirt


Non-linear registration using FNIRT
-----------------------------------


FNIRT is used to calculate a non-linear registration from a source image to a
reference image. FNIRT outputs the resulting non-linear transformation as
either:

 - A deformation/warp field which contains displacements or coordinates.
 - A coefficient field which can be used to generate a warp field.


Non-linear registration using FNIRT generally follows the process depicted
here:


.. image:: images/nonlinear_registration_process.png
   :width: 80%
   :align: center


First, an initial linear registration is performed from the source image to
the reference image using FLIRT; this provides an initial global alignment
which can be used as the starting point for the non-linear registration. Next,
FNIRT is used to non-linearly register the aligned source image to the
reference image.  Importantly, both of these steps are performed using FSL
coordinates.


Note that we have three spaces, and three sets of coordinate systems, to
consider:

 1. Source image space - the source image, before initial linear registration
    to the reference image

 2. Aligned-source image space - the source image, after it has been linearly
    transformed to the reference image space

 3. Reference image space


The initial affine registration calculates a transformation between spaces 1
and 2, and the non-linear registration calculates a transformation between
spaces 2 and 3. Note that the fields-of-view for spaces 2 and 3 are
equivalent.


The non-linear transformation file generated by FNIRT will contain the initial
linear registration, with it either being encoded directly into the warps (for
a warp field), or being stored in the NIfTI header (for a coefficient field).


FNIRT warp fields
^^^^^^^^^^^^^^^^^


A FNIRT deformation field (a.k.a. warp field) is defined in the same space as
the reference image, and may contain:

 - *relative displacements*, where each voxel in the warp field contains an
   offset which can be added to the reference image coordinates for that
   voxel, in order to calculate the corresponding source image coordinates.

 - *absolute coordinates*, where each voxel in the warp field simply contains
   the source image coordinates which correspond to those reference image
   coordinates.

.. note:: FNIRT deformation field files give no indication as to whether they
          contain relative displacements or absolute coordinates, so heuristics
          must be used to infer what is stored in a a particular file. The
          :func:`.nonlinear.detectDeformationType` function can be used to
          determine whether a file contains relative displacements or absolute
          coordinates.

If an initial linear registration was used as the starting point for FNIRT,
this is encoded into the displacements/coordinates themselves, so they can be
used to transform from the reference image to the *original* source image
space.


.. image:: images/fnirt_warp_field.png
   :width: 80%
   :align: center


FNIRT coefficient fields
^^^^^^^^^^^^^^^^^^^^^^^^


A FNIRT coefficient field contains the coefficients of a set of quadratic or
cubic B-spline functions defined on a regular 3D grid overlaid on the
reference image voxel coordinate system. Each coefficient in this grid may be
referred to as a *control point* or a *knot*.


Evaluating the spline functions at a particular location in the grid will
result in a relative displacement which can be added to that location's
reference image coordinates, in order to determine the corresponding source
image coordinates.


If an initial linear registration was used as the starting point for FNIRT,
the generated displacement field will encode a transformation to *aligned*
source image coordinates, and the initial affine will be stored in the NIfTI
header of the coefficient field file.


.. image:: images/fnirt_coefficient_field.png
   :width: 80%
   :align: center
"""


import logging

import nibabel as nib
import numpy   as np

import fsl.data.constants as constants
import fsl.data.image     as fslimage
from . import                affine
from . import                nonlinear


log = logging.getLogger(__name__)


def _readFnirtDeformationField(fname, img, src, ref, defType=None):
    """Loads ``fname``, assumed to be a FNIRT deformation field.

    :arg fname:   File name of FNIRT deformation field

    :arg img:     ``fname`` loaded as an :class:`.Image`

    :arg src:     Source image

    :arg ref:     Reference image

    :arg defType: Deformation type - either ``'absolute'`` or ``'relative'``.
                  If not provided, is automatically inferred from the data.

    :return:      A :class:`.DeformationField` object
    """
    return nonlinear.DeformationField(fname,
                                      src,
                                      ref,
                                      srcSpace='fsl',
                                      refSpace='fsl',
                                      defType=defType)


def _readFnirtCoefficientField(fname, img, src, ref):
    """Loads ``fname``, assumed to be a FNIRT coefficient field.

    :arg fname: File name of FNIRT coefficient field
    :arg img:   ``fname`` loaded as an :class:`.Image`
    :arg src:   Source image
    :arg ref:   Reference image
    :return:    A :class:`.CoefficientField`
    """

    # FNIRT uses NIFTI header fields in
    # non-standard ways to store some
    # additional information about the
    # coefficient field. See
    # $FSLDIR/src/fnirt/fnirt_file_writer.cpp
    # for more details.

    # The field type (quadratic, cubic,
    # or discrete-cosine-transform) is
    # inferred from the intent. There is
    # no support in this implementation
    # for DCT fields
    cubics = (constants.FSL_CUBIC_SPLINE_COEFFICIENTS,
              constants.FSL_TOPUP_CUBIC_SPLINE_COEFFICIENTS)
    quads  = (constants.FSL_QUADRATIC_SPLINE_COEFFICIENTS,
              constants.FSL_TOPUP_QUADRATIC_SPLINE_COEFFICIENTS)

    if img.intent in cubics:
        fieldType = 'cubic'
    elif img.intent in quads:
        fieldType = 'quadratic'
    else:
        fieldType = 'cubic'
        log.warning('Unrecognised/unsupported coefficient '
                    'field type (assuming cubic b-spline): '
                    '{}'.format(img.intent))

    # Knot spacing (in voxels) is
    # stored in the pixdims
    knotSpacing = img.pixdim[:3]

    # The sform contains an initial
    # global src-to-ref affine
    # (the starting point for the
    # non-linear registration). This
    # is encoded as a flirt matrix,
    # i.e. it transforms from
    # source-scaled-voxels to
    # ref-scaled-voxels
    srcToRefMat = img.header.get_sform()

    # The fieldToRefMat affine tells
    # the CoefficientField class how
    # to transform coefficient field
    # voxel coordinates into
    # displacement field/reference
    # image voxel coordinates.
    fieldToRefMat = affine.scaleOffsetXform(knotSpacing, 0)

    # But if the provided reference has
    # different resolution to the
    # reference that was originally
    # used to generate the warp field,
    # we need to adjust the field
    # accordingly. We assume that the
    # references are aligned in the FSL
    # coordinate system, so simply apply
    # a scaling factor calculated by
    # dividing the original reference
    # pixdims by the provided reference
    # pixdims.
    refPixdims = np.array([img.header['intent_p1'],
                           img.header['intent_p2'],
                           img.header['intent_p3']])

    if not np.all(np.isclose(ref.pixdim[:3], refPixdims)):
        fieldToRefMat = affine.concat(
            affine.scaleOffsetXform(refPixdims / ref.pixdim[:3], 0),
            fieldToRefMat)

    return nonlinear.CoefficientField(fname,
                                      src,
                                      ref,
                                      srcSpace='fsl',
                                      refSpace='fsl',
                                      fieldType=fieldType,
                                      knotSpacing=knotSpacing,
                                      srcToRefMat=srcToRefMat,
                                      fieldToRefMat=fieldToRefMat)


def readFnirt(fname, src, ref, defType=None, intent=None):
    """Reads a non-linear FNIRT transformation image, returning
    a :class:`.DeformationField` or :class:`.CoefficientField` depending
    on the file type.

    :arg fname:    File name of FNIRT transformation
    :arg src:      Source image
    :arg ref:      Reference image
    :arg defType:  Deformation type - either ``'absolute'`` or ``'relative'``.
                   Only used if the file is a deformation field. If not
                   provided, is automatically inferred from the data.
    :arg intent:   NIFTI intent code of ``fname``. e.g.
                   :attr:`.constants.FSL_FNIRT_DISPLACEMENT_FIELD`. If not
                   provided, the intent is read from the image header.
    """

    if defType not in (None, 'absolute', 'relative'):
        raise ValueError('defType must be None, "absolute" or "relative" '
                         '(passed in as {})'.format(defType))

    # Figure out whether the file is a
    # deformation field or a coefficient
    # field by checking the intent code.
    # If the intent is provided, assume
    # that the caller knows the type of
    # the field.
    img    = fslimage.Image(fname)
    intent = intent or img.intent
    disps  = (constants.FSL_FNIRT_DISPLACEMENT_FIELD,
              constants.FSL_TOPUP_FIELD)
    coefs  = (constants.FSL_CUBIC_SPLINE_COEFFICIENTS,
              constants.FSL_DCT_COEFFICIENTS,
              constants.FSL_QUADRATIC_SPLINE_COEFFICIENTS,
              constants.FSL_TOPUP_CUBIC_SPLINE_COEFFICIENTS,
              constants.FSL_TOPUP_QUADRATIC_SPLINE_COEFFICIENTS)

    if intent in disps:
        return _readFnirtDeformationField(fname, img, src, ref, defType)
    elif intent in coefs:
        return _readFnirtCoefficientField(fname, img, src, ref)
    else:
        raise ValueError('Cannot determine type of nonlinear warp field '
                         '{} (intent code: {})'.format(fname, intent))


def toFnirt(field):
    """Convert a :class:`.NonLinearTransform` to a FNIRT-compatible
    :class:`.DeformationField` or :class:`.CoefficientField`.

    :arg field: :class:`.NonLinearTransform` to convert
    :return:    A FNIRT-compatible :class:`.DeformationField` or
                :class:`.CoefficientField`.
    """

    # If we have a coefficient field
    # which transforms between fsl
    # space, we can just create a copy.
    if isinstance(field, nonlinear.CoefficientField) and \
       (field.srcSpace == 'fsl' and field.refSpace == 'fsl'):

        # We start with a nibabel image,
        # as we need to mess with the header
        # fields to store all of the FNIRT
        # coefficient field information
        fieldBase = nib.nifti1.Nifti1Image(field.data, None)

        # Set the intent
        if field.fieldType == 'cubic':
            intent = constants.FSL_CUBIC_SPLINE_COEFFICIENTS
        elif field.fieldType == 'quadratic':
            intent = constants.FSL_QUADRATIC_SPLINE_COEFFICIENTS
        fieldBase.header['intent_code'] = intent

        # Reference image pixdims are
        # stored in the intent code
        # parameters.
        fieldBase.header['intent_p1'] = field.ref.pixdim[0]
        fieldBase.header['intent_p2'] = field.ref.pixdim[1]
        fieldBase.header['intent_p3'] = field.ref.pixdim[2]

        # Pixdims are used to
        # store the knot spacing,
        pixdims      = list(field.knotSpacing) + [1]
        qform        = np.diag(pixdims)

        # The sform is used to store the
        # initial src-to-ref affine
        if field.srcToRefMat is not None: sform = field.srcToRefMat
        else:                             sform = np.eye(4)

        # The qform offsets are
        # used to store the
        # reference image shape
        qform[:3, 3] = field.ref.shape[:3]

        fieldBase.header.set_zooms(pixdims)
        fieldBase.set_sform(sform, 1)
        fieldBase.set_qform(qform, 1)
        fieldBase.update_header()

        field = nonlinear.CoefficientField(
            fieldBase,
            src=field.src,
            ref=field.ref,
            srcSpace='fsl',
            refSpace='fsl',
            fieldType=field.fieldType,
            knotSpacing=field.knotSpacing,
            fieldToRefMat=field.fieldToRefMat,
            srcToRefMat=field.srcToRefMat)

    # Otherwise we have a non-FSL coefficient
    # field, or a deformation field.
    else:

        # We can't convert a CoefficientField
        # which doesn't transform in FSL
        # coordinates, because the coefficients
        # will have been calculated between some
        # other source/reference coordinate
        # systems, and we can't adjust the
        # coefficients to encode an FSL->FSL
        # deformation.
        if isinstance(field, nonlinear.CoefficientField):
            field = nonlinear.coefficientFieldToDeformationField(field)

        # Again, if we have a displacement
        # field which transforms between
        # fsl spaces, we can just take a copy
        if field.srcSpace == 'fsl' and field.refSpace == 'fsl':
            field = nonlinear.DeformationField(
                field.data,
                header=field.header,
                src=field.src,
                ref=field.ref,
                defType=field.deformationType)

        # Otherwise we have to adjust the
        # displacements so they transform
        # between fsl coordinates.
        field = nonlinear.convertDeformationSpace(
            field, from_='fsl', to='fsl')

        field.header['intent_code'] = constants.FSL_FNIRT_DISPLACEMENT_FIELD

    return field


def fromFnirt(field, from_='world', to='world'):
    """Convert a FNIRT-style :class:`.NonLinearTransform` to a generic
    :class:`.DeformationField`.

    :arg field: A FNIRT-style :class:`.CoefficientField` or
                :class:`.DeformationField`

    :arg from_: Desired reference image coordinate system

    :arg to:    Desired source image coordinate system

    :return:    A :class:`.DeformationField` which contains displacements
                from the reference image ``from_`` cordinate system to the
                source image ``to`` coordinate syste.
    """
    if isinstance(field, nonlinear.CoefficientField):
        field = nonlinear.coefficientFieldToDeformationField(field)
    return nonlinear.convertDeformationSpace(field, from_=from_, to=to)
