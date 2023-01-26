#!/usr/bin/env python
#
# bedpostx.py - Wrappers for bedpostx probtrackx commands.
#
# Author: Fidel Alfaro Almagro <fidel.alfaroalmagro@ndcn.ox.ac.uk>
#
"""This module provides wrapper functions for the main FSL
`FDT <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FDT>` tractography
commands.

.. autosummary::
   :nosignatures:

   xfibres
   xfibres_gpu
   split_parts_gpu
   bedpostx_postproc_gpu
   probtrackx
   probtrackx2
   probtrackx2_gpu
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
"""Boolean options for the ``xfibres``/``xfibres_gpu`` commands, used by the
corresponding wrapper functions.
"""


PROBTRACKX2_VALMAP = {
    'forcedir'        : wutils.SHOW_IF_TRUE,
    'simple'          : wutils.SHOW_IF_TRUE,
    'network'         : wutils.SHOW_IF_TRUE,
    'opd'             : wutils.SHOW_IF_TRUE,
    'pd'              : wutils.SHOW_IF_TRUE,
    'ompl'            : wutils.SHOW_IF_TRUE,
    'os2t'            : wutils.SHOW_IF_TRUE,
    's2tastext'       : wutils.SHOW_IF_TRUE,
    'closestvertex'   : wutils.SHOW_IF_TRUE,
    'wayorder'        : wutils.SHOW_IF_TRUE,
    'onewaycondition' : wutils.SHOW_IF_TRUE,
    'omatrix1'        : wutils.SHOW_IF_TRUE,
    'omatrix2'        : wutils.SHOW_IF_TRUE,
    'omatrix3'        : wutils.SHOW_IF_TRUE,
    'omatrix4'        : wutils.SHOW_IF_TRUE,
    'l'               : wutils.SHOW_IF_TRUE,
    'loopcheck'       : wutils.SHOW_IF_TRUE,
    'f'               : wutils.SHOW_IF_TRUE,
    'usef'            : wutils.SHOW_IF_TRUE,
    'modeuler'        : wutils.SHOW_IF_TRUE,
    'forcefirststep'  : wutils.SHOW_IF_TRUE,
    'osampfib'        : wutils.SHOW_IF_TRUE,
    'onewayonly'      : wutils.SHOW_IF_TRUE,
    'opathdir'        : wutils.SHOW_IF_TRUE,
    'savepaths'       : wutils.SHOW_IF_TRUE,
    'otargetpaths'    : wutils.SHOW_IF_TRUE,
    'noprobinterpol'  : wutils.SHOW_IF_TRUE,
}
"""Boolean options for the ``probtrackx2``/``probtrackx2_gpu`` commands, used
by the corresponding wrapper functions.
"""


@wutils.fileOrImage('data', 'mask',)
@wutils.fileOrArray('bvecs', 'bvals')
@wutils.fslwrapper
def xfibres(data, mask, bvecs, bvals, **kwargs):
    """Wrapper for the ``xfibres`` command."""

    asrt.assertFileExists(data, bvecs, bvals)
    asrt.assertIsNifti(mask)

    cmd = ['xfibres',
           f'--data={data}',
           f'--mask={mask}',
           f'--bvecs={bvecs}',
           f'--bvals={bvals}']

    cmd += wutils.applyArgStyle('--=', valmap=XFIBRES_VALMAP, **kwargs)
    return cmd


@wutils.fileOrImage('data', 'mask',)
@wutils.fileOrArray('bvecs', 'bvals')
@wutils.fslwrapper
def xfibres_gpu(data, mask, bvecs, bvals, subjdir, idpart,
                nparts, numvoxels, **kwargs):
    """Wrapper for the ``xfibres_gpu`` command."""

    asrt.assertFileExists(data, bvecs, bvals)
    asrt.assertIsNifti(mask)

    cmd = ['xfibres_gpu',
           '--data='  + data,
           '--mask='  + mask,
           '--bvecs=' + bvecs,
           '--bvals=' + bvals]

    cmd += wutils.applyArgStyle('--=', valmap=XFIBRES_VALMAP, **kwargs)
    cmd += [subjdir, str(idpart), str(nparts), str(numvoxels)]
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
             str(Gradfile), Use_grad_file, str(TotalNumParts), OutputDirectory]
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
    cmd += [str(TotalNumVoxels), str(TotalNumParts), SubjectDir, bindir]
    return cmd


@wutils.fileOrImage('mask', 'seed')
@wutils.fslwrapper
def probtrackx(samples, mask, seed, **kwargs):
    """Wrapper for the ``probtrackx`` command. """

    valmap = {
        'opd'          : wutils.SHOW_IF_TRUE,
        'pd'           : wutils.SHOW_IF_TRUE,
        'os2t'         : wutils.SHOW_IF_TRUE,
        'omatrix1'     : wutils.SHOW_IF_TRUE,
        'omatrix2'     : wutils.SHOW_IF_TRUE,
        'omatrix3'     : wutils.SHOW_IF_TRUE,
        'omaskmatrix'  : wutils.SHOW_IF_TRUE,
        'network'      : wutils.SHOW_IF_TRUE,
        'forcedir'     : wutils.SHOW_IF_TRUE,
        'sampvox'      : wutils.SHOW_IF_TRUE,
        'l'            : wutils.SHOW_IF_TRUE,
        'loopcheck'    : wutils.SHOW_IF_TRUE,
        'f'            : wutils.SHOW_IF_TRUE,
        'usef'         : wutils.SHOW_IF_TRUE,
        'modeuler'     : wutils.SHOW_IF_TRUE,
        's2tastext'    : wutils.SHOW_IF_TRUE,
        'splitmatrix2' : wutils.SHOW_IF_TRUE,
    }

    asrt.assertIsNifti(mask, seed)

    cmd = ['probtrackx',
           '--samples=' + samples,
           '--mask='    + mask,
           '--seed='    + seed]

    cmd += wutils.applyArgStyle('--=', valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrImage('mask', 'seed')
@wutils.fslwrapper
def probtrackx2(samples, mask, seed, out=None, **kwargs):
    """Wrapper for the ``probtrackx2`` command. """



    asrt.assertIsNifti(mask, seed)

    cmd = ['probtrackx2',
           f'--samples={samples}',
           f'--mask={mask}',
           f'--seed={seed}']

    if out is not None:
        cmd.append(f'--out={out}')

    cmd += wutils.applyArgStyle('--=', valmap=PROBTRACKX2_VALMAP, **kwargs)

    return cmd


@wutils.fileOrImage('mask', 'seed')
@wutils.fslwrapper
def probtrackx2_gpu(samples, mask, seed, out=None, **kwargs):
    """Wrapper for the ``probtrackx2_gpu`` command. """

    asrt.assertIsNifti(mask, seed)

    cmd = ['probtrackx2_gpu',
           f'--samples={samples}',
           f'--mask={mask}',
           f'--seed={seed}']

    if out is not None:
        cmd.append(f'--out={out}')

    cmd += wutils.applyArgStyle('--=', valmap=PROBTRACKX2_VALMAP, **kwargs)

    return cmd
