#!/usr/bin/env python
#
# fnirt.py - FNIRT wrapper functions.
#
# Author: Sean Fitzgibbon <sean.fitzgibbon@ndcn.ox.ac.uk>
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides wrapper functions for the FSL `FNIRT
<https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FNIRT/>`_ tool, used for performing
non-linear registration of 3D images.

.. autosummary::
   :nosignatures:

   fnirt
   applywarp
   invwarp
   convertwarp
"""


import fsl.utils.assertions as asrt
from . import wrapperutils  as wutils


@wutils.fileOrImage('src', 'ref', 'inwarp', 'cout', 'iout', 'fout', 'jout',
                    'refout', 'refmask', 'inmask')
@wutils.fileOrArray('aff')
@wutils.fslwrapper
def fnirt(src, ref, **kwargs):
    """Wrapper for the ``fnirt`` command."""

    asrt.assertIsNifti(src, ref)

    cmd  = ['fnirt', '--in={}'.format(src), '--ref={}'.format(ref)]
    cmd += wutils.applyArgStyle('--=', **kwargs)

    return cmd


@wutils.fileOrImage('src', 'ref', 'out', 'warp', 'mask')
@wutils.fileOrArray('premat', 'postmat')
@wutils.fslwrapper
def applywarp(src, ref, out, warp, **kwargs):
    """Wrapper for the ``applywarp`` command. """

    valmap = {
        'abs'     : wutils.SHOW_IF_TRUE,
        'rel'     : wutils.SHOW_IF_TRUE,
        'super'   : wutils.SHOW_IF_TRUE,
        'debug'   : wutils.SHOW_IF_TRUE,
        'verbose' : wutils.SHOW_IF_TRUE,
    }

    cmd = ['applywarp',
           '--in={}'.format(src),
           '--ref={}'.format(ref),
           '--out={}'.format(out),
           '--warp={}'.format(warp)]

    cmd += wutils.applyArgStyle('--=', valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrImage('warp', 'ref', 'out')
@wutils.fslwrapper
def invwarp(warp, ref, out, **kwargs):
    """Wrapper for the ``invwarp`` command."""

    valmap = {
        'abs'          : wutils.SHOW_IF_TRUE,
        'rel'          : wutils.SHOW_IF_TRUE,
        'noconstraint' : wutils.SHOW_IF_TRUE,
        'debug'        : wutils.SHOW_IF_TRUE,
        'verbose'      : wutils.SHOW_IF_TRUE,
    }

    asrt.assertIsNifti(warp, ref, out)

    cmd  = ['invwarp',
            '--warp={}'.format(warp),
            '--ref={}'.format(ref),
            '--out={}'.format(out)]

    cmd += wutils.applyArgStyle('--=', valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrImage('out', 'ref', 'warp1', 'warp2', 'shiftmap')
@wutils.fileOrArray('premat', 'midmat', 'postmat')
@wutils.fslwrapper
def convertwarp(out, ref, **kwargs):
    """Wrapper for the ``convertwarp`` command."""

    valmap = {
        'abs'        : wutils.SHOW_IF_TRUE,
        'rel'        : wutils.SHOW_IF_TRUE,
        'absout'     : wutils.SHOW_IF_TRUE,
        'relout'     : wutils.SHOW_IF_TRUE,
        'jacobian'   : wutils.SHOW_IF_TRUE,
        'jstats'     : wutils.SHOW_IF_TRUE,
        'constrainj' : wutils.SHOW_IF_TRUE,
        'verbose'    : wutils.SHOW_IF_TRUE,
    }

    cmd  = ['convertwarp', '--ref={}'.format(ref), '--out={}'.format(out)]
    cmd += wutils.applyArgStyle('--=', valmap=valmap, **kwargs)

    return cmd
