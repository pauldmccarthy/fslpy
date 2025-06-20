#!/usr/bin/env python
#
# test_run.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path    as op
import               os
import               shutil
import               threading
import               time
import               shlex
import subprocess as sp
import textwrap   as tw

from unittest import mock

import pytest
import dill

import fsl.utils.tempdir                  as tempdir
from   fsl.utils.platform import platform as fslplatform
import fsl.utils.run                      as run
import fsl.wrappers                       as wrappers

from fsl.tests import make_random_image, mockFSLDIR, CaptureStdout, touch


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

    test_script = tw.dedent("""
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
    test_script = tw.dedent("""
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

        # default behaviour is for tee=True
        with capture:
            stdout = run.run('./script.sh 1 2 3')
        assert stdout         == expstdout
        assert capture.stdout == expstdout

        with capture.reset():
            stdout = run.run('./script.sh 1 2 3', log={'tee' : True})
        assert stdout         == expstdout
        assert capture.stdout == expstdout

        # disable forwarding
        with capture.reset():
            stdout = run.run('./script.sh 1 2 3', log={'tee' : False})
        assert stdout         == expstdout
        assert capture.stdout == ''


        # disable forwarding via silent=True
        with capture.reset():
            stdout = run.run('./script.sh 1 2 3', silent=True)
        assert stdout         == expstdout
        assert capture.stdout == ''

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

    test_script = tw.dedent("""
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

    test_script = tw.dedent("""
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

    test_script = tw.dedent("""
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


def mock_fsl_sub(*cmd, **kwargs):
    if len(cmd) == 1 and isinstance(cmd[0], str):
        name = cmd[0].split()[0]
    else:
        name = cmd[0]

    name = op.basename(name)

    kwargs.pop('log', None)

    jid = '12345'
    output = run.run(cmd)

    with open('{}.o{}'.format(name, jid), 'wt') as f:
        f.write(output)

    with open('{}.e{}'.format(name, jid), 'wt') as f:
        for k in sorted(kwargs.keys()):
            f.write('{}: {}\n'.format(k, kwargs[k]))

    return (jid, '')


def test_run_submit():

    def mkexec(path, contents):
        with open(path, 'wt') as f:
            f.write(contents)
        os.chmod(path, 0o755)

    test_script = tw.dedent("""
    #!/usr/bin/env bash
    echo test_script running
    exit 0
    """).strip()

    with tempdir.tempdir(), \
         mockFSLDIR(), \
         mock.patch('fsl.wrappers.fsl_sub', mock_fsl_sub):

        mkexec(op.expandvars('$FSLDIR/bin/fsltest'), test_script)

        jid = run.run('fsltest', submit=True)
        assert jid == '12345'
        stdout, stderr = run.job_output(jid)
        assert stdout == 'test_script running\n'
        assert stderr == ''

        # or can pass submit opts as a dict
        kwargs = {'name' : 'abcde', 'ram' : '4GB'}
        jid = run.run('fsltest', submit=kwargs)
        assert jid == '12345'
        stdout, stderr = run.job_output(jid)
        experr = '\n'.join(['{}: {}'.format(k, kwargs[k])
                            for k in sorted(kwargs.keys())]) + '\n'
        assert stdout == 'test_script running\n'
        assert stderr == experr

        # or can pass submit opts as kwargs
        kwargs = {'name' : 'abcde', 'ram' : '4GB'}
        jid = run.run('fsltest', submit=True, **kwargs)
        assert jid == '12345'
        stdout, stderr = run.job_output(jid)
        experr = '\n'.join(['{}: {}'.format(k, kwargs[k])
                            for k in sorted(kwargs.keys())]) + '\n'
        assert stdout == 'test_script running\n'
        assert stderr == experr



def test_run_streams():
    """
    """

    test_script = tw.dedent("""
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

        # logstdout/err can also be callables
        gotstdout = []
        gotstderr = []
        def logstdout(stdout):
            gotstdout.append(stdout)
        def logstderr(stderr):
            gotstderr.append(stderr)

        run.run('./script.sh',
                stdout=False,
                stderr=False,
                log={'tee'    : False,
                     'stdout' : logstdout,
                     'stderr' : logstderr})

        assert gotstdout == [expstdout]
        assert gotstderr == [expstderr]



def test_run_logcmd():
    test_script = tw.dedent("""
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

        logged = []
        def logfunc(cmd):
            logged.append(cmd)

        stdout = run.run('./script.sh 1 2 3', log={'cmd' : logfunc})
        assert stdout    == expstdout
        assert logged[0] == expcmd
        stdout = run.run('./script.sh 1 2 3', log={'cmd' : logfunc})
        assert stdout    == expstdout
        assert logged[1] == expcmd


def test_hold():

    with tempdir.tempdir():

        holdfile = op.abspath('holdfile')

        def remove_holdfile():
            time.sleep(3)
            os.remove(holdfile)

        with run.dryrun():
            threading.Thread(target=remove_holdfile).start()
            run.hold([1, 2, 3], holdfile, timeout=1)

        cmds = list(run.DRY_RUN_COMMANDS)

    # dryrun gathers all executed commands
    # in a list of (cmd, submit) tuples,
    # so we do a very simple check here
    assert len(cmds) == 1
    cmd, submit = cmds[0]
    assert cmd               == ('rm', holdfile)
    assert submit['jobhold'] == '1,2,3'


def _good_func():
    print('hello')

def _bad_func():
    1/0

def _func_returning_value():
    return [1, 2, 3, 4, 5, "six"]

def _func_reading_env():
    return os.environ['ENV_VAR']


def test_runfunc():
    assert run.runfunc(_good_func, clean='always') == 'hello\n'
    with pytest.raises(Exception):
        assert run.runfunc(_bad_func, clean='always')


def test_runfunc_save():
    with tempdir.tempdir():

        run.runfunc(_func_returning_value, tmp_dir='.', save='output.dill')

        with open('output.dill', 'rb') as f:
            result = dill.loads(f.read())
        assert result == [1, 2, 3, 4, 5, "six"]


def test_runfunc_env():
    with tempdir.tempdir():

        run.runfunc(_func_reading_env,
                    tmp_dir='.',
                    env={'ENV_VAR' : 'ENV_VALUE'},
                    save='output.dill')

        with open('output.dill', 'rb') as f:
            result = dill.loads(f.read())
        assert result == 'ENV_VALUE'


def test_func_to_cmd():
    cwd = os.getcwd()
    with tempdir.tempdir():
        for tmp_dir in (None, '.'):
            for clean in ('never', 'on_success', 'always'):
                for verbose in (False, True):
                    cmd = run.func_to_cmd(_good_func, clean=clean, tmp_dir=tmp_dir, verbose=verbose)
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
                        assert stdout.strip() == f'running "{fn}"\nhello'
                    else:
                        assert stdout.strip() == 'hello'

                cmd = run.func_to_cmd(_bad_func, clean=clean, tmp_dir=tmp_dir)
                fn = cmd.split()[-1]
                assert op.exists(fn)
                stdout, stderr, exitcode = run.run(cmd, exitcode=True, stdout=True, stderr=True,
                                                   env={'PYTHONPATH': cwd})
                assert exitcode != 0
                if clean == 'always':
                    assert not op.exists(fn), "Failing job should always be removed if requested"
                else:
                    assert op.exists(fn), f"Failing job got removed even with clean = {clean}"


def test_submitfunc():

    def func1(a1, a2):
        return a1 + a2

    def func2(a1, a2):
        raise ValueError("inputs are wrong")

    # just run the command
    def mock_fsl_sub(*cmd, **kwargs):
        sp.run(cmd)
        return '1234'

    with mock.patch('fsl.wrappers.fsl_sub', mock_fsl_sub):
        result = run.submitfunc(func1, ('123', '456'), clean='always')[0]()
        assert result == '123456'

        with pytest.raises(ValueError):
            run.submitfunc(func2, ('123', '456'), clean='always')[0]()


def test_wrapper_to_cmd():
    fn = run.func_to_cmd(wrappers.bet)
    assert op.exists(fn)
    assert op.basename(fn).startswith("bet_")


def test_job_output():
    with tempdir.tempdir() as td:
        with open('test.e12345', 'wt') as f: f.write('error')
        with open('test.o12345', 'wt') as f: f.write('output')
        assert run.job_output(12345, td) == ('output', 'error')
