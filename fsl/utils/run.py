#!/usr/bin/env python
#
# run.py - Functions for running shell commands
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides some functions for running shell commands.

.. autosummary::
   :nosignatures:

   run
   runfsl
   fslsub
"""


import               logging
import subprocess as sp
import os.path    as op

from fsl.utils.platform import platform as fslplatform


log = logging.getLogger(__name__)


def run(*args):
    """Call a command and return its output.  You can pass the command and
    arguments as a single string, or as an unpacked sequence.
    """

    # If we've been given a single argument,
    # assume it is a string containing the
    # command and its arguments. Otherwise,
    # assume it is a sequence containing
    # separate command and arguments.
    if len(args) == 1:
        args = args[0].split()

    args = list(args)

    log.debug('run: {}'.format(' '.join(args)))

    result = sp.check_output(args).decode('utf-8').strip()

    log.debug('result: {}'.format(result))

    return result


def runfsl(*args):
    """Call a FSL command and return its output. This function simply prepends
    $FSLDIR/bin/ to the command before passing it to :func:`run`.
    """

    if fslplatform.fsldir is None:
        raise RuntimeError('$FSLDIR is not set - FSL cannot be found!')

    if len(args) == 1:
        args = args[0].split()

    args    = list(args)
    args[0] = op.join(fslplatform.fsldir, 'bin', args[0])

    return run(*args)


def fslsub(*args):
    """Not implemented yet. """
    raise NotImplementedError('')
