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

def argmap(arg):
    return arg.replace('_', '-')


@wutils.fileOrImage('data')
@wutils.fslwrapper
def oxford_asl(data, out, **kwargs):
    """Wrapper for the ``oxford_asl`` command."""

    asrt.assertIsNifti(data)

    vmap = {
        'reg-init-bbr'              : wutils.SHOW_IF_TRUE,
        'casl'                      : wutils.SHOW_IF_TRUE,
        'fixbolus'                  : wutils.SHOW_IF_TRUE,
        'spatial'                   : wutils.SHOW_IF_TRUE,
        'nofmapreg'                 : wutils.SHOW_IF_TRUE,
        'qc-outout'                 : wutils.SHOW_IF_TRUE,
        'region-analysis-save-rois' : wutils.SHOW_IF_TRUE,
    }

    cmd = ['oxford_asl',
           f'-i {data}',
           f'-o {out}']

    region_analysis_atlas        = kwargs.pop('region_analysis_atlas', None)
    region_analysis_atlas_labels = kwargs.pop('region_analysis_atlas_labels', None)
    region_analysis_psf          = kwargs.pop('region_analysis_psf', None)

    if region_analysis_atlas is not None:
        cmd += ['--region-analysis']
        for r in region_analysis_atlas:
            cmd += [f'--region-analysis-atlas={r}']

    if region_analysis_atlas_labels is not None:
        for r in region_analysis_atlas_labels:
            cmd += [f'--region-analysis-atlas-labels={r}']

    if region_analysis_psf is not None:
        for r in region_analysis_psf:
            cmd += [f'--region-analysis-psf={r}']

    cmd += wutils.applyArgStyle(valmap=vmap, **kwargs, argmap=argmap)

    return cmd


@wutils.fileOrImage('data')
@wutils.fslwrapper
def asl_file(data, ntis, **kwargs):
    """Wrapper for the ``asl_file`` command."""

    asrt.assertIsNifti(data)

    vmap = {
        'diff'        : wutils.SHOW_IF_TRUE,
        'surrdif'     : wutils.SHOW_IF_TRUE,
        'extrapolate' : wutils.SHOW_IF_TRUE,
        'epoch'       : wutils.SHOW_IF_TRUE,
        'deconv'      : wutils.SHOW_IF_TRUE
    }

    cmd = ['asl_file',
           '--data='  + data,
           '--ntis='  + str(ntis)]

    cmd += wutils.applyArgStyle('--=', valmap=vmap, **kwargs)

    return cmd

