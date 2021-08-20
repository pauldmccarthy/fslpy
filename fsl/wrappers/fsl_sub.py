#!/usr/bin/env python
#
# fsl_sub.py - Wrapper for the fsl_sub command.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :func:`fsl_sub` function, a wrapper for the FSL
`fsl_sub <https://git.fmrib.ox.ac.uk/fsl/fsl_sub>`_ command.
"""


from . import wrapperutils  as wutils


@wutils.fslwrapper
def fsl_sub(*args, **kwargs):
    """Wrapper for the ``fsl_sub`` command.
    """
    cmd  = ['fsl_sub']
    cmd += wutils.applyArgStyle('--', singlechar_args=True, **kwargs)
    cmd += list(args)
    return cmd
