#!/usr/bin/env python
#
# eddy.py - Wrappers for topup and eddy.
#
# Author: Sean Fitzgibbon <sean.fitzgibbon@ndcn.ox.ac.uk>
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
# Author: Martin Craig <martin.craig@eng.ox.a.uk>
#
"""This module provides wrapper functions for the FSL `TOPUP
<https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/topup>`_ and `EDDY
<https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/eddy>`_ tools, for field map
estimation and eddy-current distortion correction.

.. autosummary::
   :nosignatures:

   eddy_cuda
   topup
   applytopup
"""


import fsl.utils.assertions as asrt
from . import wrapperutils  as wutils


@wutils.fileOrImage('imain', 'mask', 'field')
@wutils.fileOrArray('index', 'acqp', 'bvecs', 'bvals', 'field_mat')
@wutils.fslwrapper
def eddy_cuda(imain, mask, index, acqp, bvecs, bvals, out, **kwargs):
    """Wrapper for the ``eddy_cuda`` command."""

    valmap = {
        'fep'                             : wutils.SHOW_IF_TRUE,
        'initrand'                        : wutils.SHOW_IF_TRUE,
        'repol'                           : wutils.SHOW_IF_TRUE,
        'ol_pos'                          : wutils.SHOW_IF_TRUE,
        'ol_sqr'                          : wutils.SHOW_IF_TRUE,
        'dont_sep_offs_move'              : wutils.SHOW_IF_TRUE,
        'dont_peas'                       : wutils.SHOW_IF_TRUE,
        'data_is_shelled'                 : wutils.SHOW_IF_TRUE,
        'b0_only'                         : wutils.SHOW_IF_TRUE,
        'dont_mask_output'                : wutils.SHOW_IF_TRUE,
        'cnr_maps'                        : wutils.SHOW_IF_TRUE,
        'residuals'                       : wutils.SHOW_IF_TRUE,
        'estimate_move_by_susceptibility' : wutils.SHOW_IF_TRUE,
        'verbose'                         : wutils.SHOW_IF_TRUE,
        'very_verbose'                    : wutils.SHOW_IF_TRUE,
    }

    asrt.assertFileExists(imain, mask, index, acqp, bvecs, bvals)
    asrt.assertIsNifti(imain, mask)

    kwargs.update({'imain' : imain,
                   'mask'  : mask,
                   'index' : index,
                   'acqp'  : acqp,
                   'bvecs' : bvecs,
                   'bvals' : bvals,
                   'out'   : out})

    cmd = ['eddy_cuda'] + wutils.applyArgStyle('--=', valmap=valmap, **kwargs)
    return cmd


@wutils.fileOrImage('imain', 'fout', 'iout', outprefix='out')
@wutils.fileOrArray('datain', outprefix='out')
@wutils.fslwrapper
def topup(imain, datain, **kwargs):
    """Wrapper for the ``topup`` command."""

    valmap = {
        'verbose' : wutils.SHOW_IF_TRUE
    }

    asrt.assertFileExists(datain)
    asrt.assertIsNifti(imain)

    cmd  = ['topup', '--imain={}'.format(imain), '--datain={}'.format(datain)]
    cmd += wutils.applyArgStyle('--=', valmap=valmap, **kwargs)

    return cmd

@wutils.fileOrImage('imain', 'out')
@wutils.fileOrArray('datain')
@wutils.fslwrapper
def applytopup(imain, datain, index, **kwargs):
    """Wrapper for the ``applytopup`` command."""

    valmap = {
        'verbose' : wutils.SHOW_IF_TRUE
    }

    asrt.assertFileExists(datain)
    asrt.assertIsNifti(imain)

    cmd  = [
        'applytopup', '--imain={}'.format(imain),
        '--inindex={}'.format(index),
        '--datain={}'.format(datain),
    ]
    cmd += wutils.applyArgStyle('--=', valmap=valmap, **kwargs)

    return cmd
