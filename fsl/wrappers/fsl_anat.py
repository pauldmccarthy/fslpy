#!/usr/bin/env python
#
# fsl_anat.py - Wrapper for the FSL_ANAT command.
#
# Author: Martin Craig <martin.craig@eng.ox.ac.uk>
#
"""This module provides the :func:`fsl_anat` function, a wrapper for the FSL
`FSL_ANAT <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/fsl_anat>`_ command.
"""

import fsl.utils.assertions as asrt
from . import wrapperutils  as wutils

@wutils.fileOrImage('img', outprefix='out')
@wutils.fslwrapper
def fsl_anat(img, out='fsl_anat', **kwargs):
    """Wrapper for the ``fsl_anat`` command.

    :arg img:       Input structural image
    :arg out:       Output directory name
    """
    asrt.assertIsNifti(img)

    valmap = {
        'strongbias' : wutils.SHOW_IF_TRUE,
        'weakbias' : wutils.SHOW_IF_TRUE,
        'noreorient' : wutils.SHOW_IF_TRUE,
        'nocrop' : wutils.SHOW_IF_TRUE,
        'nobias' : wutils.SHOW_IF_TRUE,
        'noreg' : wutils.SHOW_IF_TRUE,
        'nononlinreg' : wutils.SHOW_IF_TRUE,
        'noseg' : wutils.SHOW_IF_TRUE,
        'nosubcortseg' : wutils.SHOW_IF_TRUE,
        'nosearch' : wutils.SHOW_IF_TRUE,
        'nocleanup' : wutils.SHOW_IF_TRUE,
    }

    argmap = {
    }

    img_type = kwargs.pop("img_type", "T1")
    cmd  = ['fsl_anat', '-i', img, '-o', out, '-t', img_type]
    smoothing = kwargs.pop("bias_smoothing", None)
    if smoothing is not None:
        cmd += ['-s', str(smoothing)]

    cmd += wutils.applyArgStyle('--=',
                                valmap=valmap,
                                argmap=argmap,
                                singlechar_args=True,
                                **kwargs)

    return cmd
