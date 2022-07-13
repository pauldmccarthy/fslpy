#!/usr/bin/env python
#
# standard_space_roi.py - Wrapper for the standard_space_roi command.
#
# Author: Fidel Alfaro Almagro
#
"""This module provides the :func:`standard_space_roi` function, a wrapper for
the FSL `standard_space_roi`_ command.
"""

import fsl.utils.assertions as asrt
from . import wrapperutils  as wutils

@wutils.fileOrImage('input', 'output', 'maskMASK', 'roiMASK', 'ssref', 'altinput')
@wutils.fslwrapper
def standard_space_roi(input, output, **kwargs):
    """Wrapper for the ``standard_space_roi`` command.

    :arg maskFOV:   Mask output using transformed standard space FOV (default)
    :arg maskMASK:  Mask output using transformed standard space mask
    :arg maskNONE:  Do not mask output

    :arg roiFOV:    Cut down input FOV using bounding box of the transformed standard space FOV (default)
    :arg roiMASK:   Cut down input FOV using nonbackground bounding box of the transformed standard space mask
    :arg roiNONE:   Co not cut down input FOV

    :arg ssref      Standard space reference image to use (default $FSLDIR/data/standard/MNI152_T1)
    :arg altinput   Alternative input image to apply the ROI to (instead of the one used to register to the reference)
    :arg d          Debug (don't delete intermediate files)
    :arg b          Betpremask, equivalent to: -maskMASK $FSLDIR/data/standard/MNI152_T1_2mm_brain_mask_dil -roiNONE

    Refer to the ``standard_space_roi`` command-line help for details on all arguments.
    """
    asrt.assertIsNifti(input)

    argmap = {
        'twod' : '2D'
    }

    valmap = {
        'maskFOV'      : wutils.SHOW_IF_TRUE,
        'maskNONE'     : wutils.SHOW_IF_TRUE,
        'roiFOV'       : wutils.SHOW_IF_TRUE,
        'roiNONE'      : wutils.SHOW_IF_TRUE,
        'd'            : wutils.SHOW_IF_TRUE,
        'b'            : wutils.SHOW_IF_TRUE,
        'usesqform'    : wutils.SHOW_IF_TRUE,
        'displayinit'  : wutils.SHOW_IF_TRUE,
        'noresample'   : wutils.SHOW_IF_TRUE,
        'forcescaling' : wutils.SHOW_IF_TRUE,
        'applyxfm'     : wutils.SHOW_IF_TRUE,
        'nosearch'     : wutils.SHOW_IF_TRUE,
        'noclamp'      : wutils.SHOW_IF_TRUE,
        'noresampblur' : wutils.SHOW_IF_TRUE,
        '2D'           : wutils.SHOW_IF_TRUE,
        'v'            : wutils.SHOW_IF_TRUE
    }

    cmd  = ['standard_space_roi', input, output]
    cmd += wutils.applyArgStyle('-', argmap=argmap, valmap=valmap, **kwargs)

    return cmd
