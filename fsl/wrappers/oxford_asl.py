#!/usr/bin/env python
#
# oxford_asl.py - Wrappers for oxford_asl commands.
#
# Author: Fidel Alfaro Almagro <fidel.alfaroalmagro@ndcn.ox.ac.uk>
#
"""This module provides wrapper functions for the main FSL
`oxford_asl <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/oxford_asl>` commands.

.. autosummary::
   :nosignatures:

   asl_file
   oxford_asl
"""


import fsl.utils.assertions as asrt
from . import wrapperutils  as wutils


@wutils.fileOrImage('data')
@wutils.fslwrapper
def oxford_asl(data, out, **kwargs):
    """Wrapper for the ``oxford_asl`` command."""

    asrt.assertIsNifti(data)

    vmap = {
        'wp'                           : wutils.SHOW_IF_TRUE,
        'mc'                           : wutils.SHOW_IF_TRUE,
        'noiseprior'                   : wutils.SHOW_IF_TRUE,
        'edgecorr'                     : wutils.SHOW_IF_TRUE,
        'senscorr'                     : wutils.SHOW_IF_TRUE,
        't2star'                       : wutils.SHOW_IF_TRUE,
        'reg-init-bbr'                 : wutils.SHOW_IF_TRUE,
        'finalreg'                     : wutils.SHOW_IF_TRUE,
        'zblur'                        : wutils.SHOW_IF_TRUE,
        'structout'                    : wutils.SHOW_IF_TRUE,
        'advout'                       : wutils.SHOW_IF_TRUE,
        'infert1'                      : wutils.SHOW_IF_TRUE,
        'artoff'                       : wutils.SHOW_IF_TRUE,
        'artonly'                      : wutils.SHOW_IF_TRUE,
        'artsupp'                      : wutils.SHOW_IF_TRUE,
        'fixbat'                       : wutils.SHOW_IF_TRUE,
        'spatial'                      : wutils.SHOW_IF_TRUE,
        'fixbolus'                     : wutils.SHOW_IF_TRUE,
        'casl'                         : wutils.SHOW_IF_TRUE,
        'pvcorr'                       : wutils.SHOW_IF_TRUE,
        'fulldata'                     : wutils.SHOW_IF_TRUE,
        'fast'                         : wutils.SHOW_IF_TRUE,
        'nofmapreg'                    : wutils.SHOW_IF_TRUE,
        'region-analysis'              : wutils.SHOW_IF_TRUE,
        'region-analysis-save-rois'    : wutils.SHOW_IF_TRUE,
        'qc-outout'                    : wutils.SHOW_IF_TRUE,
        'debug'                        : wutils.SHOW_IF_TRUE,
        'devel'                        : wutils.SHOW_IF_TRUE,
        'region-analysis-atlas'        : wutils.EXPAND_LIST,
        'region-analysis-atlas-labels' : wutils.EXPAND_LIST,
        'region-analysis-psf'          : wutils.EXPAND_LIST,
    }

    cmd = ['oxford_asl', '-i', data, '-o', out]


    def argmap(arg):
        return arg.replace('_', '-')

    cmd += wutils.applyArgStyle(valmap=vmap, **kwargs, argmap=argmap)

    return cmd


@wutils.fileOrImage('data')
@wutils.fslwrapper
def asl_file(data, ntis, out=None, **kwargs):
    """Wrapper for the ``asl_file`` command."""

    asrt.assertIsNifti(data)

    vmap = {
        'pairs'       : wutils.SHOW_IF_TRUE,
        'inpairs'     : wutils.SHOW_IF_TRUE,
        'spairs'      : wutils.SHOW_IF_TRUE,
        'diff'        : wutils.SHOW_IF_TRUE,
        'surrdif'     : wutils.SHOW_IF_TRUE,
        'extrapolate' : wutils.SHOW_IF_TRUE,
    }

    cmd = ['asl_file',
           '--data='  + data,
           '--ntis='  + str(ntis)]

    if out is not None:
        cmd += ['--out=' + out]

    cmd += wutils.applyArgStyle('--=', valmap=vmap, **kwargs)

    return cmd
