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
import               contextlib
import subprocess as sp
import os.path    as op

import               six

from fsl.utils.platform import platform as fslplatform


log = logging.getLogger(__name__)


DRY_RUN = False
"""If ``True``, the :func:`run` function will only log commands, but will not
execute them.
"""


@contextlib.contextmanager
def dryrun(*args):
    """Context manager which causes all calls to :func:`run` to be logged but
    not executed. See the :data:`DRY_RUN` flag.
    """
    global DRY_RUN

    oldval  = DRY_RUN
    DRY_RUN = True

    try:
        yield
    finally:
        DRY_RUN = oldval


def _prepareArgs(args):
    """Used by the :func:`run` function. Ensures that the given arguments is a
    list of strings.
    """

    if len(args) == 1:

        # Argument was a command string
        if isinstance(args[0], six.string_types):
            args = args[0].split()

        # Argument was an unpacked sequence
        else:
            args = args[0]

    return list(args)


def run(*args):
    """Call a command and return its output. You can pass the command and
    arguments as a single string, or as a regular or unpacked sequence.
    """

    args = _prepareArgs(args)

    if DRY_RUN:
        log.debug('dryrun: {}'.format(' '.join(args)))
    else:
        log.debug('run: {}'.format(' '.join(args)))

    if DRY_RUN:
        result = '<dryrun>'
    else:
        result = sp.check_output(args).decode('utf-8').strip()

    log.debug('result: {}'.format(result))

    return result


def runfsl(*args):
    """Call a FSL command and return its output. This function simply prepends
    ``$FSLDIR/bin/`` to the command before passing it to :func:`run`.
    """

    if fslplatform.fsldir is None:
        raise RuntimeError('$FSLDIR is not set - FSL cannot be found!')

    args    = _prepareArgs(args)
    args[0] = op.join(fslplatform.fsldir, 'bin', args[0])

    return run(*args)


def fslsub(*args):
    """Not implemented yet. """
    raise NotImplementedError('')
