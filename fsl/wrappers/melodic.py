#!/usr/bin/env python
#
# melodic.py - Wrappers for melodic.
#
# Author: Sean Fitzgibbon <sean.fitzgibbon@ndcn.ox.ac.uk>
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides wrapper functions for the FSL
`MELODIC <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/MELODIC>`_ tool, and other
related utilities.

.. autosummary::
   :nosignatures:

   melodic
   fsl_regfilt
   fsl_glm
"""


import fsl.utils.assertions as asrt
from . import wrapperutils  as wutils


@wutils.fileOrArray('mix', 'Tdes', 'Tcon', 'Sdes', 'Scon')
@wutils.fileOrImage('input', 'mask', 'ICs', 'bgimage')
@wutils.fslwrapper
def melodic(input, **kwargs):
    """Wrapper for the ``melodic`` command."""

    valmap = {
        'Oall'         : wutils.SHOW_IF_TRUE,
        'Ounmix'       : wutils.SHOW_IF_TRUE,
        'Ostats'       : wutils.SHOW_IF_TRUE,
        'Opca'         : wutils.SHOW_IF_TRUE,
        'Owhite'       : wutils.SHOW_IF_TRUE,
        'Oorig'        : wutils.SHOW_IF_TRUE,
        'Omean'        : wutils.SHOW_IF_TRUE,
        'verbose'      : wutils.SHOW_IF_TRUE,
        'debug'        : wutils.SHOW_IF_TRUE,
        'report'       : wutils.SHOW_IF_TRUE,
        'CIFTI'        : wutils.SHOW_IF_TRUE,
        'varnorm'      : wutils.SHOW_IF_TRUE,
        'nomask'       : wutils.SHOW_IF_TRUE,
        'nobet'        : wutils.SHOW_IF_TRUE,
        'sep_vn'       : wutils.SHOW_IF_TRUE,
        'disableMigp'  : wutils.SHOW_IF_TRUE,
        'update_mask'  : wutils.HIDE_IF_TRUE,
        'migp_shuffle' : wutils.HIDE_IF_TRUE,
        'no_mm'        : wutils.SHOW_IF_TRUE,
        'logPower'     : wutils.SHOW_IF_TRUE,
    }

    cmd  = ['melodic', '--in={}'.format(input)]
    cmd += wutils.applyArgStyle('--=', valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrImage('input', 'out', 'mask', 'out_data')
@wutils.fileOrArray('design', 'out_mix')
@wutils.fslwrapper
def fsl_regfilt(input, out, design, **kwargs):
    """Wrapper for the ``fsl_regfilt`` command. """

    asrt.assertIsNifti(input, out)

    valmap = {
        'freqfilt' : wutils.SHOW_IF_TRUE,
        'freq_ic'  : wutils.HIDE_IF_TRUE,
        'vn'       : wutils.SHOW_IF_TRUE,
        'F'        : wutils.SHOW_IF_TRUE,
        'v'        : wutils.SHOW_IF_TRUE,
        'a'        : wutils.SHOW_IF_TRUE,
    }

    cmd  = ['fsl_regfilt',
            '--in={}'.format(input),
            '--out={}'.format(out),
            '--design={}'.format(design)]
    cmd += wutils.applyArgStyle('--=', valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrImage('input', 'mask')
@wutils.fileOrArray('design')
@wutils.fslwrapper
def fsl_glm(input, out=None, design=None, **kwargs):
    """Wrapper for the ``fsl_glm`` command. """

    asrt.assertIsNifti(input)

    valmap = {
        'des_norm' : wutils.SHOW_IF_TRUE,
        'dat_norm' : wutils.SHOW_IF_TRUE,
        'demean'   : wutils.SHOW_IF_TRUE,
        'vn'       : wutils.SHOW_IF_TRUE
    }

    cmd = ['fsl_glm', f'--in={input}']

    if out    is not None: cmd.append(f'--out={out}')
    if design is not None: cmd.append(f'--design={design}')

    cmd += wutils.applyArgStyle('--=', valmap=valmap, **kwargs)

    return cmd
