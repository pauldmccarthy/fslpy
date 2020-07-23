#!/usr/bin/env python
#
# misc.py - Wrappers for miscellaneous FSL command-line tools.
#
# Author: Sean Fitzgibbon <sean.fitzgibbon@ndcn.ox.ac.uk>
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains wrapper functions for various `FSL
<https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/>`_ command-line tools.
"""


import fsl.utils.assertions as asrt
from . import wrapperutils  as wutils


@wutils.fileOrImage('input', 'output')
@wutils.fslwrapper
def fslreorient2std(input, output=None):
    """Wrapper for the ``fsreorient2std`` tool."""

    asrt.assertIsNifti(input)

    cmd = ['fslreorient2std', input]

    if output is not None:
        cmd.append(output)

    return cmd


@wutils.fileOrImage('input', 'output')
@wutils.fslwrapper
def fslroi(input, output, *args):
    """Wrapper for the ``fslroi`` tool."""

    asrt.assertIsNifti(input)

    cmd = ['fslroi', input, output] + [str(a) for a in args]

    return cmd


@wutils.fileOrImage('input', 'input2')
@wutils.fslwrapper
def slicer(input, input2=None, **kwargs):
    """Wrapper for the ``slicer`` command. """

    cmd = ['slicer', input]

    if input2 is not None:
        cmd.append(input2)

    # slicer output options must be
    # applied after other options
    outopts = ['x', 'y', 'z', 'a', 'A', 'S']
    outargs = { k : kwargs.pop(k) for k in outopts if k in kwargs}

    cmd = cmd + wutils.applyArgStyle('-', **kwargs) + \
                wutils.applyArgStyle('-', **outargs)

    return cmd


@wutils.fileOrImage('input', 'cope', 'oindex', 'othresh', 'olmaxim', 'osize',
                    'omax', 'omean', 'opvals', 'stdvol', 'warpvol',
                    'empiricalNull')
@wutils.fileOrArray('xfm')
@wutils.fslwrapper
def cluster(input, thresh, **kwargs):
    """Wrapper for the ``cluster`` command. """

    valmap = {
        'fractional'     : wutils.SHOW_IF_TRUE,
        'mm'             : wutils.SHOW_IF_TRUE,
        'min'            : wutils.SHOW_IF_TRUE,
        'no_table'       : wutils.SHOW_IF_TRUE,
        'minclustersize' : wutils.SHOW_IF_TRUE,
        'verbose'        : wutils.SHOW_IF_TRUE,
        'voxthresh'      : wutils.SHOW_IF_TRUE,
        'voxuncthresh'   : wutils.SHOW_IF_TRUE,
    }

    cmd  = ['cluster', '--in={}'.format(input), '--thresh={}'.format(thresh)]
    cmd += wutils.applyArgStyle('--=', valmap=valmap, **kwargs)

    return cmd

@wutils.fileOrArray('out', 'init')
@wutils.fslwrapper
def gps(out, ndir, **kwargs):
    """Wrapper of the ``gps`` command

    Usage example to get 128 gradient orientations on the whole sphere::

        from fsl.wrappers import gps, LOAD
        bvecs = gps(LOAD, 128, optws=True)['out']
    """
    valmap = {name: wutils.SHOW_IF_TRUE for name in [
        'optws', 'report', 'verbose'
    ]}

    cmd = ['gps', f'--ndir={ndir}', f'--out={out}']
    cmd += wutils.applyArgStyle('--=', valmap=valmap, **kwargs)

    return cmd
