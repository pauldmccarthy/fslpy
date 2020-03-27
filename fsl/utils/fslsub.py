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
import os.path as op
import glob
import time
import pickle
import sys
import tempfile
import logging
import importlib
from dataclasses import dataclass, asdict
from typing import Optional, Collection, Union, Tuple
import argparse
import warnings


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
    flags: bool = False
    multi_threaded: Optional[Tuple[str, str]] = None
    verbose: bool = False
    env: dict = None

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
    }

    def __post_init__(self):
        if self.env is None:
            self.env = {}

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
        if self.flags:
            res.append('-F')
        if self.multi_threaded:
            res.extend(("-s", ','.join(self.multi_threaded)))
        if self.wait_for is not None and len(_flatten_job_ids(self.wait_for)) > 0:
            res.extend(('-j', _flatten_job_ids(self.wait_for)))
        return tuple(res)

    def __str__(self):
        return 'SubmitParams({})'.format(" ".join(self.as_flags()))

    def __call__(self, *command, **kwargs):
        """
        Submits the command to the cluster.

        :param command: string or tuple of strings with the command to submit
        :param kwargs: Keyword arguments can override any parameters set in self
        :return: job ID
        """
        from fsl.utils.run import prepareArgs, runfsl
        runner = self.update(**kwargs)
        command = prepareArgs(command)
        fsl_sub_cmd = ' '.join(('fsl_sub', ) + tuple(runner.as_flags()) + tuple(command))
        log.debug(fsl_sub_cmd)
        jobid = runfsl(fsl_sub_cmd, env=runner.env).strip()
        log.debug('Job submitted as {}'.format(jobid))
        return jobid

    def update(self, **kwargs):
        """
        Creates a new SubmitParams withe updated parameters
        """
        values = asdict(self)
        values.update(kwargs)
        return SubmitParams(**values)

    @classmethod
    def add_to_parser(cls, parser: argparse.ArgumentParser, as_group='fsl_sub commands',
                      include=('wait_for', 'logdir', 'email', 'mail_options')):
        """
        Adds submission parameters to the parser

        :param parser: parser that should understand submission commands
        :param as_group: add as a new group
        :param include: sequence of argument flags/names that should be added to the parser
            (set to None to include everything)
        :return: the group the arguments got added to
        """
        from fsl.utils.run import runfsl, FSLNotPresent
        try:
            fsl_sub_run, _ = runfsl('fsl_sub', exitcode=True)
        except (FileNotFoundError, FSLNotPresent):
            warnings.warn('fsl_sub was not found')
            return
        doc_lines = fsl_sub_run.splitlines()
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

        def get_explanation(flag):
            explanation = None
            for line in doc_lines:
                if explanation is not None and len(line.strip()) > 0 and line.strip()[0] != '-':
                    explanation.append(line[nspaces:].strip())
                elif explanation is not None:
                    break
                elif line.strip().startswith(flag):
                    explanation = [line[nspaces:].strip()]
            if (explanation is None) or (len(explanation) == 0):
                return 'documentation not found'
            return ' '.join(explanation)

        for flag, value in cls.cmd_line_flags.items():
            if include is not None and value not in include and flag not in include:
                continue

            as_type = {'minutes': float, 'priority': int, 'ram': int, 'verbose': None}
            action = 'store_true' if value == 'verbose' else 'store'
            group.add_argument(flag, dest='_sub_' + value, help=get_explanation(flag), action=action,
                               metavar='<' + value + '>', type=as_type.get(value, str))
        group.add_argument('-F', dest='_sub_flags', help=get_explanation('-F'), action='store_true')
        group.add_argument('-v', dest='_sub_verbose', help=get_explanation('-v'), action='store_true')
        group.add_argument('-s', dest='_sub_multi_threaded', help=get_explanation('-s'),
                           metavar='<pename>,<threads>')
        group.add_argument('-j', dest='_sub_wait_for', help=get_explanation('-j'),
                           metavar='<jid>')
        return group

    @classmethod
    def from_args(cls, args):
        as_dict = {value: getattr(args, '_sub_' + value, None) for value in cls.cmd_line_flags.values()}
        if args._sub_wait_for is not None:
            as_dict['wait_for'] = args._sub_wait_for.split(',')
        if args._sub_multi_threaded is not None:
            pename, threads = args._sub_multi_threaded.split(',')
            as_dict['multi_threaded'] = pename, threads
        return cls(verbose=args._sub_verbose, flags=args._sub_flags, **as_dict)


def submit(*command, **kwargs):
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
    return SubmitParams(**kwargs)(*command)


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
    with open(__file__ + '_out.pickle', 'w') as f:
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
