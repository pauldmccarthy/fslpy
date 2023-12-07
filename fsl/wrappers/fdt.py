#!/usr/bin/env python
#
# fdt.py - Wrappers for FDT commands.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains wrapper functions for various FDT commands. """


import fsl.utils.assertions      as asrt
import fsl.wrappers.wrapperutils as wutils


@wutils.fileOrImage('input', 'output', 'ref', 'warpfield',
                    'rotwarp', 'mask', 'refmask')
@wutils.fileOrArray('affine', 'premat', 'postmat', 'rotmat')
@wutils.fslwrapper
def vecreg(input, output, ref, **kwargs):
    """Wrapper for the ``vecreg`` command. """

    cmd  = ['vecreg', '-i', input, '-o', output, '-r', ref]
    cmd += wutils.applyArgStyle('--=', **kwargs)

    return cmd


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
