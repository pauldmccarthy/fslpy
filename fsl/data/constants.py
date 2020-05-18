#!/usr/bin/env python
#
# constants.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines some constant values used throughout ``fslpy``.


The following constants relate to the orientation of an axis, in either
voxel or world space:

.. autosummary::
   ORIENT_L2R
   ORIENT_R2L
   ORIENT_P2A
   ORIENT_A2P
   ORIENT_I2S
   ORIENT_S2I
   ORIENT_UNKNOWN


These constants relate to the *space* in which a NIFTI image is assumed to be
(i.e. the transformed coordinate space); they are defined in the NIFTI
specification:

.. autosummary::
   NIFTI_XFORM_UNKNOWN
   NIFTI_XFORM_SCANNER_ANAT
   NIFTI_XFORM_ALIGNED_ANAT
   NIFTI_XFORM_TALAIRACH
   NIFTI_XFORM_MNI_152
"""


ORIENT_L2R     =  0
"""The axis goes from left to right."""


ORIENT_R2L     =  1
"""The axis goes from right to left."""


ORIENT_P2A     =  2
"""The axis goes from posterior to anterior."""


ORIENT_A2P     =  3
"""The axis goes from anterior to posterior."""


ORIENT_I2S     =  4
"""The axis goes from inferior to superior."""


ORIENT_S2I     =  5
"""The axis goes from superior to inferior."""


ORIENT_UNKNOWN = -1
"""The axis has an unknown orientation."""


NIFTI_XFORM_UNKNOWN      = 0
"""Arbitrary coordinates."""


NIFTI_XFORM_SCANNER_ANAT = 1
"""Scanner-based anatomical coordinates."""


NIFTI_XFORM_ALIGNED_ANAT = 2
"""Coordinates aligned to another file's, or to anatomical "truth"."""


NIFTI_XFORM_TALAIRACH    = 3
"""Coordinates aligned to Talairach-Tournoux Atlas; (0,0,0)=AC, etc."""


NIFTI_XFORM_MNI_152      = 4
"""MNI 152 normalized coordinates."""


NIFTI_XFORM_ANALYZE      = 5
"""Code which indicates that this is an ANALYZE image, not a NIFTI image. """


# NIFTI unit codes
NIFTI_UNITS_UNKNOWN = 0
NIFTI_UNITS_METER   = 1
NIFTI_UNITS_MM      = 2
NIFTI_UNITS_MICRON  = 3
NIFTI_UNITS_SEC     = 8
NIFTI_UNITS_MSEC    = 16
NIFTI_UNITS_USEC    = 24
NIFTI_UNITS_HZ      = 32
NIFTI_UNITS_PPM     = 40
NIFTI_UNITS_RADS    = 48


# NIFTI datatype codes
NIFTI_DT_NONE          = 0
NIFTI_DT_UNKNOWN       = 0
NIFTI_DT_BINARY        = 1
NIFTI_DT_UNSIGNED_CHAR = 2
NIFTI_DT_SIGNED_SHORT  = 4
NIFTI_DT_SIGNED_INT    = 8
NIFTI_DT_FLOAT         = 16
NIFTI_DT_COMPLEX       = 32
NIFTI_DT_DOUBLE        = 64
NIFTI_DT_RGB           = 128
NIFTI_DT_ALL           = 255
NIFTI_DT_UINT8         = 2
NIFTI_DT_INT16         = 4
NIFTI_DT_INT32         = 8
NIFTI_DT_FLOAT32       = 16
NIFTI_DT_COMPLEX64     = 32
NIFTI_DT_FLOAT64       = 64
NIFTI_DT_RGB24         = 128
NIFTI_DT_INT8          = 256
NIFTI_DT_UINT16        = 512
NIFTI_DT_UINT32        = 768
NIFTI_DT_INT64         = 1024
NIFTI_DT_UINT64        = 1280
NIFTI_DT_FLOAT128      = 1536
NIFTI_DT_COMPLEX128    = 1792
NIFTI_DT_COMPLEX256    = 2048
NIFTI_DT_RGBA32        = 2304


# NIFTI file intent codes
NIFTI_INTENT_NONE          = 0
NIFTI_INTENT_CORREL        = 2
NIFTI_INTENT_TTEST         = 3
NIFTI_INTENT_FTEST         = 4
NIFTI_INTENT_ZSCORE        = 5
NIFTI_INTENT_CHISQ         = 6
NIFTI_INTENT_BETA          = 7
NIFTI_INTENT_BINOM         = 8
NIFTI_INTENT_GAMMA         = 9
NIFTI_INTENT_POISSON       = 10
NIFTI_INTENT_NORMAL        = 11
NIFTI_INTENT_FTEST_NONC    = 12
NIFTI_INTENT_CHISQ_NONC    = 13
NIFTI_INTENT_LOGISTIC      = 14
NIFTI_INTENT_LAPLACE       = 15
NIFTI_INTENT_UNIFORM       = 16
NIFTI_INTENT_TTEST_NONC    = 17
NIFTI_INTENT_WEIBULL       = 18
NIFTI_INTENT_CHI           = 19
NIFTI_INTENT_INVGAUSS      = 20
NIFTI_INTENT_EXTVAL        = 21
NIFTI_INTENT_PVAL          = 22
NIFTI_INTENT_LOGPVAL       = 23
NIFTI_INTENT_LOG10PVAL     = 24
NIFTI_FIRST_STATCODE       = 2
NIFTI_LAST_STATCODE        = 24
NIFTI_INTENT_ESTIMATE      = 1001
NIFTI_INTENT_LABEL         = 1002
NIFTI_INTENT_NEURONAME     = 1003
NIFTI_INTENT_GENMATRIX     = 1004
NIFTI_INTENT_SYMMATRIX     = 1005
NIFTI_INTENT_DISPVECT      = 1006
NIFTI_INTENT_VECTOR        = 1007
NIFTI_INTENT_POINTSET      = 1008
NIFTI_INTENT_TRIANGLE      = 1009
NIFTI_INTENT_QUATERNION    = 1010
NIFTI_INTENT_DIMLESS       = 1011
NIFTI_INTENT_TIME_SERIES   = 2001
NIFTI_INTENT_NODE_INDEX    = 2002
NIFTI_INTENT_RGB_VECTOR    = 2003
NIFTI_INTENT_RGBA_VECTOR   = 2004
NIFTI_INTENT_SHAPE         = 2005

# FSL-specific intent codes

# FNIRT
FSL_FNIRT_DISPLACEMENT_FIELD            = 2006
FSL_CUBIC_SPLINE_COEFFICIENTS           = 2007
FSL_DCT_COEFFICIENTS                    = 2008
FSL_QUADRATIC_SPLINE_COEFFICIENTS       = 2009

# TOPUP
FSL_TOPUP_CUBIC_SPLINE_COEFFICIENTS     = 2016
FSL_TOPUP_QUADRATIC_SPLINE_COEFFICIENTS = 2017
FSL_TOPUP_FIELD                         = 2018
