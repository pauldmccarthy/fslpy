#!/usr/bin/env python
#
# run.py - Functions for running shell commands
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides some functions for running shell commands.

.. note:: The functions in this module are only known to work in Unix-like
          environments.

.. autosummary::
   :nosignatures:

   run
   runfsl
   wait
   dryrun
"""


import               sys
import               logging
import               warnings
import               threading
import               contextlib
import               collections
import subprocess as sp
import os.path    as op

import               six

from   fsl.utils.platform import platform as fslplatform
import fsl.utils.fslsub                   as fslsub
import fsl.utils.tempdir                  as tempdir


log = logging.getLogger(__name__)


DRY_RUN = False
"""If ``True``, the :func:`run` function will only log commands, but will not
execute them.
"""


FSL_PREFIX = None
"""Global override for the FSL executable location used by :func:`runfsl`. """


class FSLNotPresent(Exception):
    """Error raised by the :func:`runfsl` function when ``$FSLDIR`` cannot
    be found.
    """
    pass


@contextlib.contextmanager
def dryrun(*args):
    """Context manager which causes all calls to :func:`run` to be logged but
    not executed. See the :data:`DRY_RUN` flag.

    The returned standard output will be equal to ``' '.join(args)``.
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


real_stdout = sys.stdout
def _forwardStream(in_, *outs):
    """Creates and starts a daemon thread which forwards the given input stream
    to one or more output streams. Used by the :func:`run` function to redirect
    a command's standard output/error streams to more than one destination.

    It is necessary to read the process stdout/ stderr on separate threads to
    avoid deadlocks.

    :arg in_:  Input stream
    :arg outs: Output stream(s)
    :returns:  The thread that has been started.
    """

    # not all file-likes have a mode attribute -
    # if not present, assume a string stream
    omodes = [getattr(o, 'mode', 'w') for o in outs]

    def realForward():
        for line in iter(in_.readline, b''):
            for i, o in enumerate(outs):
                if 'b' in omodes[i]: o.write(line)
                else:                o.write(line.decode('utf-8'))

    t = threading.Thread(target=realForward)
    t.daemon = True
    t.start()
    return t


def run(*args, **kwargs):
    """Call a command and return its output. You can pass the command and
    arguments as a single string, or as a regular or unpacked sequence.

    The command can be run on a cluster by using the ``submit`` keyword
    argument.

    An exception is raised if the command returns a non-zero exit code, unless
    the ``ret`` option is set to ``True``.

    :arg stdout:   Must be passed as a keyword argument. Defaults to ``True``.
                   If ``True``, standard output is captured and returned.
                   Ignored if ``submit`` is specified.

    :arg stderr:   Must be passed as a keyword argument. Defaults to ``False``.
                   If ``True``, standard error is captured and returned.
                   Ignored if ``submit`` is specified.

    :arg exitcode: Must be passed as a keyword argument. Defaults to ``False``.
                   If ``True``, and the command's return code is non-0, an
                   exception is not raised.  Ignored if ``submit`` is
                   specified.

    :arg err:      Deprecated - use ``stderr`` instead.

    :arg ret:      Deprecated - use ``exitcode`` instead.

    :arg submit:   Must be passed as a keyword argument. Defaults to ``None``.
                   If ``True``, the command is submitted as a cluster job via
                   the :func:`.fslsub.submit` function.  May also be a
                   dictionary containing arguments to that function.

    :arg log:      Must be passed as a keyword argument.  An optional ``dict``
                   which may be used to redirect the command's standard output
                   and error. The following keys are recognised:

                     - tee:    If ``True``, the command's standard output/error
                               streams are forwarded to this processes streams.

                     - stdout: Optional file-like object to which the command's
                               standard output stream can be forwarded.

                     - stderr: Optional file-like object to which the command's
                               standard error stream can be forwarded.

                     - cmd:    If ``True``, the command itself is logged to the
                               standard output stream(s).

    :returns:      If ``submit`` is provided, the return value of
                   :func:`.fslsub` is returned. Otherwise returns a single
                   value or a tuple, based on the based on the ``stdout``,
                   ``stderr``, and ``exitcode`` arguments.
    """

    if 'err' in kwargs:
        warnings.warn('err is deprecated and will be removed '
                      'in fslpy 2.0.0 - use stderr instead',
                      DeprecationWarning)
        kwargs['stderr'] = kwargs.get('stderr', kwargs['err'])
    if 'ret' in kwargs:
        warnings.warn('ret is deprecated and will be removed '
                      'in fslpy 2.0.0 - use exitcode instead',
                      DeprecationWarning)
        kwargs['exitcode'] = kwargs.get('exitcode', kwargs['ret'])

    returnStdout   = kwargs.get('stdout',   True)
    returnStderr   = kwargs.get('stderr',   False)
    returnExitcode = kwargs.get('exitcode', False)
    submit         = kwargs.get('submit',   {})
    log            = kwargs.get('log',      {})
    tee            = log   .get('tee',      False)
    logStdout      = log   .get('stdout',   None)
    logStderr      = log   .get('stderr',   None)
    logCmd         = log   .get('cmd',      False)
    args           = _prepareArgs(args)

    if not bool(submit):
        submit = None

    if submit is not None:
        returnStdout   = False
        returnStderr   = False
        returnExitcode = False

        if submit is True:
            submit = dict()

    if submit is not None and not isinstance(submit, collections.Mapping):
        raise ValueError('submit must be a mapping containing '
                         'options for fsl.utils.fslsub.submit')

    if DRY_RUN:
        return _dryrun(
            submit, returnStdout, returnStderr, returnExitcode, *args)

    # submit - delegate to fslsub
    if submit is not None:
        return fslsub.submit(' '.join(args), **submit)

    # Run directly - delegate to _realrun
    stdout, stderr, exitcode = _realrun(
        tee, logStdout, logStderr, logCmd, *args)

    if not returnExitcode and (exitcode != 0):
        raise RuntimeError('{} returned non-zero exit code: {}'.format(
            args[0], exitcode))

    results = []
    if returnStdout:   results.append(stdout)
    if returnStderr:   results.append(stderr)
    if returnExitcode: results.append(exitcode)

    if len(results) == 1: return results[0]
    else:                 return tuple(results)



def _dryrun(submit, returnStdout, returnStderr, returnExitcode, *args):
    """Used by the :func:`run` function when the :attr:`DRY_RUN` flag is
    active.
    """

    if submit:
        return ('0',)

    results = []
    stderr  = ''
    stdout  = ' '.join(args)

    if returnStdout:   results.append(stdout)
    if returnStderr:   results.append(stderr)
    if returnExitcode: results.append(0)

    if len(results) == 1: return results[0]
    else:                 return tuple(results)


def _realrun(tee, logStdout, logStderr, logCmd, *args):
    """Used by :func:`run`. Runs the given command and manages its standard
    output and error streams.

    :arg tee:       If ``True``, the command's standard output and error
                    streams are forwarded to this process' standard output/
                    error.

    :arg logStdout: Optional file-like object to which the command's standard
                    output stream can be forwarded.

    :arg logStderr: Optional file-like object to which the command's standard
                    error stream can be forwarded.

    :arg logCmd:    If ``True``, the command itself is logged to the standard
                    output stream(s).

    :arg args:      Command to run

    :returns:       A tuple containing:
                      - the command's standard output as a string.
                      - the command's standard error as a string.
                      - the command's exit code.
    """
    proc = sp.Popen(args, stdout=sp.PIPE, stderr=sp.PIPE)
    with tempdir.tempdir(changeto=False) as td:

        # We always direct the command's stdout/
        # stderr to two temporary files
        stdoutf = op.join(td, 'stdout')
        stderrf = op.join(td, 'stderr')

        with open(stdoutf, 'wb') as stdout, \
             open(stderrf, 'wb') as stderr:  # noqa

            outstreams = [stdout]
            errstreams = [stderr]

            # if tee, we duplicate the command's
            # stdout/stderr to this process'
            # stdout/stderr
            if tee:
                outstreams.append(sys.stdout)
                errstreams.append(sys.stderr)

            # And we also duplicate to caller-
            # provided streams if they're given.
            if logStdout is not None: outstreams.append(logStdout)
            if logStderr is not None: errstreams.append(logStderr)

            # log the command to
            # stdout if requested
            if logCmd:
                cmd = ' '.join(args) + '\n'
                for o in outstreams:
                    if 'b' in getattr(o, 'mode', 'w'):
                        o.write(cmd.encode('utf-8'))
                    else:
                        o.write(cmd)

            stdoutt = _forwardStream(proc.stdout, *outstreams)
            stderrt = _forwardStream(proc.stderr, *errstreams)

            # Wait until the forwarding threads
            # have finished cleanly, and the
            # command has terminated.
            stdoutt.join()
            stderrt.join()
            proc.communicate()

        # Read in the command's stdout/stderr
        with open(stdoutf, 'rb') as f: stdout = f.read()
        with open(stderrf, 'rb') as f: stderr = f.read()

    exitcode = proc.returncode
    stdout   = stdout.decode('utf-8')
    stderr   = stderr.decode('utf-8')

    return stdout, stderr, exitcode


def runfsl(*args, **kwargs):
    """Call a FSL command and return its output. This function simply prepends
    ``$FSLDIR/bin/`` to the command before passing it to :func:`run`.
    """

    prefix = None

    if FSL_PREFIX is not None:
        prefix = FSL_PREFIX
    elif fslplatform.fsldevdir is not None:
        prefix = op.join(fslplatform.fsldevdir, 'bin')
    elif fslplatform.fsldir is not None:
        prefix = op.join(fslplatform.fsldir, 'bin')
    else:
        raise FSLNotPresent('$FSLDIR is not set - FSL cannot be found!')

    args    = _prepareArgs(args)
    args[0] = op.join(prefix, args[0])

    return run(*args, **kwargs)


def wait(job_ids):
    """Proxy for :func:`.fslsub.wait`. """
    return fslsub.wait(job_ids)
