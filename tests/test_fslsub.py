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

from fsl.utils         import fslsub
from fsl.utils.tempdir import tempdir

from . import mockFSLDIR


mock_fsl_sub = f"""
#!{sys.executable}

import random
import os
import os.path as op
import sys
import subprocess as sp
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

env  = dict(os.environ)
env['PYTHONPATH'] = op.join(op.dirname(fsl.__file__), '..')

cmd   = op.basename(args[0])
jobid = random.randint(1, 9999)

with open(f'{{cmd}}.o{{jobid}}', 'w') as stdout, \
     open(f'{{cmd}}.e{{jobid}}', 'w') as stderr:
    result = sp.run(args, stdout=stdout, stderr=stderr, env=env)

print(str(jobid))
sys.exit(0)
""".strip()


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
