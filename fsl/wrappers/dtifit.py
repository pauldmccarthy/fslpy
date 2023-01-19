#!/usr/bin/env python
#
# dtifit.py - Wrappers for topup and dtifit.
#
# Author: Fidel Alfaro Almagro <fidel.alfaroalmagro@ndcn.ox.ac.uk>
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides wrapper functions for the FSL `dtifit
<https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/dtifit>`_ tools,.
"""

import fsl.utils.assertions as asrt
from fsl.utils.deprecated import deprecated
from . import wrapperutils  as wutils

@wutils.fileOrImage('data', 'mask', 'field')
@wutils.fileOrArray('bvecs', 'bvals')
@wutils.fslwrapper
def dtifit(data, mask, bvecs, bvals, out, **kwargs):
    """Wrapper for the ``dtifit`` command."""

    valmap = {
        'wls'                             : wutils.SHOW_IF_TRUE,
        'sse'                             : wutils.SHOW_IF_TRUE,
        'kurt'                            : wutils.SHOW_IF_TRUE,
        'kurtdir'                         : wutils.SHOW_IF_TRUE,
        'littlebit'                       : wutils.SHOW_IF_TRUE,
        'save_tensor'                     : wutils.SHOW_IF_TRUE,
        'gradnnlin'                       : wutils.SHOW_IF_TRUE,
        'verbose'                         : wutils.SHOW_IF_TRUE,
    }

    asrt.assertFileExists(data, mask, bvecs, bvals)
    asrt.assertIsNifti(data, mask)

    cmd  = ['dtifit', '--data=' + data, '--mask=' + mask, '--out=' + out]
    cmd += ['--bvecs=' + bvecs, '--bvals=' + bvals]
    cmd += wutils.applyArgStyle('--', valmap=valmap, **kwargs)
    return cmd

