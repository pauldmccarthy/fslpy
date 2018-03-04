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
def fslroi(input, output, xmin=None, xsize=None, ymin=None, ysize=None,
           zmin=None, zsize=None, tmin=None, tsize=None):
    """Wrapper for the ``fslroi`` tool."""
    assert ((tmin is not None and tsize is not None) or
            (xmin is not None and xsize is not None and
             ymin is not None and ysize is not None and
             zmin is not None and zsize is not None)), \
        "either time min/size or x/y/z min/size must be provided"

    cmd = ['fslroi', input, output]

    if xmin is not None:
        cmd += [str(v) for v in [xmin, xsize, ymin, ysize, zmin, zsize]]
    if tmin is not None:
        cmd += [str(tmin), str(tsize)]

    return cmd


@wutils.fileOrImage('input', 'input2')
@wutils.fslwrapper
def slicer(input, input2=None, label=None, lut=None, intensity=None,
           edgethreshold=None, x=None, y=None, z=None):
    """Wrapper for the ``slicer`` command. """

    cmd = "slicer {0}".format(input)

    if input2 is not None:
        cmd += " {0}".format(input2)
    if label is not None:
        cmd += " -L {0}".format(label)
    if lut is not None:
        cmd += " -l {0}".format(lut)
    if intensity is not None:
        cmd += " -i {0} {1}".format(intensity[0], intensity[1])
    if edgethreshold is not None:
        cmd += " -e {0}".format(edgethreshold)
    if x is not None:
        cmd += " -x {0} {1}".format(x[0], x[1])
    if y is not None:
        cmd += " -y {0} {1}".format(y[0], y[1])
    if z is not None:
        cmd += " -z {0} {1}".format(z[0], z[1])

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
