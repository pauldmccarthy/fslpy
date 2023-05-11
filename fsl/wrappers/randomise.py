#!/usr/bin/env python
#
# randomise.py - Randomise wrapper functions.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides wrapper functions for the FSL `randomise
<https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/Randomise>`_ tool, used for
calculating non-parametric statistics.
"""


import fsl.wrappers.wrapperutils as wutils


@wutils.fslwrapper
def randomise(input, out_root, **kwargs):
    """Wrapper for the ``randomise`` command.

    The ``-1`` option can be addedd by passing ``one=True``.
    """

    valmap = {
        'D'             : wutils.SHOW_IF_TRUE,
        '1'             : wutils.SHOW_IF_TRUE,
        'q'             : wutils.SHOW_IF_TRUE,
        'Q'             : wutils.SHOW_IF_TRUE,
        'x'             : wutils.SHOW_IF_TRUE,
        'fonly'         : wutils.SHOW_IF_TRUE,
        'T'             : wutils.SHOW_IF_TRUE,
        'T2'            : wutils.SHOW_IF_TRUE,
        'quiet'         : wutils.SHOW_IF_TRUE,
        'twopass'       : wutils.SHOW_IF_TRUE,
        'R'             : wutils.SHOW_IF_TRUE,
        'uncorrp'       : wutils.SHOW_IF_TRUE,
        'P'             : wutils.SHOW_IF_TRUE,
        'N'             : wutils.SHOW_IF_TRUE,
        'norcmask'      : wutils.SHOW_IF_TRUE,
        'permuteBlocks' : wutils.SHOW_IF_TRUE,
        'glm_output'    : wutils.SHOW_IF_TRUE,
        'film'          : wutils.SHOW_IF_TRUE,
    }
    argmap = {
        'one' : '1',
    }

    cmd  = ['randomise', '-i', input, '-o', out_root]
    cmd += wutils.applyArgStyle('--=', valmap=valmap, argmap=argmap, **kwargs)

    return cmd
