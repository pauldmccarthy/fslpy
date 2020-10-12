#!/usr/bin/env python
#
# test_run.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path as op
import            os
import            shutil
import            textwrap

# python 3
try:  from unittest import mock
# python 2
except ImportError: import mock

import six
import pytest

import fsl.utils.tempdir                  as tempdir
from   fsl.utils.platform import platform as fslplatform
import fsl.utils.run                      as run
import fsl.utils.fslsub                   as fslsub

from . import make_random_image, mockFSLDIR, CaptureStdout


pytestmark = pytest.mark.unixtest


def mkexec(path, contents):
    with open(path, 'wt') as f:
        f.write(contents)
    os.chmod(path, 0o755)


def test_prepareArgs():
    tests = [
        ('a b c',              ['a', 'b', 'c']),
        (['a', 'b', 'c'],      ['a', 'b', 'c']),
        ('abc "woop woop"',    ['abc', 'woop woop']),
        (['abc', 'woop woop'], ['abc', 'woop woop']),
    ]

    for args, expected in tests:
        assert run.prepareArgs((args, )) == expected

def test_run():

    test_script = textwrap.dedent("""
    #!/bin/bash

    echo "standard output - arguments: $@"
    echo "standard error" >&2
    exit {}
    """).strip()

    with tempdir.tempdir():

        # return code == 0
        mkexec('script.sh', test_script.format(0))

        expstdout = "standard output - arguments: 1 2 3\n"
        expstderr = "standard error\n"

        # test:
        #   - single string
        #   - packed sequence
        #   - unpacked sequence
        assert run.run('./script.sh 1 2 3')             == expstdout
        assert run.run(('./script.sh', '1', '2', '3'))  == expstdout
        assert run.run(*('./script.sh', '1', '2', '3')) == expstdout

        # test stdout/stderr
        stdout, stderr = run.run('./script.sh 1 2 3', stderr=True)
        assert stdout == expstdout
        assert stderr == expstderr

        # test return code
        res = run.run('./script.sh 1 2 3', exitcode=True)
        stdout, ret = res
        assert stdout == expstdout
        assert ret == 0
        stdout, stderr, ret = run.run('./script.sh 1 2 3', stderr=True,
                                      exitcode=True)
        assert stdout == expstdout
        assert stderr == expstderr
        assert ret == 0

        # stdout=False
        res = run.run('./script.sh 1 2 3', stdout=False)
        assert res == ()
        stderr = run.run('./script.sh 1 2 3', stdout=False, stderr=True)
        assert stderr == expstderr

        # return code != 0
        mkexec('./script.sh', test_script.format(255))

        with pytest.raises(RuntimeError):
            run.run('./script.sh 1 2 3')

        stdout, ret = run.run('./script.sh 1 2 3', exitcode=True)
        assert stdout == expstdout
        assert ret == 255


def test_run_tee():
    test_script = textwrap.dedent("""
    #!/bin/bash

    echo "standard output - arguments: $@"
    echo "standard error" >&2
    exit 0
    """).strip()

    with tempdir.tempdir():
        mkexec('script.sh', test_script)

        expstdout = "standard output - arguments: 1 2 3\n"
        expstderr = "standard error\n"

        capture = CaptureStdout()

        with capture:
            stdout = run.run('./script.sh 1 2 3', log={'tee' : True})

        assert stdout         == expstdout
        assert capture.stdout == expstdout

        with capture.reset():
            stdout, stderr = run.run('./script.sh 1 2 3', stderr=True,
                                     log={'tee' : True})

        assert stdout         == expstdout
        assert stderr         == expstderr
        assert capture.stdout == expstdout
        assert capture.stderr == expstderr

        with capture.reset():
            stdout, stderr, ret = run.run('./script.sh 1 2 3',
                                          stderr=True,
                                          exitcode=True,
                                          log={'tee' : True})

        assert ret            == 0
        assert stdout         == expstdout
        assert stderr         == expstderr
        assert capture.stdout == expstdout
        assert capture.stderr == expstderr

        with capture.reset():
            stdout, ret = run.run('./script.sh 1 2 3',
                                  exitcode=True,
                                  log={'tee' : True})

        assert ret            == 0
        assert stdout         == expstdout
        assert capture.stdout == expstdout


def test_run_passthrough():

    test_script = textwrap.dedent("""
    #!/bin/bash

    echo "env: $RUN_TEST_ENV_VAR"
    """).strip()

    with tempdir.tempdir():

        # return code == 0
        mkexec('script.sh', test_script.format(0))

        env       = {'RUN_TEST_ENV_VAR' : 'howdy ho'}
        expstdout = "env: howdy ho\n"

        assert run.run('./script.sh', env=env) == expstdout


def test_cmdonly():
    assert run.run('script.sh',        cmdonly=True) == ['script.sh']
    assert run.run('script.sh 1 2 3',  cmdonly=True) == ['script.sh', '1', '2', '3']
    assert run.run(['script.sh'],      cmdonly=True) == ['script.sh']
    assert run.run(['script.sh', '1'], cmdonly=True) == ['script.sh', '1']


def test_dryrun():

    test_script = textwrap.dedent("""
    #!/bin/bash
    touch foo
    """).strip()

    with tempdir.tempdir():
        mkexec('./script.sh', test_script)

        run.run('./script.sh')
        assert op.exists('foo')

        os.remove('foo')

        with run.dryrun():
            run.run('./script.sh')

        assert not op.exists('foo')


# test runfsl with/without $FSLDIR
def test_runfsl():

    test_script = textwrap.dedent("""
    #!/bin/bash
    echo {}
    exit 0
    """).strip()

    old_fsldir    = fslplatform.fsldir
    old_fsldevdir = fslplatform.fsldevdir

    try:
        with tempdir.tempdir():

            make_random_image('image.nii.gz')

            # no FSLDIR - should error
            fslplatform.fsldir    = None
            fslplatform.fsldevdir = None
            with pytest.raises(run.FSLNotPresent):
                run.runfsl('fslhd')

            # FSLDIR/bin exists - should be good
            fsldir = op.abspath('./fsl')
            fslhd  = op.join(fsldir, 'bin', 'fslhd')
            os.makedirs(op.join(fsldir, 'bin'))

            mkexec(fslhd, test_script.format('fsldir'))

            fslplatform.fsldir = fsldir
            assert run.runfsl('fslhd').strip() == 'fsldir'

            # non-FSL command - should error
            with pytest.raises(FileNotFoundError):
                run.runfsl('ls')

            # FSLDEVDIR should take precedence
            fsldevdir = './fsldev'
            fslhd  = op.join(fsldevdir, 'bin', 'fslhd')
            shutil.copytree(fsldir, fsldevdir)

            mkexec(fslhd, test_script.format('fsldevdir'))

            fslplatform.fsldevdir = fsldevdir
            fslplatform.fsldir    = None
            assert run.runfsl('fslhd').strip() == 'fsldevdir'

            # FSL_PREFIX should override all
            override = './override'
            fslhd    = op.join(override, 'fslhd')
            os.makedirs(override)
            mkexec(fslhd, test_script.format('override'))

            fslplatform.fsldir    = None
            fslplatform.fsldevdir = None
            run.FSL_PREFIX = override
            assert run.runfsl('fslhd').strip() == 'override'

    finally:
        fslplatform.fsldir    = old_fsldir
        fslplatform.fsldevdir = old_fsldevdir
        run.FSL_PREFIX        = None


def mock_submit(cmd, **kwargs):
    if isinstance(cmd, six.string_types):
        name = cmd.split()[0]
    else:
        name = cmd[0]

    name = op.basename(name)

    jid = '12345'
    output = run.run(cmd)

    with open('{}.o{}'.format(name, jid), 'wt') as f:
        f.write(output)

    with open('{}.e{}'.format(name, jid), 'wt') as f:
        for k in sorted(kwargs.keys()):
            f.write('{}: {}\n'.format(k, kwargs[k]))

    return jid


def test_run_submit():

    def mkexec(path, contents):
        with open(path, 'wt') as f:
            f.write(contents)
        os.chmod(path, 0o755)

    test_script = textwrap.dedent("""
    #!/usr/bin/env bash
    echo test_script running
    exit 0
    """).strip()

    with tempdir.tempdir(), \
         mockFSLDIR(), \
         mock.patch('fsl.utils.fslsub.submit', mock_submit):

        mkexec(op.expandvars('$FSLDIR/bin/fsltest'), test_script)

        jid = run.run('fsltest', submit=True)
        assert jid == '12345'
        stdout, stderr = fslsub.output(jid)
        assert stdout == 'test_script running\n'
        assert stderr == ''

        # or can pass submit opts as a dict
        kwargs = {'name' : 'abcde', 'ram' : '4GB'}
        jid = run.run('fsltest', submit=kwargs)
        assert jid == '12345'
        stdout, stderr = fslsub.output(jid)
        experr = '\n'.join(['{}: {}'.format(k, kwargs[k])
                            for k in sorted(kwargs.keys())]) + '\n'
        assert stdout == 'test_script running\n'
        assert stderr == experr

        # or can pass submit opts as kwargs
        kwargs = {'name' : 'abcde', 'ram' : '4GB'}
        jid = run.run('fsltest', submit=True, **kwargs)
        assert jid == '12345'
        stdout, stderr = fslsub.output(jid)
        experr = '\n'.join(['{}: {}'.format(k, kwargs[k])
                            for k in sorted(kwargs.keys())]) + '\n'
        assert stdout == 'test_script running\n'
        assert stderr == experr



def test_run_streams():
    """
    """

    test_script = textwrap.dedent("""
    #!/usr/bin/env bash
    echo standard output
    echo standard error >&2
    exit 0
    """).strip()

    expstdout = 'standard output\n'
    expstderr = 'standard error\n'

    with tempdir.tempdir():
        mkexec('./script.sh', test_script)

        with open('my_stdout', 'wt') as stdout, \
             open('my_stderr', 'wt') as stderr:

            stdout, stderr = run.run('./script.sh',
                                     stderr=True,
                                     log={'stdout' : stdout,
                                          'stderr' : stderr})

        assert stdout                         == expstdout
        assert stderr                         == expstderr
        assert open('my_stdout', 'rt').read() == expstdout
        assert open('my_stderr', 'rt').read() == expstderr


        capture = CaptureStdout()

        with open('my_stdout', 'wt') as stdout, \
             open('my_stderr', 'wt') as stderr, \
             capture.reset():

            stdout, stderr = run.run('./script.sh',
                                     stderr=True,
                                     log={'tee'    : True,
                                          'stdout' : stdout,
                                          'stderr' : stderr})

        assert stdout                         == expstdout
        assert stderr                         == expstderr
        assert capture.stdout                 == expstdout
        assert capture.stderr                 == expstderr
        assert open('my_stdout', 'rt').read() == expstdout
        assert open('my_stderr', 'rt').read() == expstderr


def test_run_logcmd():
    test_script = textwrap.dedent("""
    #!/usr/bin/env bash
    echo output $@
    exit 0
    """).strip()

    expcmd = './script.sh 1 2 3\n'
    expstdout = 'output 1 2 3\n'

    with tempdir.tempdir():
        mkexec('script.sh', test_script)

        with open('my_stdout', 'wt') as stdoutf:
            stdout = run.run('./script.sh 1 2 3',
                             log={'cmd' : stdoutf})

        assert stdout                         == expstdout
        assert open('my_stdout', 'rt').read() == expcmd

        with open('my_stdout', 'wt') as stdoutf:
            stdout = run.run('./script.sh 1 2 3',
                             log={'cmd' : stdoutf, "stdout" : stdoutf})

        assert stdout                         == expstdout
        assert open('my_stdout', 'rt').read() == expcmd + expstdout
