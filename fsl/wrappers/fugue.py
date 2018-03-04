#!/usr/bin/env python
#
# fugue.py - Wrappers for fugue/field map tools.
#
# Author: Sean Fitzgibbon <sean.fitzgibbon@ndcn.ox.ac.uk>
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains wrappers for the FSL `FUGUE
<https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FUGUE>`_ tools, for EPI field map
processing and distortion correction.
"""


from . import wrapperutils as wutils


@wutils.fileOrImage('in', 'unwarp', 'warp', 'phasemap', 'savefmap',
                    'loadfmap', 'saveshift', 'loadshift', 'mask')
@wutils.fslwrapper
def fugue(input=None, **kwargs):
    """Wrapper for the ``fugue`` command."""

    argmap = {
        'input' : 'in'
    }

    valmap = {
        'dwelltoasym' : wutils.SHOW_IF_TRUE,
        'median'      : wutils.SHOW_IF_TRUE,
        'despike'     : wutils.SHOW_IF_TRUE,
        'nofill'      : wutils.SHOW_IF_TRUE,
        'noextend'    : wutils.SHOW_IF_TRUE,
        'pava'        : wutils.SHOW_IF_TRUE,
        'phaseconj'   : wutils.SHOW_IF_TRUE,
        'icorr'       : wutils.SHOW_IF_TRUE,
        'icorronly'   : wutils.SHOW_IF_TRUE,
        'unmaskfmap'  : wutils.SHOW_IF_TRUE,
        'unmaskshift' : wutils.SHOW_IF_TRUE,
        'nokspace'    : wutils.SHOW_IF_TRUE,
        'nocheck'     : wutils.SHOW_IF_TRUE,
        'verbose'     : wutils.SHOW_IF_TRUE,
    }

    kwargs.update({'input' : input})

    cmd = ['fugue'] + wutils.applyArgStyle('--=',
                                           argmap=argmap,
                                           valmap=valmap,
                                           **kwargs)

    return cmd


@wutils.fileOrImage('input', 'mask', 'sigloss')
@wutils.fslwrapper
def sigloss(input, sigloss, **kwargs):
    """Wrapper for the ``sigloss`` command."""

    valmap = {'verbose' : wutils.SHOW_IF_TRUE}

    cmd  = ['sigloss', '--in', input, '--sigloss', sigloss]
    cmd += wutils.applyArgStyle('--', valmap=valmap, **kwargs)

    return cmd
