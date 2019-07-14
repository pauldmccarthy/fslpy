#!/usr/bin/env python
#
# fnirt.py - Functions for working with FNIRT non-linear transformations.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains functions for working with FNIRT non-linear
transformation matrices. The following functions are available:

.. autosummary::
   :nosignatures:

   readFnirt
   toFnirt
   fromFnirt
"""


import logging

import numpy   as np
import nibabel as nib

import fsl.data.constants as constants


log = logging.getLogger(__name__)


def _readFnirtDisplacementField(fname, img, src, ref, dispType=None):
    """Loads ``fname``, assumed to be a FNIRT displacement field.

    :arg fname:    File name of FNIRT displacement field
    :arg img:      ``fname`` loaded as an :class:`.Image`
    :arg src:      Source image
    :arg ref:      Reference image
    :arg dispType: Displacement type - either ``'absolute'`` or ``'relative'``.
                   If not provided, is automatically inferred from the data.
    :return:       A :class:`.DisplacementField`
    """
    from . import nonlinear
    return nonlinear.DisplacementField(fname,
                                       src,
                                       ref,
                                       srcSpace='fsl',
                                       refSpace='fsl',
                                       dispType=dispType)


def _readFnirtCoefficientField(fname, img, src, ref):
    """Loads ``fname``, assumed to be a FNIRT coefficient field.

    :arg fname: File name of FNIRT coefficient field
    :arg img:   ``fname`` loaded as an :class:`.Image`
    :arg src:   Source image
    :arg ref:   Reference image
    :return:    A :class:`.CoefficientField`
    """

    from . import affine
    from . import nonlinear

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

    return nonlinear.CoefficientField(fname,
                                      src,
                                      ref,
                                      srcSpace='fsl',
                                      refSpace='fsl',
                                      fieldType=fieldType,
                                      knotSpacing=knotSpacing,
                                      srcToRefMat=srcToRefMat,
                                      fieldToRefMat=fieldToRefMat)


def readFnirt(fname, src, ref, dispType=None):
    """Reads a non-linear FNIRT transformation image, returning
    a :class:`.DisplacementField` or :class:`.CoefficientField` depending
    on the file type.

    :arg fname:    File name of FNIRT transformation
    :arg src:      Source image
    :arg ref:      Reference image
    :arg dispType: Displacement type - either ``'absolute'`` or ``'relative'``.
                   If not provided, is automatically inferred from the data.
    """

    # Figure out whether the file
    # is a displacement field or
    # a coefficient field
    import fsl.data.image as fslimage

    img   = fslimage.Image(fname, loadData=False)
    disps = (constants.FSL_FNIRT_DISPLACEMENT_FIELD,
             constants.FSL_TOPUP_FIELD)
    coefs = (constants.FSL_CUBIC_SPLINE_COEFFICIENTS,
             constants.FSL_DCT_COEFFICIENTS,
             constants.FSL_QUADRATIC_SPLINE_COEFFICIENTS,
             constants.FSL_TOPUP_CUBIC_SPLINE_COEFFICIENTS,
             constants.FSL_TOPUP_QUADRATIC_SPLINE_COEFFICIENTS)

    if img.intent in disps:
        return _readFnirtDisplacementField(fname, img, src, ref, dispType)
    elif img.intent in coefs:
        return _readFnirtCoefficientField(fname, img, src, ref)
    else:
        raise ValueError('Cannot determine type of nonlinear '
                         'file {}'.format(fname))


def toFnirt(field):
    """Convert a :class:`.NonLinearTransform` to a FNIRT-compatible
    :class:`.DisplacementField` or:class:`.CoefficientField`.

    :arg field: :class:`.NonLinearTransform` to convert
    :return:    A FNIRT-compatible :class:`.DisplacementField` or
                :class:`.CoefficientField`.
    """

    from . import nonlinear

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
    # field, or a displacement field.
    #
    # We can't convert a CoefficientField
    # which doesn't transform in FSL
    # coordinates, because the coefficients
    # will have been calculated between some
    # other source/reference coordinate
    # systems, and we can't adjust the
    # coefficients to encode an FSL->FSL
    # deformation.
    else:

        if isinstance(field, nonlinear.CoefficientField):
            field = nonlinear.coefficientFieldToDisplacementField(field)

        # Again, if we have a displacement
        # field which transforms between
        # fsl spaces, we can just take a copy
        if field.srcSpace == 'fsl' and field.refSpace == 'fsl':
            field = nonlinear.DisplacementField(
                field.data,
                src=field.src,
                ref=field.ref,
                xform=field.voxToWorldMat,
                dispType=field.displacementType)

        # Otherwise we have to adjust the
        # displacements so they transform
        # between fsl coordinates.
        field = nonlinear.convertDisplacementSpace(
            field, from_='fsl', to='fsl')

        field.header['intent_code'] = constants.FSL_FNIRT_DISPLACEMENT_FIELD

    return field


def fromFnirt(field, from_='world', to='world'):
    """Convert a FNIRT-style :class:`.NonLinearTransform` to a generic
    :class:`.DisplacementField`.

    :arg field: A FNIRT-style :class:`.CoefficientField` or
                :class:`.DisplacementField`

    :arg from_: Desired reference image coordinate system

    :arg to:    Desired source image coordinate system

    :return:    A :class:`.DisplacementField` which contains displacements
                from the reference image ``from_`` cordinate system to the
                source image ``to`` coordinate syste.
    """
    from . import nonlinear

    # see comments in toFnirt
    if isinstance(field, nonlinear.CoefficientField):
        field = nonlinear.coefficientFieldToDisplacementField(field)

    return nonlinear.convertDisplacementSpace(field, from_=from_, to=to)
