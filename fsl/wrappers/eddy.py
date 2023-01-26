#!/usr/bin/env python
#
# eddy.py - Wrappers for topup and eddy.
#
# Author: Sean Fitzgibbon <sean.fitzgibbon@ndcn.ox.ac.uk>
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
# Author: Martin Craig <martin.craig@eng.ox.a.uk>
# Author: Michiel Cottaar <michiel.cottaar@ndcn.ox.ac.uk>
# Author: Fidel Alfaro Almagro <fidel.alfaroalmagro@ndcn.ox.ac.uk>
#
"""This module provides wrapper functions for the FSL `TOPUP
<https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/topup>`_ and `EDDY
<https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/eddy>`_ tools, for field map
estimation and eddy-current distortion correction.

.. autosummary::
   :nosignatures:

   eddy
   eddy_cuda
   topup
   applytopup
"""


import fsl.utils.assertions as asrt
from fsl.utils.deprecated import deprecated
from . import wrapperutils  as wutils


@wutils.fileOrImage('imain', 'mask', 'field')
@wutils.fileOrArray('index', 'acqp', 'bvecs', 'bvals', 'field_mat')
@wutils.fslwrapper
def eddy(imain, mask, index, acqp, bvecs, bvals, out, **kwargs):
    """Wrapper for the ``eddy`` command."""

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
        'sep_offs_move'                   : wutils.SHOW_IF_TRUE,
        'rms'                             : wutils.SHOW_IF_TRUE,
    }

    asrt.assertFileExists(imain, mask, index, acqp, bvecs, bvals)
    asrt.assertIsNifti(imain, mask)

    cmd = ['eddy',
           f'--imain={imain}',
           f'--mask={mask}',
           f'--index={index}',
           f'--acqp={acqp}',
           f'--bvecs={bvecs}',
           f'--bvals={bvals}',
           f'--out={out}']
    cmd += wutils.applyArgStyle('--=', valmap=valmap, **kwargs)
    return cmd


@deprecated('3.10', '4.0',
            'eddy_cuda has been deprecated in favour of eddy, '
            'which will call the appropriate GPU or CPU version '
            'of eddy automatically.')
def eddy_cuda(*args, **kwargs):
    eddy(*args, **kwargs)


@wutils.fileOrImage('imain', 'fout', 'iout', outprefix='out')
@wutils.fileOrArray('datain', outprefix='out')
@wutils.fslwrapper
def topup(imain, datain, **kwargs):
    """Wrapper for the ``topup`` command. """

    valmap = {
        'v'       : wutils.SHOW_IF_TRUE,
        'verbose' : wutils.SHOW_IF_TRUE
    }

    asrt.assertFileExists(datain)
    asrt.assertIsNifti(imain)

    cmd  = ['topup', '--imain={}'.format(imain), '--datain={}'.format(datain)]
    cmd += wutils.applyArgStyle('--=', valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrImage('imain', outprefix='out')
@wutils.fileOrArray('datain')
@wutils.fslwrapper
def applytopup(imain, datain, index, topup, out, **kwargs):
    """Wrapper for the ``applytopup`` command. """

    valmap = {
        'v'       : wutils.SHOW_IF_TRUE,
        'verbose' : wutils.SHOW_IF_TRUE
    }

    asrt.assertFileExists(datain)
    for fn in imain.split(','):
        asrt.assertIsNifti(fn)

    allargs = {
        'imain'   : imain,
        'datain'  : datain,
        'inindex' : index,
        'topup'   : topup,
        'out'     : out
    }
    allargs.update(kwargs)

    cmd  = ['applytopup'] + wutils.applyArgStyle('--=', valmap=valmap, **allargs)

    return cmd
