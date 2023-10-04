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


@wutils.fileOrImage('input')
@wutils.fslwrapper
def fslorient(input, **kwargs):
    """Wrapper for the ``fslorient`` tool."""

    asrt.assertIsNifti(input)

    valmap = {
        'getorient'                : wutils.SHOW_IF_TRUE,
        'getsform'                 : wutils.SHOW_IF_TRUE,
        'getqform'                 : wutils.SHOW_IF_TRUE,
        'getsformcode'             : wutils.SHOW_IF_TRUE,
        'getqformcode'             : wutils.SHOW_IF_TRUE,
        'copysform2qform'          : wutils.SHOW_IF_TRUE,
        'copyqform2sform'          : wutils.SHOW_IF_TRUE,
        'deleteorient'             : wutils.SHOW_IF_TRUE,
        'forceradiological'        : wutils.SHOW_IF_TRUE,
        'forceneurological'        : wutils.SHOW_IF_TRUE,
        'swaporient'               : wutils.SHOW_IF_TRUE,
    }

    cmd = ['fslorient']
    cmd += wutils.applyArgStyle('-', valsep=' ', valmap=valmap, **kwargs)
    cmd += [input]

    return cmd


@wutils.fileOrImage('input', 'output')
@wutils.fslwrapper
def fslswapdim(input, a, b, c, output=None):
    """Wrapper for the ``fslswapdim`` tool."""

    asrt.assertIsNifti(input)

    cmd = ['fslswapdim', input, a, b, c]
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
