#!/usr/bin/env python
#
# mmorf.py - Wrapper for mmorf.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides wrapper functions for the FSL :fsldocs:`MMORF
<registration/mmorf.html>` registration utility.
"""


from . import wrapperutils as wutils


@wutils.fslwrapper
def mmorf(config=None, **kwargs):
    """Wrapper for the ``mmorf`` command. """

    cmd = ['mmorf']

    if config is not None:
        cmd += ['--config', config]

    cmd += wutils.applyArgStyle('--', **kwargs)

    return cmd
