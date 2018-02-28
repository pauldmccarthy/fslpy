#!/usr/bin/env python
#
# fugue.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""
"""


import fsl.utils.run as run


def fugue(**kwargs):
    """FMRIB's Utility for Geometric Unwarping of EPIs."""

    cmd = "fugue"

    if kwargs.pop('unmaskshift', False):
        cmd += " --unmaskshift"
    if kwargs.pop('despike', False):
        cmd += " --despike"
    if kwargs.pop('unmaskfmap', False):
        cmd += " --unmaskfmap"

    cmd += ' '.join(['--{}={}'.format(k, v) for k, v in kwargs.items()])

    return run.runfsl(cmd)


def sigloss(input, output, te=None, slicedir=None, mask=None):
    """Estimate signal loss from a field map (in rad/s)."""
    cmd = "sigloss -i {0} -s {1}".format(input, output)

    if te is not None:
        cmd += " --te={0}".format(te)
    if slicedir is not None:
        cmd += " --slicedir={0}".format(slicedir)
    if mask is not None:
        cmd += " --mask={0}".format(mask)

    return run.runfsl(cmd)
