#!/usr/bin/env python
#
# bet.py - Wrapper for the FSL bet command.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :func:`bet` function, a wrapper for the FSL
`BET <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/BET>`_ command.
"""


import fsl.utils.assertions as asrt
import fsl.utils.run        as run
from . import wrapperutils  as wutils


@wutils.fileOrImage('input', 'output')
def bet(input, output, **kwargs):
    """Delete non-brain tissue from an image of the whole head.

    :arg input:         Image to be brain-extracted
    :arg output:        Output image
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
    cmd += wutils.applyArgStyle('-', argmap, valmap, **kwargs)

    return run.runfsl(*cmd)


@wutils.fileOrImage('input', 'output')
@wutils.fileOrArray('matrix')
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

    return run.runfsl(cmd)