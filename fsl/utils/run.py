#!/usr/bin/env python
#
# run.py - Functions for running shell commands
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
# Author: Michiel Cottaar <michiel.cottaar@ndcn.ox.ac.uk>
#
"""This module provides some functions for running shell commands.

.. note:: The functions in this module are only known to work in Unix-like
          environments.

.. autosummary::
   :nosignatures:

   run
   runfsl
   dryrun
   hold
"""


import                    sys
import                    shlex
import                    logging
import                    threading
import                    contextlib
import collections.abc as abc
import subprocess      as sp
import os.path         as op
import                    os

from   fsl.utils.platform import platform as fslplatform
import fsl.utils.fslsub                   as fslsub
import fsl.utils.tempdir                  as tempdir
import fsl.utils.path                     as fslpath

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


def prepareArgs(args):
    """Used by the :func:`run` function. Ensures that the given arguments is a
    list of strings.
    """

    if len(args) == 1:

        # Argument was a command string
        if isinstance(args[0], str):
            args = shlex.split(args[0])

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
    the ``exitcode`` option is set to ``True``.

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

    :arg submit:   Must be passed as a keyword argument. Defaults to ``None``.
                   If ``True``, the command is submitted as a cluster job via
                   the :func:`.fslsub.submit` function.  May also be a
                   dictionary containing arguments to that function.

    :arg cmdonly:  Defaults to ``False``. If ``True``, the command is not
                   executed, but rather is returned directly, as a list of
                   arguments.

    :arg log:      Must be passed as a keyword argument.  An optional ``dict``
                   which may be used to redirect the command's standard output
                   and error. The following keys are recognised:

                     - tee:    If ``True``, the command's standard output/error
                               streams are forwarded to this processes streams.

                     - stdout: Optional file-like object to which the command's
                               standard output stream can be forwarded.

                     - stderr: Optional file-like object to which the command's
                               standard error stream can be forwarded.

                     - cmd:    Optional file-like object to which the command
                               itself is logged.

    All other keyword arguments are passed through to the ``subprocess.Popen``
    object (via :func:`_realrun`), unless ``submit=True``, in which case they
    are passed through to the :func:`.fslsub.submit` function.

    :returns:      If ``submit`` is provided, the return value of
                   :func:`.fslsub` is returned. Otherwise returns a single
                   value or a tuple, based on the based on the ``stdout``,
                   ``stderr``, and ``exitcode`` arguments.
    """

    returnStdout   = kwargs.pop('stdout',   True)
    returnStderr   = kwargs.pop('stderr',   False)
    returnExitcode = kwargs.pop('exitcode', False)
    submit         = kwargs.pop('submit',   {})
    cmdonly        = kwargs.pop('cmdonly',  False)
    log            = kwargs.pop('log',      None)
    args           = prepareArgs(args)

    if log is None:
        log = {}

    tee       = log.get('tee',    False)
    logStdout = log.get('stdout', None)
    logStderr = log.get('stderr', None)
    logCmd    = log.get('cmd',    None)

    if not bool(submit):
        submit = None

    if submit is not None:
        returnStdout   = False
        returnStderr   = False
        returnExitcode = False

        if submit is True:
            submit = dict()

    if submit is not None and not isinstance(submit, abc.Mapping):
        raise ValueError('submit must be a mapping containing '
                         'options for fsl.utils.fslsub.submit')

    if cmdonly:
        return args

    if DRY_RUN:
        return _dryrun(
            submit, returnStdout, returnStderr, returnExitcode, *args)

    # submit - delegate to fslsub
    if submit is not None:
        return fslsub.submit(' '.join(args), **submit, **kwargs)

    # Run directly - delegate to _realrun
    stdout, stderr, exitcode = _realrun(
        tee, logStdout, logStderr, logCmd, *args, **kwargs)

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


def _realrun(tee, logStdout, logStderr, logCmd, *args, **kwargs):
    """Used by :func:`run`. Runs the given command and manages its standard
    output and error streams.

    :arg tee:       If ``True``, the command's standard output and error
                    streams are forwarded to this process' standard output/
                    error.

    :arg logStdout: Optional file-like object to which the command's standard
                    output stream can be forwarded.

    :arg logStderr: Optional file-like object to which the command's standard
                    error stream can be forwarded.

    :arg logCmd:    Optional file-like object to which the command itself is
                    logged.

    :arg args:      Command to run

    :arg kwargs:    Passed through to the ``subprocess.Popen`` object.

    :returns:       A tuple containing:
                      - the command's standard output as a string.
                      - the command's standard error as a string.
                      - the command's exit code.
    """
    if fslplatform.fslwsl:
        # On Windows this prevents opening of a popup window
        startupinfo = sp.STARTUPINFO()
        startupinfo.dwFlags |= sp.STARTF_USESHOWWINDOW
        kwargs["startupinfo"] = startupinfo

    proc = sp.Popen(args, stdout=sp.PIPE, stderr=sp.PIPE, **kwargs)
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

            # log the command if requested
            if logCmd is not None:
                cmd = ' '.join(args) + '\n'
                if 'b' in getattr(logCmd, 'mode', 'w'):
                    logCmd.write(cmd.encode('utf-8'))
                else:
                    logCmd.write(cmd)

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
    """Call a FSL command and return its output.

      This function searches for the command in the following
      locations (ordered by priority):

      1. ``FSL_PREFIX``
      2. ``$FSLDEVDIR/bin``
      3. ``$FSLDIR/bin``

      If found, the full path to the command is then passed to :func:`run`.
    """
    prefixes = []

    if FSL_PREFIX is not None:
        prefixes.append(FSL_PREFIX)
    if fslplatform.fsldevdir is not None:
        prefixes.append(op.join(fslplatform.fsldevdir, 'bin'))
    if fslplatform.fsldir is not None:
        prefixes.append(op.join(fslplatform.fsldir, 'bin'))

    if not prefixes:
        raise FSLNotPresent('$FSLDIR is not set - FSL cannot be found!')

    args = prepareArgs(args)
    for prefix in prefixes:
        cmdpath = op.join(prefix, args[0])
        if fslplatform.fslwsl:
            wslargs = wslcmd(cmdpath, *args)
            if wslargs is not None:
                args = wslargs
                break
        elif op.isfile(cmdpath):
            args[0] = cmdpath
            break

    # error if the command cannot
    # be found in a FSL directory
    else:
        raise FileNotFoundError('FSL tool {} not found (checked {})'.format(
            args[0], ', '.join(prefixes)))

    return run(*args, **kwargs)


def wslcmd(cmdpath, *args):
    """
    Convert a command + arguments into an equivalent set of arguments that will run the command
    under Windows Subsystem for Linux

    :param cmdpath: Fully qualified path to the command. This is essentially a WSL path not a Windows
                    one since FSLDIR is specified as a WSL path, however it may have backslashes
                    as path separators due to previous use of ``os.path.join``
    :param args: Sequence of command arguments (the first of which is the unqualified command name)

    :return: If ``cmdpath`` exists and is executable in WSL, return a sequence of command arguments
             which when executed will run the command in WSL. Windows paths in the argument list will
             be converted to WSL paths. If ``cmdpath`` was not executable in WSL, returns None
    """
    # Check if command exists in WSL (remembering that the command path may include FSLDIR which
    # is a Windows path)
    cmdpath = fslpath.wslpath(cmdpath)
    _stdout, _stderr, retcode = _realrun(False, None, None, None, "wsl", "test", "-x", cmdpath)
    if retcode == 0:
        # Form a new argument list and convert any Windows paths in it into WSL paths
        wslargs = [fslpath.wslpath(arg) for arg in args]
        wslargs[0] = cmdpath
        local_fsldir = fslpath.wslpath(fslplatform.fsldir)
        if fslplatform.fsldevdir:
            local_fsldevdir = fslpath.wslpath(fslplatform.fsldevdir)
        else:
            local_fsldevdir = None
        # Prepend important environment variables - note that it seems we cannot
        # use WSLENV for this due to its insistance on path mapping. FIXME FSLDEVDIR?
        local_path = "$PATH"
        if local_fsldevdir:
            local_path += ":%s/bin" % local_fsldevdir
        local_path += ":%s/bin" % local_fsldir
        prepargs = [
            "wsl",
            "PATH=%s" % local_path,
            "FSLDIR=%s" % local_fsldir,
            "FSLOUTPUTTYPE=%s" % os.environ.get("FSLOUTPUTTYPE", "NIFTI_GZ")
        ]
        if local_fsldevdir:
            prepargs.append("FSLDEVDIR=%s" % local_fsldevdir)
        return prepargs + wslargs
    else:
        # Command was not found in WSL with this path
        return None


def hold(job_ids, hold_filename=None):
    """
    Waits until all jobs have finished

    :param job_ids: possibly nested sequence of job ids. The job ids themselves should be strings.
    :param hold_filename: filename to use as a hold file.
        The containing directory should exist, but the file itself should not.
        Defaults to a ./.<random characters>.hold in the current directory.
    :return: only returns when all the jobs have finished
    """
    fslsub.hold(job_ids, hold_filename)
