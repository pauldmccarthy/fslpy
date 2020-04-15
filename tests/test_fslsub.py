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

import fsl
from fsl.utils         import fslsub
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
        fslsub.wait(jid)
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

        fslsub.wait(jid)

        stdout, stderr = fslsub.output(jid)

        assert stdout.strip() == 'standard output'
        assert stderr.strip() == 'standard error'
