#!/usr/bin/env python
#
# test_fslsub.py - Tests functions in the fsl.utils.fslsub module.
#
# Author: Michiel Cottaar <Michiel.Cottaar@ndcn.ox.ac.uk>
# Author: Paul McCarthy   <pauldmccarthy@gmail.com>
#


import os
import os.path as op
import sys
import textwrap as tw
import contextlib
import argparse
import pytest

import fsl
from fsl.utils         import fslsub, run
from fsl.utils.tempdir import tempdir

from . import mockFSLDIR


mock_fsl_sub = """
#!/usr/bin/env python3

import random
import os
import os.path as op
import sys
import subprocess as sp

fslpydir = op.join('{}', '..')
env = dict(os.environ)

env['PYTHONPATH'] = fslpydir
sys.path.insert(0, fslpydir)

import fsl

args = sys.argv[1:]

for i in range(len(args)):
    a = args[i]
    if a[0] == '-':
       if a[1] == 's':
           i += 2
       elif a[1] not in ('F', 'v'):
           i += 1
       continue
    else:
        break

args = args[i:]

cmd   = op.basename(args[0])
jobid = random.randint(1, 9999)

with open('{{}}.o{{}}'.format(cmd, jobid), 'w') as stdout, \
     open('{{}}.e{{}}'.format(cmd, jobid), 'w') as stderr:
    result = sp.run(args, stdout=stdout, stderr=stderr, env=env)

print(str(jobid))
sys.exit(0)
""".format(op.dirname(fsl.__file__)).strip()

@contextlib.contextmanager
def fslsub_mockFSLDIR():
    with mockFSLDIR() as fsldir:
        fslsubbin = op.join(fsldir, 'bin', 'fsl_sub')
        with open(fslsubbin, 'wt') as f:
            f.write(mock_fsl_sub)
        os.chmod(fslsubbin, 0o755)
        yield fsldir


def test_flatten_jobids():
    job_ids = ('12', '27', '35', '41', 721)
    res = '12,27,35,41,721'

    assert fslsub._flatten_job_ids(job_ids) == res
    assert fslsub._flatten_job_ids(job_ids[::-1]) == res
    assert fslsub._flatten_job_ids('12') == '12'
    assert fslsub._flatten_job_ids([job_ids[:2], job_ids[2:]]) == res
    assert fslsub._flatten_job_ids([set(job_ids[:2]), job_ids[2:]]) == res
    assert fslsub._flatten_job_ids(((job_ids, ), job_ids + job_ids)) == res


def test_submit():
    script = tw.dedent("""#!/usr/bin/env bash
    echo "standard output"
    echo "standard error" >&2
    exit 0
    """).strip()

    with fslsub_mockFSLDIR(), tempdir():
        cmd = op.join('.', 'myscript')
        with open(cmd, 'wt') as f:
            f.write(script)
        os.chmod(cmd, 0o755)

        jid = fslsub.submit(cmd)
        stdout, stderr = fslsub.output(jid)

        assert stdout.strip() == 'standard output'
        assert stderr.strip() == 'standard error'


def test_info():
    mock_qstat = tw.dedent("""
    #!/usr/bin/env bash
    echo "#####################"
    echo "job_number:        1 "
    echo "exec_file:         2 "
    echo "submission_time:   3 "
    echo "owner:             4 "
    """).strip()

    with mockFSLDIR() as fsldir:
        qstatbin = op.join(fsldir, 'bin', 'qstat')
        with open(qstatbin, 'wt') as f:
            f.write(mock_qstat)
        os.chmod(qstatbin, 0o755)

        exp = {'job_number'      : '1',
               'exec_file'       : '2',
               'submission_time' : '3',
               'owner'           : '4'}
        assert fslsub.info('12345') == exp


def test_add_to_parser():
    test_flags = [
        ('-T', '30.0'),
        ('-q', 'short.q'),
        ('-a', 'architecture'),
        ('-p', '3'),
        ('-M', 'test@something.com'),
        ('-N', 'job_name'),
        ('-R', '20'),
        ('-l', 'logdir'),
        ('-j', '12345,67890'),
        ('-m', 'mail_options'),
        ('-v', ),
        ('-F', ),
        ('-s', 'pename,thread')
    ]
    with fslsub_mockFSLDIR():
        for flag in test_flags:
            for include in (None, [flag[0]]):
                parser = argparse.ArgumentParser("test parser")
                fslsub.SubmitParams.add_to_parser(parser, include=include)
                args = parser.parse_args(flag)
                submitter = fslsub.SubmitParams.from_args(args)
                assert submitter.as_flags() == flag

    with fslsub_mockFSLDIR():
        parser = argparse.ArgumentParser("test parser")
        parser.add_argument('some_input')
        fslsub.SubmitParams.add_to_parser(parser, include=None)
        all_flags = tuple(part for flag in test_flags for part in flag)
        args = parser.parse_args(('input', ) + all_flags)
        assert args.some_input == 'input'
        submitter = fslsub.SubmitParams.from_args(args)
        assert len(all_flags) == len(submitter.as_flags())

        for flag in test_flags:
            res_flags = submitter.as_flags()
            assert flag[0] in res_flags
            start_index = res_flags.index(flag[0])
            for idx, part in enumerate(flag):
                assert res_flags[idx + start_index] == part


def myfunc():
    print('standard output')
    print('standard error', file=sys.stderr)


def test_func_to_cmd():
    with fslsub_mockFSLDIR(), tempdir():
        cmd = fslsub.func_to_cmd(myfunc, (), {})
        jid = fslsub.submit(cmd)

        stdout, stderr = fslsub.output(jid)

        assert stdout.strip() == 'standard output'
        assert stderr.strip() == 'standard error'


example_qstat_reply = """==============================================================
job_number:                 9985061
exec_file:                  job_scripts/9985061
owner:                      user
sge_o_home:                 /home/fs0/user
sge_o_log_name:             user
sge_o_shell:                /bin/bash
sge_o_workdir:              /home/fs0/user
account:                    sge
cwd:                        /home/fs0/user
mail_options:               a
notify:                     FALSE
job_name:                   echo
jobshare:                   0
hard_queue_list:            long.q
restart:                    y
job_args:                   test
script_file:                echo
binding:                    set linear:slots
job_type:                   binary,noshell
scheduling info:            queue instance "<some queue>" dropped because it is temporarily not available
                            queue instance "<some queue>" dropped because it is disabled
==============================================================
job_number:                 9985062
exec_file:                  job_scripts/9985062
owner:                      user
sge_o_home:                 /home/fs0/user
sge_o_log_name:             user
sge_o_shell:                /bin/bash
sge_o_workdir:              /home/fs0/user
account:                    sge
cwd:                        /home/fs0/user
mail_options:               a
notify:                     FALSE
job_name:                   echo
jobshare:                   0
hard_queue_list:            long.q
restart:                    y
job_args:                   test
script_file:                echo
binding:                    set linear:slots
job_type:                   binary,noshell
scheduling info:            queue instance "<some queue>" dropped because it is temporarily not available
                            queue instance "<some queue>" dropped because it is disabled
"""


def test_info():
    valid_job_ids = ['9985061', '9985062']
    res = fslsub._parse_qstat(','.join(valid_job_ids), example_qstat_reply)
    assert len(res) == 2
    for job_id in valid_job_ids:
        assert res[job_id] is not None
        assert res[job_id]['account'] == 'sge'
        assert res[job_id]['job_type'] == 'binary,noshell'
        assert len(res[job_id]['scheduling info'].splitlines()) == 2
        for line in res[job_id]['scheduling info'].splitlines():
            assert line.startswith('queue instance ')

    res2 = fslsub._parse_qstat(','.join(valid_job_ids + ['1']), example_qstat_reply)
    assert len(res2) == 3
    for job_id in valid_job_ids:
        assert res[job_id] == res2[job_id]
    assert res2['1'] is None

    with pytest.raises(ValueError):
        fslsub._parse_qstat(valid_job_ids[0], example_qstat_reply)


def _good_func():
    print('hello')


def _bad_func():
    1/0


def test_func_to_cmd():
    cwd = os.getcwd()
    with tempdir():
        for tmp_dir in (None, '.'):
            for clean in ('never', 'on_success', 'always'):
                for verbose in (False, True):
                    cmd = fslsub.func_to_cmd(_good_func, clean=clean, tmp_dir=tmp_dir, verbose=verbose)
                    fn = cmd.split()[-1]
                    assert op.exists(fn)
                    stdout, stderr, exitcode = run.run(cmd, exitcode=True, stdout=True, stderr=True,
                                                       env={"PYTHONPATH": cwd})
                    assert exitcode == 0
                    if clean == 'never':
                        assert op.exists(fn), "Successful job got removed, even though this was not requested"
                    else:
                        assert not op.exists(fn), f"Successful job did not get removed after run for clean = {clean}"
                    if verbose:
                        assert stdout.strip() == f'running {fn}\nhello'
                    else:
                        assert stdout.strip() == 'hello'

                cmd = fslsub.func_to_cmd(_bad_func, clean=clean, tmp_dir=tmp_dir)
                fn = cmd.split()[-1]
                assert op.exists(fn)
                stdout, stderr, exitcode = run.run(cmd, exitcode=True, stdout=True, stderr=True,
                                                   env={'PYTHONPATH': cwd})
                assert exitcode != 0
                if clean == 'always':
                    assert not op.exists(fn), "Failing job should always be removed if requested"
                else:
                    assert op.exists(fn), f"Failing job got removed even with clean = {clean}"
