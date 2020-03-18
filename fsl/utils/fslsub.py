#!/usr/bin/env python
#
# fslsub.py - Functions for using fsl_sub.
#
# Author: Michiel Cottaar <michiel.cottaar@ndcn.ox.ac.uk>
#
"""This module submits jobs to a computing cluster using FSL's fsl_sub command
line tool. It is assumed that the computing cluster is managed by SGE.

Example usage, building a short pipeline::

    from fsl.utils.fslsub import submit, wait

    # submits bet to veryshort queue unless <mask_filename> already exists
    bet_job = submit('bet <input_filename> -m',
                     queue='veryshort.q',
                     output='<mask_filename>')

    # submits another job
    other_job = submit('some other pre-processing step', queue='short.q')

    # submits cuda job, that should only start after both preparatory jobs are
    # finished. This will work if bet_job and other_job are single job-ids
    # (i.e., strings) or a sequence of multiple job-ids
    cuda_job = submit('expensive job',
                      wait_for=(bet_job, other_job),
                      queue='cuda.q')

    # waits for the cuda job to finish
    wait(cuda_job)

.. autosummary::
   :nosignatures:

   submit
   info
   output
   wait
   func_to_cmd
"""


from six import BytesIO
import subprocess as sp
import os.path as op
import os
import glob
import time
import pickle
import sys
import tempfile
import logging
import importlib
from dataclasses import dataclass, asdict
from typing import Optional, Collection, Union
import argparse
import warnings
from subprocess import run, PIPE


log = logging.getLogger(__name__)


@dataclass
class SubmitParams(object):
    """
    Represents the fsl_sub parameters
    """
    minutes: Optional[float] = None
    queue: Optional[str] = None
    architecture: Optional[str] = None
    priority: Optional[int] = None
    email: Optional[str] = None
    wait_for: Union[str, None, Collection[str]] = None
    job_name: Optional[str] = None
    ram: Optional[int] = None
    logdir: Optional[str] = None
    mail_options: Optional[str] = None
    flags: Optional[str] = None
    verbose: bool = False
    environment: dict = None

    cmd_line_flags = {
        '-T': 'minutes',
        '-q': 'queue',
        '-a': 'architecture',
        '-p': 'priority',
        '-M': 'email',
        '-N': 'job_name',
        '-R': 'ram',
        '-l': 'logdir',
        '-m': 'mail_options',
        '-F': 'flags',
    }

    def __post_init__(self):
        if self.environment is None:
            self.environment = {}

    def as_flags(self, ):
        """
        Creates flags for submission using fsl_sub

        All parameters changed from their default value (typically None) will be included in the flags.

        :return: tuple with the flags
        """
        res = []
        for key, value in self.cmd_line_flags.items():
            if getattr(self, value) is not None:
                res.extend((key, str(getattr(self, value))))
        if self.verbose:
            res.append('-v')
        if self.wait_for is not None and len(_flatten_job_ids(self.wait_for)) > 0:
            res.extend(('-j', _flatten_job_ids(self.wait_for)))
        return tuple(res)

    def __str__(self):
        return f'SubmitParams({" ".join(self.as_flags())})'

    def __call__(self, *cmd, **kwargs):
        """
        Submits the command to the cluster.

        :param cmd: string or tuple of strings with the command to submit
        :param kwargs: Keyword arguments can override any parameters set in self
        :return: job ID
        """
        from fsl.utils.run import prepareArgs
        runner = self.update(**kwargs)
        cmd = prepareArgs(cmd)
        log.debug(' '.join(('fsl_sub', ) + tuple(runner.as_flags()) + tuple(cmd)))
        env = dict(os.environ)
        env.update(runner.environment)
        jobid = run(
            ('fsl_sub', ) + tuple(runner.as_flags()) + tuple(cmd),
            stdout=PIPE, check=True, env=env,
            ).stdout.decode().strip()
        log.debug(f'Job submitted as {jobid}')
        return jobid

    def update(self, **kwargs):
        """
        Creates a new SubmitParams withe updated parameters
        """
        values = asdict(self)
        values.update(kwargs)
        return SubmitParams(**values)

    @classmethod
    def add_to_parser(cls, parser: argparse.ArgumentParser, as_group='fsl_sub commands', skip=()):
        """
        Adds submission parameters to the parser

        :param parser: parser that should understand submission commands
        :param as_group: add as a new group
        :param skip: sequence of argument flags/names that should not be added to the parser
        :return: the group the arguments got added to
        """
        from fsl.utils.run import runfsl, prepareArgs
        try:
            fsl_sub_run = runfsl(['fsl_sub'])
        except FileNotFoundError:
            warnings.warn('fsl_sub was not found')
            return
        doc_lines = fsl_sub_run.stdout.decode().splitlines()
        nspaces = 1
        for line in doc_lines:
            if len(line.strip()) > 0:
                while line.startswith(' ' * nspaces):
                    nspaces += 1
        nspaces -= 1
        if as_group:
            group = parser.add_argument_group(as_group)
        else:
            group = parser
        for flag, value in cls.cmd_line_flags.items():
            if value in skip or flag in skip:
                continue
            explanation = None
            for line in doc_lines:
                if explanation is not None and len(line.strip()) > 0 and line.strip()[0] != '-':
                    explanation.append(line[nspaces:].strip())
                elif explanation is not None:
                    break
                elif line.strip().startswith(flag):
                    explanation = [line[nspaces:].strip()]
            explanation = ' '.join(explanation)
            as_type = {'minutes': float, 'priority': int, 'ram': int, 'verbose': None}
            action = 'store_true' if value == 'verbose' else 'store'
            group.add_argument(flag, dest='sub_' + value, help=explanation, action=action,
                               type=as_type[value] if value in as_type else str)
        return group

    @classmethod
    def from_args(cls, args):
        as_dict = {value: getattr(args, 'sub_' + value, None) for value in cls.cmd_line_flags.values()}
        return cls(**as_dict)


def submit(*command,
           minutes=None,
           queue=None,
           architecture=None,
           priority=None,
           email=None,
           wait_for=None,
           job_name=None,
           ram=None,
           logdir=None,
           mail_options=None,
           output=None,
           flags=False,
           multi_threaded=None,
           verbose=False,
           env=None):
    """
    Submits a given command to the cluster

    You can pass the command and arguments as a single string, or as a regular or unpacked sequence.

    :arg command:        string or regular/unpacked sequence of strings with the job command
    :arg minutes:        Estimated job length in minutes, used to auto-set
                         queue name
    :arg queue:          Explicitly sets the queue name
    :arg architecture:   e.g., darwin or lx24-amd64
    :arg priority:       Lower priority [0:-1024] default = 0
    :arg email:          Who to email after job completion
    :arg wait_for:       Place a hold on this task until the job-ids in this
                         string or tuple are complete
    :arg job_name:       Specify job name as it will appear on the queue
    :arg ram:            Max total RAM to use for job (integer in MB)
    :arg logdir:         where to output logfiles
    :arg mail_options:   Change the SGE mail options, see qsub for details
    :arg output:         If <output> image or file already exists, do nothing
                         and exit
    :arg flags:          If True, use flags embedded in scripts to set SGE
                         queuing options
    :arg multi_threaded: Submit a multi-threaded task - Set to a tuple
                         containing two elements:

                          - <pename>: a PE configures for the requested queues

                          - <threads>: number of threads to run

    :arg verbose:        If True, use verbose mode
    :arg env:            Dict containing environment variables

    :return:             string of submitted job id
    """

    from fsl.utils.run import runfsl, prepareArgs

    base_cmd = ['fsl_sub']

    for flag, variable_name in [
            ('-T', 'minutes'),
            ('-q', 'queue'),
            ('-a', 'architecture'),
            ('-p', 'priority'),
            ('-M', 'email'),
            ('-N', 'job_name'),
            ('-R', 'ram'),
            ('-l', 'logdir'),
            ('-m', 'mail_options'),
            ('-z', 'output')]:
        variable = locals()[variable_name]
        if variable:
            base_cmd.extend([flag, str(variable)])

    if flags:
        base_cmd.append('-F')
    if verbose:
        base_cmd.append('-v')

    if wait_for:
        base_cmd.extend(['-j', _flatten_job_ids(wait_for)])

    if multi_threaded:
        base_cmd.append('-s')
        base_cmd.extend(multi_threaded)

    base_cmd.extend(prepareArgs(command))

    return runfsl(*base_cmd, env=env).strip()


def info(job_id):
    """Gets information on a given job id

    Uses `qstat -j <job_id>`

    :arg job_id: string with job id
    :return:     dictionary with information on the submitted job (empty
                 if job does not exist)
    """
    from fsl.utils.run import run
    try:
        result = run(['qstat', '-j', job_id], exitcode=True)[0]
    except FileNotFoundError:
        log.debug("qstat not found; assuming not on cluster")
        return {}
    if 'Following jobs do not exist:' in result:
        return {}
    res = {}
    for line in result.splitlines()[1:]:
        kv = line.split(':', 1)
        if len(kv) == 2:
            res[kv[0].strip()] = kv[1].strip()
    return res


def output(job_id, logdir='.', command=None, name=None):
    """Returns the output of the given job.

    :arg job_id:  String containing job ID.
    :arg logdir:  Directory containing the log - defaults to
                  the current directory.
    :arg command: Command that was run. Not currently used.
    :arg name:    Job name if it was specified. Not currently used.
    :returns:     A tuple containing the standard output and standard error.
    """

    stdout = list(glob.glob(op.join(logdir, '*.o{}'.format(job_id))))
    stderr = list(glob.glob(op.join(logdir, '*.e{}'.format(job_id))))

    if len(stdout) != 1 or len(stderr) != 1:
        raise ValueError('No/too many error/output files for job {}: stdout: '
                         '{}, stderr: {}'.format(job_id, stdout, stderr))

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


def wait(job_ids):
    """Wait for one or more jobs to finish

    :arg job_ids: string or tuple of strings with jobs that should finish
                  before continuing
    """
    start_time = time.time()
    for job_id in _flatten_job_ids(job_ids).split(','):
        log.debug('Waiting for job {}'.format(job_id))
        while len(info(job_id)) > 0:
            wait_time = min(max(1, (time.time() - start_time) / 3.), 20)
            time.sleep(wait_time)
        log.debug('Job {} finished, continuing to next'.format(job_id))
    log.debug('All jobs have finished')


def _flatten_job_ids(job_ids):
    """
    Returns a potentially nested sequence of job ids as a single comma-separated string

    :param job_ids: possibly nested sequence of job ids. The job ids themselves should be strings.
    :return: comma-separated string of job ids
    """
    def unpack(job_ids):
        """Unpack the (nested) job-ids in a single set"""
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


_external_job = """#!{}
# This is a temporary file designed to run the python function {},
# so that it can be submitted to the cluster

import pickle
from six import BytesIO
from importlib import import_module

pickle_bytes = BytesIO({})
name_type, name, func_name, args, kwargs = pickle.load(pickle_bytes)

if name_type == 'module':
    # retrieves a function defined in an external module
    func = getattr(import_module(name), func_name)
elif name_type == 'script':
    # retrieves a function defined in the __main__ script
    local_execute = {{'__name__': '__not_main__', '__file__': name}}
    exec(open(name, 'r').read(), local_execute)
    func = local_execute[func_name]
else:
    raise ValueError('Unknown name_type: %r' % name_type)

res = func(*args, **kwargs)
if res is not None:
    with open(__file__ + '_out.pickle') as f:
        pickle.dump(f, res)
"""


def func_to_cmd(func, args, kwargs, tmp_dir=None, clean=False):
    """Defines the command needed to run the function from the command line

    WARNING: if submitting a function defined in the __main__ script,
    the script will be run again to retrieve this function. Make sure there is a
    "if __name__ == '__main__'" guard to prevent the full script from being rerun.

    :arg func:    function to be run
    :arg args:    positional arguments
    :arg kwargs:  keyword arguments
    :arg tmp_dir: directory where to store the temporary file
    :arg clean:   if True removes the submitted script after running it
    :return:      string which will run the function
    """
    pickle_bytes = BytesIO()
    if func.__module__ == '__main__':
        pickle.dump(('script', importlib.import_module('__main__').__file__, func.__name__,
                     args, kwargs), pickle_bytes)
    else:
        pickle.dump(('module', func.__module__, func.__name__,
                     args, kwargs), pickle_bytes)
    python_cmd = _external_job.format(sys.executable,
                                      func.__name__,
                                      pickle_bytes.getvalue())

    _, filename = tempfile.mkstemp(prefix=func.__name__ + '_',
                                   suffix='.py',
                                   dir=tmp_dir)

    with open(filename, 'w') as python_file:
        python_file.write(python_cmd)

    return sys.executable + " " + filename + ('; rm ' + filename if clean else '')
