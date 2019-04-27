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
   writeFnirt
"""


import logging

import fsl.data.constants as constants


log = logging.getLogger(__name__)


def readFnirt(fname, src, ref, dispType=None):
    """
    """

    # Figure out whether the file
    # is a displacement field or
    # a coefficient field
    import fsl.data.image     as fslimage
    from   .              import nonlinear

    img = fslimage.Image(fname, loadData=False)

    dispfields = (constants.FSL_FNIRT_DISPLACEMENT_FIELD,
                  constants.FSL_TOPUP_FIELD)
    coeffields = (constants.FSL_CUBIC_SPLINE_COEFFICIENTS,
                  constants.FSL_DCT_COEFFICIENTS,
                  constants.FSL_QUADRATIC_SPLINE_COEFFICIENTS,
                  constants.FSL_TOPUP_CUBIC_SPLINE_COEFFICIENTS,
                  constants.FSL_TOPUP_QUADRATIC_SPLINE_COEFFICIENTS)

    kwargs = {
        'src'      : src,
        'ref'      : ref,
        'srcSpace' : 'fsl',
        'refSpace' : 'fsl',
        'dispType' : None,
    }

    if img.intent in dispfields:
        return nonlinear.DisplacementField(fname, **kwargs)

    elif img.intent in coeffields:
        pass  # return nonlinear.CoefficientField(fname, **kwargs)

    else:
        raise ValueError('Cannot determine type of nonlinear '
                         'file {}'.format(fname))


def writeFnirt(field, fname):
    """
    """
    field.save(fname)


def toFnirt(field):
    pass


def fromFnirt(field, from_='voxel', to='world'):
    """
    """

    from . import nonlinear

    return nonlinear.convertDisplacementSpace(field, from_=from_, to=to)
