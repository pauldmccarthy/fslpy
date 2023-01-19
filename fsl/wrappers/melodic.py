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
        'v'        : wutils.SHOW_IF_TRUE,
    }

    cmd  = ['fsl_regfilt',
            '--in={}'.format(input),
            '--out={}'.format(out),
            '--design={}'.format(design)]
    cmd += wutils.applyArgStyle('--=', valsep=',', valmap=valmap, **kwargs)

    return cmd

@wutils.fileOrImage('input', 'mask')
@wutils.fileOrArray('design')
@wutils.fslwrapper
def fsl_glm(input, **kwargs):
    """Wrapper for the ``fsl_glm`` command. 

Compulsory arguments (You MUST set one or more of):
    :arg input:         input file name (text matrix or 3D/4D image file)

Optional arguments (You may optionally specify one or more of):
    :arg out:        output file name for GLM parameter estimates (GLM betas)
    :arg design:     file name of the GLM design matrix (text time courses for temporal regression or an image file for spatial regression )
    :arg contrasts:  matrix of t-statistics contrasts
    :arg mask:       mask image file name if input is image
    :arg dof:        set degrees-of-freedom explicitly
    :arg des_norm:   switch on normalisation of the design matrix columns to unit std. deviation
    :arg dat_norm:   switch on normalisation of the data time series to unit std. deviation
    :arg vn:         perform MELODIC variance-normalisation on data
    :arg demean:     switch on de-meaning of design and data
    :arg out_cope:   output file name for COPEs (either as text file or image)
    :arg out_z:      output file name for Z-stats (either as text file or image)
    :arg out_t:      output file name for t-stats (either as text file or image)
    :arg out_p:      output file name for p-values of Z-stats (either as text file or image)
    :arg out_f:      output file name for F-value of full model fit
    :arg out_pf:     output file name for p-value for full model fit
    :arg out_res:    output file name for residuals
    :arg out_varcb:  output file name for variance of COPEs
    :arg out_sigsq:  output file name for residual noise variance sigma-square
    :arg out_data:   output file name for pre-processed data
    :arg out_vnscales:  output file name for scaling factors for variance normalisation
    :arg vxt:        list of text files containing text matrix confounds. caution BETA option.
    :arg vxf:        list of 4D images containing voxelwise confounds. caution BETA option.


    """

    asrt.assertIsNifti(input)

    valmap = {
        'des_norm' : wutils.SHOW_IF_TRUE,
        'dat_norm' :wutils.SHOW_IF_TRUE,
        'demean'   : wutils.SHOW_IF_TRUE,
        'vn'       : wutils.SHOW_IF_TRUE
    }

    cmd  = ['fsl_glm',
            '--in={}'.format(input)]
    cmd += wutils.applyArgStyle('--=', valsep=',', valmap=valmap, **kwargs)

    return cmd
