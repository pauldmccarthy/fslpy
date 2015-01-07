#!/usr/bin/env python
#
# constants.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

# Constants which represent the orientation
# of an axis, in either voxel or world space.
ORIENT_UNKNOWN = -1
ORIENT_L2R     = 0
ORIENT_R2L     = 1
ORIENT_P2A     = 2
ORIENT_A2P     = 3
ORIENT_I2S     = 4
ORIENT_S2I     = 5


# Constants from the NIFTI1 specification that define
# the 'space' in which an image is assumed to be.
NIFTI_XFORM_UNKNOWN      = 0
NIFTI_XFORM_SCANNER_ANAT = 1
NIFTI_XFORM_ALIGNED_ANAT = 2
NIFTI_XFORM_TALAIRACH    = 3
NIFTI_XFORM_MNI_152      = 4
