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
   runfunc
   func_to_cmd
   dryrun
   hold
   job_output
"""


import                    io
import                    sys
import                    glob
import                    time
import                    shlex
import                    logging
import                    tempfile
import                    threading
import                    contextlib
import collections.abc as abc
import subprocess      as sp
import os.path         as op
import                    os
import textwrap        as tw

import                    dill

from   fsl.utils.platform import platform as fslplatform
import fsl.utils.tempdir                  as tempdir
import fsl.utils.path                     as fslpath


log = logging.getLogger(__name__)


DRY_RUN = False
"""If ``True``, the :func:`run` function will only log commands, but will not
execute them.
"""

DRY_RUN_COMMANDS = None
"""Contains the commands that got logged during a dry run.

Commands will be logged if :data:`DRY_RUN` is true, which can be set using :func:`dryrun`.
"""


FSL_PREFIX = None
"""Global override for the FSL executable location used by :func:`runfsl`. """


class FSLNotPresent(Exception):
    """Error raised by the :func:`runfsl` function when ``$FSLDIR`` cannot
    be found.
    """


@contextlib.contextmanager
def dryrun(*_):
    """Context manager which causes all calls to :func:`run` to be logged but
    not executed. See the :data:`DRY_RUN` flag.

    The returned standard output will be equal to ``' '.join(args)``.

    After this function returns, each command that was executed while the
    dryrun is active, along with any submission parameters, will be accessible
    within a list which is stored as :data:`DRY_RUN_COMMANDS`.
    """
    global DRY_RUN, DRY_RUN_COMMANDS  # pylint: disable=global-statement

    oldval          = DRY_RUN
    DRY_RUN         = True
    DRY_RUN_COMMANDS = []


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
                   the :mod:`fsl.wrappers.fsl_sub` function.  May also be a
                   dictionary containing arguments to that function.

    :arg cmdonly:  Defaults to ``False``. If ``True``, the command is not
                   executed, but rather is returned directly, as a list of
                   arguments.

    :arg log:      Must be passed as a keyword argument.  Defaults to
                   ``{'tee' : True}``. An optional ``dict`` which may be used
                   to redirect the command's standard output and error. Ignored
                   if ``submit`` is specified. The following keys are
                   recognised:

                     - tee:    If ``True`` (the default), the command's
                               standard output/error streams are forwarded to
                               the output streams of this process, in addition
                               to being captured and returned.

                     - stdout: Optional callable or file-like object to which
                               the command's standard output stream can be
                               forwarded.

                     - stderr: Optional callable or file-like object to which
                               the command's standard error stream can be
                               forwarded.

                     - cmd:    Optional callable or file-like object to which
                               the command itself is logged.

    :arg silent:   Suppress standard output/error. Equivalent to passing
                   ``log={'tee' : False}``. Ignored if `log` is also passed.

    All other keyword arguments are passed through to the ``subprocess.Popen``
    object (via :func:`_realrun`), unless ``submit=True``, in which case they
    are passed through to the :func:`.fsl_sub` function.

    :returns: If ``submit`` is provided, the ID of the submitted job is
              returned as a string. Otherwise returns a single value or a
              tuple, based on the based on the ``stdout``, ``stderr``, and
              ``exitcode`` arguments.
    """

    returnStdout   = kwargs.pop('stdout',   True)
    returnStderr   = kwargs.pop('stderr',   False)
    returnExitcode = kwargs.pop('exitcode', False)
    submit         = kwargs.pop('submit',   {})
    cmdonly        = kwargs.pop('cmdonly',  False)
    logg           = kwargs.pop('log',      None)
    silent         = kwargs.pop('silent',   False)
    args           = prepareArgs(args)

    if logg is None:
        logg = {'tee' : not silent}

    tee       = logg.get('tee',    True)
    logStdout = logg.get('stdout', None)
    logStderr = logg.get('stderr', None)
    logCmd    = logg.get('cmd',    None)

    if not bool(submit):
        submit = None

    if submit is not None:
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

    # submit - delegate to fsl_sub. This will induce a nested
    # call back to this run function, which is a bit confusing,
    # but harmless, as we've popped the "submit" arg above.
    if submit is not None:
        from fsl.wrappers import fsl_sub  # pylint: disable=import-outside-toplevel  # noqa: E501
        return fsl_sub(*args, log=logg, **submit, **kwargs)[0].strip()

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

    # Save command/submit parameters -
    # see the dryrun ctx manager
    if DRY_RUN_COMMANDS is not None:
        DRY_RUN_COMMANDS.append((args, submit))

    if submit:
        return ('0',)

    results = []
    stderr  = ''
    join    = getattr(shlex, 'join', ' '.join)
    stdout  = join(args)

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

    :arg logStdout: Optional callable or file-like object to which the
                    command's standard output stream can be forwarded.

    :arg logStderr: Optional callable or file-like object to which the
                    command's standard error stream can be forwarded.

    :arg logCmd:    Optional  callable or file-like to which the command
                    itself is logged.

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

            # And we also duplicate to caller-provided
            # streams if they are file-likes (if they're
            # callables, we call them after the process
            # has completed)
            if logStdout is not None and not callable(logStdout):
                outstreams.append(logStdout)
            if logStderr is not None and not callable(logStderr):
                errstreams.append(logStderr)

            # log the command if requested.
            # logCmd can be a callable, or
            # can be a file-like.
            cmd = ' '.join(args) + '\n'
            if callable(logCmd):
                logCmd(cmd)
            elif logCmd is not None:
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

    # Send stdout/error to logStdout/err callables
    if logStdout is not None and callable(logStdout): logStdout(stdout)
    if logStderr is not None and callable(logStderr): logStderr(stderr)

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


def runfunc(func,
            args=None,
            kwargs=None,
            tmp_dir=None,
            clean="never",
            verbose=False,
            **run_kwargs):
    """Run the given python function as a shell command. See
    :func:`func_to_cmd` for details on the arguments.

    The remaining ``run_kwargs`` arguments are passed through to the
    :func:`run` function.
    """
    cmd = func_to_cmd(func, args, kwargs, tmp_dir, clean, verbose)
    return run(cmd, **run_kwargs)


def func_to_cmd(func,
                args=None,
                kwargs=None,
                tmp_dir=None,
                clean="never",
                verbose=False):
    """Save the given python function to an executable file. Return a string
    containing a command that can be used to run the function.

    ..warning:: If submitting a function defined in the ``__main__`` script,
                the script will be run again to retrieve this function. Make
                sure there is a ``if __name__ == '__main__'`` guard to prevent
                the full script from being re-run.

    :arg func:    function to be run

    :arg args:    positional arguments

    :arg kwargs:  keyword arguments

    :arg tmp_dir: directory where to store the temporary file (default: the
                  system temporary directory)

    :arg clean:   Whether the script should be removed after running. There are
                  three options:

                    - ``"never"``:      (default) Script is kept
                    - ``"on_success"``: only remove if script successfully
                                        finished (i.e., no error is raised)
                    - ``"always"``:     always remove the script, even if it
                                        raises an error

    :arg verbose: If set to True, the script will print its own filename
                  before running
    """
    script_template = tw.dedent("""
    #!{executable}
    # This is a temporary file designed to run the python function {funcname},
    # so that it can be submitted to the cluster
    import os
    import dill
    from io import BytesIO
    from importlib import import_module

    if {verbose}:
        print('running {filename}')

    dill_bytes = BytesIO({dill_bytes})
    func, args, kwargs = dill.load(dill_bytes)

    clean = {clean}

    try:
        res = func(*args, **kwargs)
    except Exception as e:
        if clean == 'on_success':
            clean = 'never'
        raise e
    finally:
        if clean in ('on_success', 'always'):
            os.remove({filename})
    """).strip()

    if clean not in ('never', 'always', 'on_success'):
        raise ValueError("Clean should be one of 'never', 'always', "
                         f"or 'on_success', not {clean}")

    if args   is None: args   = ()
    if kwargs is None: kwargs = {}

    dill_bytes = io.BytesIO()
    dill.dump((func, args, kwargs), dill_bytes, recurse=True)

    handle, filename = tempfile.mkstemp(prefix=func.__name__ + '_',
                                        suffix='.py',
                                        dir=tmp_dir)
    os.close(handle)

    python_cmd = script_template.format(
        executable=sys.executable,
        funcname=func.__name__,
        filename=f'"{filename}"',
        verbose=verbose,
        clean=f'"{clean}"',
        dill_bytes=dill_bytes.getvalue())

    with open(filename, 'w') as f:
        f.write(python_cmd)
    os.chmod(filename, 0o755)

    return f'{filename}'


def wslcmd(cmdpath, *args):
    """Convert a command + arguments into an equivalent set of arguments that
    will run the command under Windows Subsystem for Linux

    :param cmdpath: Fully qualified path to the command. This is essentially
                    a WSL path not a Windows one since FSLDIR is specified
                    as a WSL path, however it may have backslashes as path
                    separators due to previous use of ``os.path.join``

    :param args:    Sequence of command arguments (the first of which is the
                    unqualified command name)

    :return: If ``cmdpath`` exists and is executable in WSL, return a
             sequence of command arguments which when executed will run the
             command in WSL. Windows paths in the argument list will be
             converted to WSL paths. If ``cmdpath`` was not executable in
             WSL, returns None
    """
    # Check if command exists in WSL (remembering
    # that the command path may include FSLDIR
    # which is a Windows path)
    cmdpath = fslpath.wslpath(cmdpath)
    _stdout, _stderr, retcode = _realrun(
        False, None, None, None, "wsl", "test", "-x", cmdpath)
    if retcode == 0:
        # Form a new argument list and convert
        # any Windows paths in it into WSL paths
        wslargs = [fslpath.wslpath(arg) for arg in args]
        wslargs[0] = cmdpath
        local_fsldir = fslpath.wslpath(fslplatform.fsldir)
        if fslplatform.fsldevdir:
            local_fsldevdir = fslpath.wslpath(fslplatform.fsldevdir)
        else:
            local_fsldevdir = None
        # Prepend important environment variables -
        # note that it seems we cannot use WSLENV
        # for this due to its insistance on path
        # mapping. FIXME FSLDEVDIR?
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


def hold(job_ids, hold_filename=None, timeout=10):
    """Waits until all specified cluster jobs have finished.

    :arg job_ids:       Possibly nested sequence of job ids. The job ids
                        themselves should be strings.

    :arg hold_filename: Filename to use as a hold file.  The containing
                        directory should exist, but the file itself should
                        not.  Defaults to a ./.<random characters>.hold in
                        the current directory.

    :arg timeout:       Number of seconds to sleep between  status checks.
    """

    # Returns a potentially nested sequence of
    # job ids as a single comma-separated string
    def _flatten_job_ids(job_ids):
        def unpack(job_ids):
            if isinstance(job_ids, str):
                return {job_ids}
            elif isinstance(job_ids, int):
                return {str(job_ids)}
            else:
                res = set()
                for job_id in job_ids:
                    res.update(unpack(job_id))
                return res
        return ','.join(sorted(unpack(job_ids)))

    if hold_filename is not None:
        if op.exists(hold_filename):
            raise IOError(f"Hold file ({hold_filename}) already exists")
        elif not op.isdir(op.split(op.abspath(hold_filename))[0]):
            raise IOError(f"Hold file ({hold_filename}) can not be created "
                          "in non-existent directory")

    # Generate a random file name to use as
    # the hold file. Reduce likelihood of
    # naming collision by storing file in
    # cwd.
    if hold_filename is None:
        handle, hold_filename = tempfile.mkstemp(prefix='.',
                                                 suffix='.hold',
                                                 dir='.')
        os.remove(hold_filename)
        os.close(handle)

    submit = {
        'jobhold'  : _flatten_job_ids(job_ids),
        'jobtime'  : 1,
        'name'     : '.hold',
    }

    run(f'touch {hold_filename}', submit=submit, silent=True)

    while not op.exists(hold_filename):
        time.sleep(timeout)

    # remove the hold file and the
    # fsl_sub job stdout/err files
    os.remove(hold_filename)
    for outfile in glob.glob('.hold.[o,e]*'):
        os.remove(outfile)


def job_output(job_id, logdir='.', command=None, name=None):
    """Returns the output of the given cluster-submitted job.

    On SGE cluster systems, the standard output and error streams of a
    submitted job are saved to files named ``<job_id>.o`` and ``<job_id>.e``.
    This function simply reads those files and returns their content.

    :arg job_id:  String containing job ID.
    :arg logdir:  Directory containing the log - defaults to
                  the current directory.
    :arg command: Command that was run. Not currently used.
    :arg name:    Job name if it was specified. Not currently used.
    :returns:     A tuple containing the standard output and standard error.
    """

    stdout = list(glob.glob(op.join(logdir, f'*.o{job_id}')))
    stderr = list(glob.glob(op.join(logdir, f'*.e{job_id}')))

    if len(stdout) != 1 or len(stderr) != 1:
        raise ValueError('No/too many error/output files for job '
                         f'{job_id}: stdout: {stdout}, stderr: {stderr}')

    stdout = stdout[0]
    stderr = stderr[0]

    if op.exists(stdout):
        with open(stdout, 'rt') as f:
            stdout = f.read()
    else:
        stdout = None

    if op.exists(stderr):
        with open(stderr, 'rt') as f:
            stderr = f.read()
    else:
        stderr = None

    return stdout, stderr
