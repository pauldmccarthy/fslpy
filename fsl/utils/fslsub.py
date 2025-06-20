#!/usr/bin/env python
#
# fslsub.py - Functions for using fsl_sub.
#
# Author: Michiel Cottaar <michiel.cottaar@ndcn.ox.ac.uk>
#
"""This module submits jobs to a computing cluster using FSL's fsl_sub command
line tool. It is assumed that the computing cluster is managed by SGE.

.. note:: All of the functionality in this module is deprecated and will be
          removed in a future version of fslpy. Equivalent functionality is
          available in the `fsl_sub <https://git.fmrib.ox.ac.uk/fsl/fsl_sub>`_
          project, and the :mod:`fsl.utils.run` module and
          :mod:`.wrappers.fsl_sub` wrapper function.

Example usage, building a short pipeline::

    from fsl.utils.fslsub import submit

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

.. autosummary::
   :nosignatures:

   submit
   info
   output
   func_to_cmd
   hold
"""


from io import BytesIO
import os.path as op
import glob
import time
import dill
import sys
import tempfile
import logging
import importlib
from dataclasses import dataclass, asdict
from typing import Optional, Collection, Union, Tuple, Dict
import argparse
import warnings
import os


import fsl.utils.deprecated as deprecated
import fsl.utils.run        as run


log = logging.getLogger(__name__)


@dataclass
class SubmitParams:
    """Represents the fsl_sub parameters

    The ``SubmitParams`` class is deprecated - you should use
    :mod:`fsl.wrappers.fsl_sub` instead, or use the ``fsl_sub`` Python
    library, which is installed as part of FSL.

    Any command line script can be submitted by the parameters by calling the `SubmitParams` object:

    .. code-block:: python

        submit = SubmitParams(minutes=1, logdir='log', wait_for=['108023', '108019'])
        submit('echo finished')

    This will run "echo finished" with a maximum runtime of 1 minute after the jobs with IDs 108023 and 108019 are finished.
    It is the equivalent of

    .. code-block:: bash

        fsl_sub -T 1 -l log -j 108023,108019 "echo finished"

    For python scripts that submit themselves to the cluster, it might be useful to give the user some control
    over at least some of the submission parameters. This can be done using:

    .. code-block:: python

        import argparse
        parser = argparse.ArgumentParser("my script doing awesome stuff")
        parser.add_argument("input_file")
        parser.add_argument("output_file")
        SubmitParams.add_to_parser(parser, include=('wait_for', 'logdir'))
        args = parser.parse_args()

        submitter = SubmitParams.from_args(args).update(minutes=10)
        from fsl import wrappers
        wrappers.bet(input_file, output_file, fslsub=submitter)

    This submits a BET job using the -j and -l flags set by the user and a maximum time of 10 minutes.
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
        """
        If not set explicitly by the user don't alter the environment in which the script will be submitted
        """
        if self.env is None:
            self.env = dict(os.environ)

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

    @deprecated.deprecated('3.7.0', '4.0.0',
                           'Use fsl_sub or fsl.wrappers.fsl_sub instead')
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
        """
        Create a SubmitParams from the command line arguments
        """
        as_dict = {value: getattr(args, '_sub_' + value, None) for value in cls.cmd_line_flags.values()}
        if args._sub_wait_for is not None:
            as_dict['wait_for'] = args._sub_wait_for.split(',')
        if args._sub_multi_threaded is not None:
            pename, threads = args._sub_multi_threaded.split(',')
            as_dict['multi_threaded'] = pename, threads
        return cls(verbose=args._sub_verbose, flags=args._sub_flags, **as_dict)


@deprecated.deprecated('3.7.0', '4.0.0',
                       'Use fsl_sub or fsl.wrappers.fsl_sub instead')
def submit(*command, **kwargs):
    """
    Submits a given command to the cluster

    The ``submit`` function is deprecated - you should use
    :mod:`fsl.wrappers.fsl_sub` instead, or use the ``fsl_sub`` Python
    library, which is available in FSL 6.0.5 and newer.

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


@deprecated.deprecated('3.7.0', '4.0.0', 'Use fsl_sub.report instead')
def info(job_ids) -> Dict[str, Optional[Dict[str, str]]]:
    """Gets information on a given job id

    The ``info`` function is deprecated - you should use the
    ``fsl_sub.report`` function from the ``fsl_sub`` Python library, which
    is available in FSL 6.0.5 and newer.

    Uses `qstat -j <job_ids>`

    :arg job_ids: string with job id or (nested) sequence with jobs
    :return: dictionary of jobid -> another dictionary with job information
             (or None if job does not exist)
    """
    if not hasattr(info, '_ncall'):
        info._ncall = 0
    info._ncall += 1
    if info._ncall == 3:
        warnings.warn("Please do not call `fslsub.info` repeatably, because it slows down the cluster. You can avoid this message by simply passing all the job IDs you are interested in to a single `fslsub.info` call.")

    from fsl.utils.run import run
    job_ids_string = _flatten_job_ids(job_ids)
    try:
        result = run(['qstat', '-j', job_ids_string], exitcode=True)[0]
    except FileNotFoundError:
        log.debug("qstat not found; assuming not on cluster")
        return {}
    return _parse_qstat(job_ids_string, result)


def _parse_qstat(job_ids_string, qstat_stdout):
    """
    Parses the qstat output into a dictionary of dictionaries

    :param job_ids_string: input job ids
    :param qstat_stdout: qstat output
    :return: dictionary of jobid -> another dictionary with job information
             (or None if job does not exist)
    """
    res = {job_id: None for job_id in job_ids_string.split(',')}
    current_job_id = None
    for line in qstat_stdout.splitlines()[1:]:
        line = line.strip()
        if len(line) == 0:
            continue
        if line == '=' * len(line):
            current_job_id = None
        elif ':' in line:
            current_key, value = [part.strip() for part in line.split(':', 1)]
            if current_key == 'job_number':
                current_job_id = value
                if current_job_id not in job_ids_string:
                    raise ValueError(f"Unexpected job ID in qstat output:\n{line}")
                res[current_job_id] = {}
            else:
                if current_job_id is None:
                    raise ValueError(f"Found job information before job ID in qstat output:\n{line}")
                res[current_job_id][current_key] = value
        else:
            res[current_job_id][current_key] += '\n' + line
    return res


@deprecated.deprecated('3.13.0', '4.0.0',
                       'Use fsl.utils.run.job_output instead')
def output(job_id, logdir='.', command=None, name=None):
    """Returns the output of the given job.

    :arg job_id:  String containing job ID.
    :arg logdir:  Directory containing the log - defaults to
                  the current directory.
    :arg command: Command that was run. Not currently used.
    :arg name:    Job name if it was specified. Not currently used.
    :returns:     A tuple containing the standard output and standard error.
    """
    return run.job_output(job_id, logdir, command, name)


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


@deprecated.deprecated('3.13.0', '4.0.0', 'Use fsl.utils.run.hold instead')
def hold(*args, **kwargs):
    """Deprecated - moved to the :mod:`.run` module. """
    run.hold(*args, **kwargs)


@deprecated.deprecated('3.13.0', '4.0.0',
                      'Use fsl.utils.run.func_to_cmd instead')
def func_to_cmd(*args, **kwargs):
    """Deprecated - moved to the :mod:`.run` module. """
    return run.func_to_cmd(*args, **kwargs)
