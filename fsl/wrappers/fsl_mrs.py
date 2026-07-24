#!/usr/bin/env python
# fsl_mrs.py - Wrappers for FSL-MRS command line tools.
#
# Author: Vasilis Karlaftis <vasilis.karlaftis@ndcn.ox.ac.uk>
#
#
"""This module provides wrapper functions for FSL-MRS command line tools.

.. autosummary::
   :nosignatures:

   fsl_mrs
   fsl_mrsi
   fsl_mrs_preproc
   fsl_mrs_preproc_edit
   svs_segment
   mrsi_segment
   fsl_dynmrs
   basis2spec
   fmrs_stats
"""

import fsl.utils.assertions as asrt
from . import wrapperutils as wutils
from pathlib import Path


@wutils.fileOrNiftiMRS('data', 'h2o')
@wutils.fileOrImage('t1')
@wutils.fileOrBasis('basis')
@wutils.fslwrapper
def fsl_mrs(data, basis, output, **kwargs):
    """Wrapper for the ``fsl_mrs`` command.
    The following arguments are currently supported:
    algo, ignore, keep, combine, ppmlim, h2o, baseline,
    baseline_order, metab_groups, lorentzian, free_shift,
    ind_scale, disable_MH_priors, mh_samples, t1, TE, TR,
    tissue_frac, t1_values, t2_values, internal_ref,
    wref_metabolite, ref_protons, ref_int_limits, h2o_scale,
    report, verbose, overwrite, conj_fid, no_conj_fid,
    conj_basis, no_conj_basis, no_rescale, export_baseline,
    export_no_baseline, export_separate, f/filename, config.
    """

    asrt.assertIsNiftiMRS(data)
    asrt.assertIsMRSBasis(basis)

    argmap = {
        't1_values' : 't1-values',
        't2_values' : 't2-values',
        'f'         : 'filename',
    }

    valmap = {
        'lorentzian'         : wutils.SHOW_IF_TRUE,
        'free_shift'         : wutils.SHOW_IF_TRUE,
        'disable_MH_priors'  : wutils.SHOW_IF_TRUE,
        'report'             : wutils.SHOW_IF_TRUE,
        'verbose'            : wutils.SHOW_IF_TRUE,
        'overwrite'          : wutils.SHOW_IF_TRUE,
        'conj_fid'           : wutils.SHOW_IF_TRUE,
        'no_conj_fid'        : wutils.SHOW_IF_TRUE,
        'conj_basis'         : wutils.SHOW_IF_TRUE,
        'no_conj_basis'      : wutils.SHOW_IF_TRUE,
        'no_rescale'         : wutils.SHOW_IF_TRUE,
        'export_baseline'    : wutils.SHOW_IF_TRUE,
        'export_no_baseline' : wutils.SHOW_IF_TRUE,
        'export_separate'    : wutils.SHOW_IF_TRUE,
        'combine'            : wutils.EXPAND_LIST,
    }

    cmd = ['fsl_mrs',
           '--data', data,
           '--output', output,
           '--basis', basis,
    ]

    cmd += wutils.applyArgStyle('--', argmap=argmap, valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrNiftiMRS('data', 'h2o')
@wutils.fileOrImage('mask')
@wutils.fileOrBasis('basis')
@wutils.fslwrapper
def fsl_mrsi(data, basis, output, **kwargs):
    """Wrapper for the ``fsl_mrsi`` command.
    The following arguments are currently supported:
    mask, algo, ignore, keep, combine, ppmlim, h2o, baseline,
    baseline_order, metab_groups, lorentzian, free_shift,
    ind_scale, disable_MH_priors, TE, TR, tissue_frac,
    internal_ref, wref_metabolite, ref_protons, ref_int_limits,
    h2o_scale, report, output_correlations, verbose, overwrite,
    single_proc, parallel, parallel_workers,
    parallel-batch-size-multiple, minimize-maxfun,
    slow-fit-log-threshold, slow-fit-log, slow-fit-worker-log-lines,
    conj_fid, no_conj_fid, conj_basis, no_conj_basis, no_rescale,
    config.
    """

    asrt.assertIsNiftiMRS(data)
    asrt.assertIsMRSBasis(basis)

    argmap = {
        'parallel_workers' : 'parallel-workers',
    }

    valmap = {
        'lorentzian'          : wutils.SHOW_IF_TRUE,
        'free_shift'          : wutils.SHOW_IF_TRUE,
        'disable_MH_priors'   : wutils.SHOW_IF_TRUE,
        'report'              : wutils.SHOW_IF_TRUE,
        'output_correlations' : wutils.SHOW_IF_TRUE,
        'verbose'             : wutils.SHOW_IF_TRUE,
        'overwrite'           : wutils.SHOW_IF_TRUE,
        'single_proc'         : wutils.SHOW_IF_TRUE,
        'conj_fid'            : wutils.SHOW_IF_TRUE,
        'no_conj_fid'         : wutils.SHOW_IF_TRUE,
        'conj_basis'          : wutils.SHOW_IF_TRUE,
        'no_conj_basis'       : wutils.SHOW_IF_TRUE,
        'no_rescale'          : wutils.SHOW_IF_TRUE,
        'combine'             : wutils.EXPAND_LIST,
    }

    cmd = ['fsl_mrsi',
           '--data', data,
           '--output', output,
           '--basis', basis,
    ]

    cmd += wutils.applyArgStyle('--', argmap=argmap, valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrNiftiMRS('data', 'reference', 'quant', 'ecc', 'noise', 'target')
@wutils.fileOrImage('t1')
@wutils.fslwrapper
def fsl_mrs_preproc(data, reference, output, **kwargs):
    """Wrapper for the ``fsl_mrs_preproc`` command.
    The following arguments are currently supported:
    quant, ecc, noise, target, fmrs, noremoval, noaverage, noalign,
    align_limits, align_window, remove_water, hlsvd, truncate_fid,
    leftshift, t1, verbose, conjugate, overwrite, report, config.
    """

    asrt.assertIsNiftiMRS(data, reference)

    argmap = {
        'remove_water' : 'remove-water',
        'truncate_fid' : 'truncate-fid',
    }

    valmap = {
        'fmrs'          : wutils.SHOW_IF_TRUE,
        'noremoval'     : wutils.SHOW_IF_TRUE,
        'noaverage'     : wutils.SHOW_IF_TRUE,
        'noalign'       : wutils.SHOW_IF_TRUE,
        'remove-water'  : wutils.SHOW_IF_TRUE,
        'hlsvd'         : wutils.SHOW_IF_TRUE,
        'verbose'       : wutils.SHOW_IF_TRUE,
        'conjugate'     : wutils.SHOW_IF_TRUE,
        'report'        : wutils.SHOW_IF_TRUE,
        'overwrite'     : wutils.SHOW_IF_TRUE,
    }

    cmd = ['fsl_mrs_preproc',
           '--data', data,
           '--reference', reference,
           '--output', output,
    ]
    cmd += wutils.applyArgStyle('--', argmap=argmap, valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrNiftiMRS('data', 'reference', 'quant', 'ecc', 'noise')
@wutils.fileOrImage('t1')
@wutils.fslwrapper
def fsl_mrs_preproc_edit(data, reference, output, **kwargs):
    """Wrapper for the ``fsl_mrs_preproc_edit`` command.
    The following arguments are currently supported:
    quant, ecc, noise, noaverage, noalign, align_ppm_dynamic,
    align_window_dynamic, align_ppm_edit, dynamic_align,
    dynamic_align_edit, remove_water, hlsvd, truncate_fid,
    leftshift, t1, verbose, conjugate, overwrite, report, config.
    """

    asrt.assertIsNiftiMRS(data, reference)

    argmap = {
        'remove_water' : 'remove-water',
        'truncate_fid' : 'truncate-fid',
    }

    valmap = {
        'noaverage'          : wutils.SHOW_IF_TRUE,
        'noalign'            : wutils.SHOW_IF_TRUE,
        'dynamic_align'      : wutils.SHOW_IF_TRUE,
        'dynamic_align_edit' : wutils.SHOW_IF_TRUE,
        'remove-water'       : wutils.SHOW_IF_TRUE,
        'hlsvd'              : wutils.SHOW_IF_TRUE,
        'verbose'            : wutils.SHOW_IF_TRUE,
        'conjugate'          : wutils.SHOW_IF_TRUE,
        'overwrite'          : wutils.SHOW_IF_TRUE,
        'report'             : wutils.SHOW_IF_TRUE,
    }

    cmd = ['fsl_mrs_preproc_edit',
           '--data', data,
           '--reference', reference,
           '--output', output,
    ]

    cmd += wutils.applyArgStyle('--', argmap=argmap, valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrNiftiMRS('svs')
@wutils.fileOrImage('t1', outprefix='filename')
@wutils.fslwrapper
def svs_segment(svs, **kwargs):
    """Wrapper for the ``svs_segment`` command.
    The following arguments are currently supported:
    t/t1, a/anat, o/output, f/filename, m/mask_only, no_normalisation.
    """

    asrt.assertIsNiftiMRS(svs)

    argmap = {
        't' : 't1',
        'a' : 'anat',
        'o' : 'output',
        'f' : 'filename',
        'm' : 'mask_only',
    }

    valmap = {
        'no_normalisation' : wutils.SHOW_IF_TRUE,
        'mask_only'        : wutils.SHOW_IF_TRUE,
    }

    cmd = ['svs_segment', svs]
    cmd += wutils.applyArgStyle('--', argmap=argmap, valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrNiftiMRS('mrsi')
@wutils.fileOrImage('t1', outprefix='filename')
@wutils.fslwrapper
def mrsi_segment(mrsi, **kwargs):
    """Wrapper for the ``mrsi_segment`` command.
    The following arguments are currently supported:
    t/t1, a/anat, o/output, f/filename, no_normalisation.
    """

    asrt.assertIsNiftiMRS(mrsi)

    argmap = {
        't' : 't1',
        'a' : 'anat',
        'o' : 'output',
        'f' : 'filename',
    }

    valmap = {
        'no_normalisation' : wutils.SHOW_IF_TRUE,
    }

    cmd = ['mrsi_segment', mrsi]
    cmd += wutils.applyArgStyle('--', argmap=argmap, valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrNiftiMRS('data')
@wutils.fileOrImage('t1', 'spatial_mask')
@wutils.fileOrBasis('basis')
@wutils.fslwrapper
def fsl_dynmrs(data, basis, output, dyn_config, time_variables, **kwargs):
    """Wrapper for the ``fsl_dynmrs`` command.
    The following arguments are currently supported:
    ppmlim, baseline, baseline_order, metab_groups, lorentzian,
    free_shift, inversion_model, t1, report, verbose, overwrite,
    parallel, parallel_workers, no_rescale, save_fit, full_save,
    mean_mrsi, spatial_mask, spatial_index.
    """

    asrt.assertIsNiftiMRS(data)
    asrt.assertIsMRSBasis(basis)

    argmap = {
        'parallel_workers'  : 'parallel-workers',
        'save_fit'          : 'save-fit',
        'full_save'         : 'full-save',
        'spatial_mask'      : 'spatial-mask',
        'spatial_index'     : 'spatial-index',
    }

    valmap = {
        'lorentzian'         : wutils.SHOW_IF_TRUE,
        'free_shift'         : wutils.SHOW_IF_TRUE,
        'inversion_model'    : wutils.SHOW_IF_TRUE,
        'report'             : wutils.SHOW_IF_TRUE,
        'verbose'            : wutils.SHOW_IF_TRUE,
        'overwrite'          : wutils.SHOW_IF_TRUE,
        'no_rescale'         : wutils.SHOW_IF_TRUE,
        'save_fit'           : wutils.SHOW_IF_TRUE,
        'full_save'          : wutils.SHOW_IF_TRUE,
        'mean_mrsi'          : wutils.SHOW_IF_TRUE,
    }

    # convert time_variables input to list
    if isinstance(time_variables, (str, Path)):
        time_variables = [time_variables]

    cmd = ['fsl_dynmrs',
           '--data', data,
           '--basis', basis,
           '--output', output,
           '--dyn_config', dyn_config,
           '--time_variables', *time_variables,
    ]

    cmd += wutils.applyArgStyle('--', argmap=argmap, valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrNiftiMRS('reference')
@wutils.fileOrBasis('basis')
@wutils.fslwrapper
def basis2spec(basis, reference, output, **kwargs):
    """Wrapper for the ``basis2spec`` command.
    The following arguments are currently supported:
    linewidth, ignore.
    """

    asrt.assertIsNiftiMRS(reference)
    asrt.assertIsMRSBasis(basis)

    argmap = {}
    valmap = {}

    cmd = ['basis2spec',
           '--basis', basis,
           '--reference', reference,
           '--output', output,
    ]

    cmd += wutils.applyArgStyle('--', argmap=argmap, valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrText('')
@wutils.fslwrapper
def fmrs_stats(data, output, **kwargs):
    """Wrapper for the ``fmrs_stats`` command.
    The following arguments are currently supported:
    combine, fl_contrasts, mean_contrasts, reference_contrast,
    hl_design, hl_contrasts, hl_covariance, hl_contrast_names,
    hl_ftests, runmode, report, verbose, overwrite, config.
    """

    argmap = {
        'fl_contrasts'       : 'fl-contrasts',
        'mean_contrasts'     : 'mean-contrasts',
        'reference_contrast' : 'reference-contrast',
        'hl_design'          : 'hl-design',
        'hl_contrasts'       : 'hl-contrasts',
        'hl_covariance'      : 'hl-covariance',
        'hl_contrast_names'  : 'hl-contrast-names',
        'hl_ftests'          : 'hl-ftests',
    }

    valmap = {
        'report'            : wutils.SHOW_IF_TRUE,
        'verbose'           : wutils.SHOW_IF_TRUE,
        'overwrite'         : wutils.SHOW_IF_TRUE,
        'combine'           : wutils.EXPAND_LIST,
        'mean-contrasts'    : wutils.EXPAND_LIST,
    }

    # convert data input to list
    if isinstance(data, (str, Path)):
        data = [data]

    cmd = ['fmrs_stats',
           '--data', *data,
           '--output', output,
    ]

    cmd += wutils.applyArgStyle('--', argmap=argmap, valmap=valmap, **kwargs)

    return cmd
