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


from six import string_types, BytesIO
import subprocess as sp
import os.path as op
import glob
import time
import pickle
import sys
import tempfile
import logging
import importlib


log = logging.getLogger(__name__)


def submit(command,
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
           verbose=False):
    """Submits a given command to the cluster

    :arg command:        single string with the job command
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

    :return:             string of submitted job id
    """

    from fsl.utils.run import runfsl

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

    base_cmd.append(command)

    return runfsl(*base_cmd).strip()


def info(job_id):
    """Gets information on a given job id

    Uses `qstat -j <job_id>`

    :arg job_id: string with job id
    :return:     dictionary with information on the submitted job (empty
                 if job does not exist)
    """
    try:
        result = sp.call(['qstat', '-j', job_id]).decode('utf-8')
    except FileNotFoundError:
        log.debug("qstat not found; assuming not on cluster")
        return {}
    if 'Following jobs do not exist:' in result:
        return {}
    res = {}
    for line in result.splitlines()[1:]:
        key, value = line.split(':', nsplit=1)
        res[key.strip()] = value.strip()
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
    for job_id in _flatten_job_ids(job_ids):
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
