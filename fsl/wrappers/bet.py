#!/usr/bin/env python
#
# bet.py - Wrapper for the FSL bet command.
#
# Author: Sean Fitzgibbon <sean.fitzgibbon@ndcn.ox.ac.uk>
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :func:`bet` function, a wrapper for the FSL
`BET <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/BET>`_ command.
"""


import fsl.utils.assertions as asrt
from . import wrapperutils  as wutils


@wutils.fileOrImage('input', 'output')
@wutils.fslwrapper
def bet(input, output, **kwargs):
    """Wrapper for the ``bet`` command.

    :arg mask:          Generate a brain mask
    :arg seg:           If ``False``, a brain extracted image is not
                        generated.
    :arg robust:        Robust brain centre estimation
    :arg fracintensity: Fractional intensity threshold

    Refer to the ``bet`` command-line help for details on all arguments.
    """

    asrt.assertIsNifti(input)

    argmap = {
        'mask'          : 'm',
        'robust'        : 'R',
        'fracintensity' : 'f',
        'seg'           : 'n',
    }

    valmap = {
        'm' : wutils.SHOW_IF_TRUE,
        'R' : wutils.SHOW_IF_TRUE,
        'n' : wutils.HIDE_IF_TRUE,
    }

    cmd  = ['bet', input, output]
    cmd += wutils.applyArgStyle('-', argmap=argmap, valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrImage('input', 'output')
@wutils.fileOrArray('matrix')
@wutils.fslwrapper
def robustfov(input, output=None, **kwargs):
    """Wrapper for the ``robustfov`` command. """
    asrt.assertIsNifti(input)

    if output is not None:
        kwargs.update({'output' : output})

    argmap = {
        'output' : 'r',
        'matrix' : 'm'
    }

    cmd  = ['robustfov', '-i', input]
    cmd += wutils.applyArgStyle('-', argmap=argmap, **kwargs)

    return cmd
