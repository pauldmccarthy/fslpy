#!/usr/bin/env python
#
# bedpostx.py - Wrappers for bedpostx and related commands.
#
# Author: Fidel Alfaro Almagro <fidel.alfaroalmagro@ndcn.ox.ac.uk>
#
"""This module provides wrapper functions for various FSL
`FDT <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FDT>` tractography
commands.

.. autosummary::
   :nosignatures:

   xfibres_gpu
   split_parts_gpu
   bedpostx_postproc_gpu
   probtrackx
"""


import fsl.utils.assertions as asrt
from . import wrapperutils  as wutils


XFIBRES_VALMAP = {
    'V'          : wutils.SHOW_IF_TRUE,
    'verbose'    : wutils.SHOW_IF_TRUE,
    'forcedir'   : wutils.SHOW_IF_TRUE,
    'noard'      : wutils.SHOW_IF_TRUE,
    'allard'     : wutils.SHOW_IF_TRUE,
    'nospat'     : wutils.SHOW_IF_TRUE,
    'nonlinear'  : wutils.SHOW_IF_TRUE,
    'cnonlinear' : wutils.SHOW_IF_TRUE,
    'rician'     : wutils.SHOW_IF_TRUE,
    'f0'         : wutils.SHOW_IF_TRUE,
    'ardf0'      : wutils.SHOW_IF_TRUE
}
"""Boolean options for the ``xfibres``/``xfibres_gpu`` commands, used by
a couple of wrapper functions.
"""


@wutils.fileOrImage('data', 'mask',)
@wutils.fileOrArray('bvecs', 'bvals')
@wutils.fslwrapper
def xfibres_gpu(data, mask, bvecs, bvals, SubjectDir, NumThisPart,
                TotalNumParts, TotalNumVoxels, **kwargs):
    """Wrapper for the ``xfibres_gpu`` command."""

    asrt.assertFileExists(data, bvecs, bvals)
    asrt.assertIsNifti(mask)

    cmd = ['xfibres_gpu',
           '--data='  + data,
           '--mask='  + mask,
           '--bvecs=' + bvecs,
           '--bvals=' + bvals]

    cmd += wutils.applyArgStyle('--=', valmap=XFIBRES_VALMAP, **kwargs)
    cmd += [SubjectDir, NumThisPart, TotalNumParts, TotalNumVoxels]
    return cmd


@wutils.fileOrImage('Datafile', 'Maskfile')
@wutils.fileOrArray('Bvalsfile', 'Bvecsfile')
@wutils.fslwrapper
def split_parts_gpu(Datafile, Maskfile, Bvalsfile, Bvecsfile, TotalNumParts,
                    OutputDirectory, Gradfile=None):
    """Wrapper for the ``split_parts_gpu`` command. Note that the ``Gradfile``
    option is handled slightly differently to the command-line interface -
    the ``Use_grad_file`` argument is automatically set based on whether the
    ``Gradfile`` argument is provided.
    """

    asrt.assertFileExists(Bvalsfile, Bvecsfile)
    asrt.assertIsNifti(Datafile, Maskfile)

    if Gradfile is None: Use_grad_file = '0'
    else:                Use_grad_file = '1'

    cmd  = ['split_parts_gpu', Datafile, Maskfile, Bvalsfile, Bvecsfile,
             Gradfile, Use_grad_file, TotalNumParts, OutputDirectory]
    return cmd


@wutils.fileOrImage('data', 'mask',)
@wutils.fileOrArray('bvecs', 'bvals')
@wutils.fslwrapper
def bedpostx_postproc_gpu(data, mask, bvecs, bvals, TotalNumVoxels,
                          TotalNumParts, SubjectDir, bindir, **kwargs):
    """Wrapper for the ``bedpostx_postproc_gpu`` command."""

    asrt.assertFileExists(data, bvecs, bvals)
    asrt.assertIsNifti(mask)

    cmd = ['bedpostx_postproc_gpu.sh',
           '--data='  + data,
           '--mask='  + mask,
           '--bvecs=' + bvecs,
           '--bvals=' + bvals]

    cmd += wutils.applyArgStyle('--=', valmap=XFIBRES_VALMAP, **kwargs)
    cmd += [TotalNumVoxels, TotalNumParts, SubjectDir, bindir]
    return cmd


@wutils.fileOrImage('mask', 'seed')
@wutils.fslwrapper
def probtrackx(samples, mask, seed, **kwargs):
    """Wrapper for the ``probtrackx`` command. """

    valmap = {
        'forcedir'  : wutils.SHOW_IF_TRUE,
        'network'   : wutils.SHOW_IF_TRUE,
        'vebose'    : wutils.SHOW_IF_TRUE,
        'opd'       : wutils.SHOW_IF_TRUE,
        'pd'        : wutils.SHOW_IF_TRUE,
        'sampvox'   : wutils.SHOW_IF_TRUE,
        'loopcheck' : wutils.SHOW_IF_TRUE,
        'usef'      : wutils.SHOW_IF_TRUE,
        'modeuler'  : wutils.SHOW_IF_TRUE,
    }

    asrt.assertIsNifti(mask, seed)

    cmd = ['probtrackx',
           '--samples=' + samples,
           '--mask='    + mask,
           '--seed='    + seed]

    cmd += wutils.applyArgStyle('--=', valmap=valmap, **kwargs)

    return cmd
