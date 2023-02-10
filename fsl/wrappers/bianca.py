#!/usr/bin/env python
#
# bianca.py - Wrapper function for BIANCA.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains wrapper functions for the FSL `BIANCA
<https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/BIANCA/>`_ commands.
"""


import fsl.wrappers.wrapperutils as wutils


@wutils.fslwrapper
def bianca(singlefile,
           querysubjectnum=None,
           brainmaskfeaturenum=None,
           **kwargs):
    """Wrapper function for the FSL ``bianca`` command. """

    valmap = {
        'listbysubject' : wutils.SHOW_IF_TRUE,
        'patch3d'       : wutils.SHOW_IF_TRUE,
        'transposefile' : wutils.SHOW_IF_TRUE,
        'debug'         : wutils.SHOW_IF_TRUE,
        'v'             : wutils.SHOW_IF_TRUE,
    }

    cmd = ['bianca', '--singlefile', singlefile]
    if querysubjectnum is not None:
        cmd += ['--querysubjectnum', str(querysubjectnum)]
    if brainmaskfeaturenum is not None:
        cmd += ['--brainmaskfeaturenum', str(brainmaskfeaturenum)]

    cmd += wutils.applyArgStyle('--', charstyle='-', valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrImage('bianca_output_map', 'mask')
@wutils.fslwrapper
def bianca_cluster_stats(bianca_output_map,
                         threshold,
                         min_cluster_size,
                         mask=None):
    """Wrapper function for the FSL ``bianca_cluster_stats`` command. """

    cmd = ['bianca_cluster_stats',
           bianca_output_map,
           str(threshold),
           str(min_cluster_size)]
    if mask is not None:
        cmd += [mask]
    return cmd



@wutils.fileOrImage('lesionmask', 'manualmask')
@wutils.fslwrapper
def bianca_overlap_measures(lesionmask,
                            threshold,
                            manualmask,
                            saveoutput=True):
    """Wrapper function for the FSL ``bianca_overlap_measures`` command. """
    cmd = ['bianca_overlap_measures', lesionmask, str(threshold), manualmask]
    if saveoutput: cmd.append('1')
    else:          cmd.append('0')
    return cmd


@wutils.fileOrImage('wmh_map', 'vent_mask')
@wutils.fslwrapper
def bianca_perivent_deep(wmh_map,
                         vent_mask,
                         minclustersize,
                         outputdir,
                         do_stats=1):
    """Wrapper function for the FSL ``bianca_perivent_deep`` command. """
    return ['bianca_perivent_deep', wmh_map, vent_mask,
            str(minclustersize), str(do_stats), outputdir]


@wutils.fileOrImage('struc', 'csf_pve', 'mni2struc')
@wutils.fslwrapper
def make_bianca_mask(struc, csf_pve, mni2struc, keep_files=False):
    """Wrapper function for the FSL ``make_bianca_mask`` command. """
    cmd = ['make_bianca_mask', struc, csf_pve, mni2struc]
    if keep_files: cmd.append('1')
    else:          cmd.append('0')
    return cmd
