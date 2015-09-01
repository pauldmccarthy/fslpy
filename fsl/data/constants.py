#!/usr/bin/env python
#
# constants.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines some constant values used throughout ``fsleyes``.


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


These constants relate to the *space* in which a NIFTI1 image is assumed to be
(i.e. the transformed coordinate space); they are defined in the NIFTI1
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
