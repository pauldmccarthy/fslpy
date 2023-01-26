#!/usr/bin/env python
#
# dtifit.py - Wrapper for dtifit.
#
# Author: Fidel Alfaro Almagro <fidel.alfaroalmagro@ndcn.ox.ac.uk>
#
"""This module provides wrapper functions for the FSL `dtifit
<https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FDT>`_ command.
"""

import fsl.utils.assertions as asrt

from . import wrapperutils  as wutils


@wutils.fileOrImage('data', 'mask', 'field', outprefix='out')
@wutils.fileOrArray('bvecs', 'bvals')
@wutils.fslwrapper
def dtifit(data, out, mask, bvecs, bvals, **kwargs):
    """Wrapper for the ``dtifit`` command."""

    valmap = {
        'w'           : wutils.SHOW_IF_TRUE,
        'wls'         : wutils.SHOW_IF_TRUE,
        'sse'         : wutils.SHOW_IF_TRUE,
        'kurt'        : wutils.SHOW_IF_TRUE,
        'kurtdir'     : wutils.SHOW_IF_TRUE,
        'littlebit'   : wutils.SHOW_IF_TRUE,
        'save_tensor' : wutils.SHOW_IF_TRUE,
        'verbose'     : wutils.SHOW_IF_TRUE,
    }

    asrt.assertFileExists(data, mask, bvecs, bvals)
    asrt.assertIsNifti(data, mask)

    cmd  = ['dtifit',
            '--data='  + data,
            '--out='   + out,
            '--mask='  + mask,
            '--bvecs=' + bvecs,
            '--bvals=' + bvals]
    cmd += wutils.applyArgStyle('--=', valmap=valmap, **kwargs)
    return cmd
