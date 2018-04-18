#!/usr/bin/env python
#
# callfsl.py - The callFSL function.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Deprecated - use :mod:`fsl.utils.run` instead.

This module provides the :func:`callFSL` function, which can be
used to call a FSL command, and retrieve the result.
"""


import               logging
import subprocess as sp
import os.path    as op

import               deprecation

from fsl.utils.platform import platform as fslplatform


log = logging.getLogger(__name__)


@deprecation.deprecated(deprecated_in='1.8.0',
                        removed_in='2.0.0',
                        details='Use fsl.utils.run.runfsl instead')
def callFSL(*args):
    """Call a FSL command and return the result.

    You can pass the command and arguments as a single string, or as a
    list/tuple.
    """

    if fslplatform.fsldir is None:
        raise RuntimeError('FSL cannot be found!')

    # If we've been given a single argument,
    # assume it is a string containing the
    # command and its arguments. Otherwise,
    # assume it is a sequence containing
    # separate command and arguments.
    if len(args) == 1:
        args = args[0].split()

    args    = list(args)
    args[0] = op.join(fslplatform.fsldir, 'bin', args[0])

    log.debug('callfsl: {}'.format(' '.join(args)))

    result = sp.check_output(args).decode('utf-8')

    log.debug('result: {}'.format(result))

    return result
