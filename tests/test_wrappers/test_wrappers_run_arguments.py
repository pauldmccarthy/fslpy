#!/usr/bin/env python
#
# Test that arguments intended for fsl.utils.run.run are passed
# through correctly by wrapper functions

import os
import os.path as op

from io import StringIO

from unittest import mock

import pytest

import fsl.utils.tempdir         as tempdir
import fsl.wrappers              as wrappers
import fsl.wrappers.wrapperutils as wutils

from .. import CaptureStdout


mock_command = """
#!/usr/bin/env bash

echo     "Standard output"
>&2 echo "Standard error"

exit {exitcode}
""".strip()


def create_mock_command(exitcode):
    with open('mock_command', 'wt') as f:
        f.write(mock_command.format(exitcode=exitcode))
    os.chmod('mock_command', 0o777)


@wutils.cmdwrapper
def command():
    return ['mock_command']

command_fot = wutils.fileOrImage()(command)

def run_command(fileorthing, expect=None, *args, **kwargs):
    if fileorthing: result = command_fot(*args, **kwargs)
    else:           result = command(    *args, **kwargs)

    if expect is None:
        return

    if fileorthing:
        if 'submit' in kwargs or 'cmdonly' in kwargs:
            assert result == expect
        else:
            assert result.stdout == expect
    else:
        assert result == expect


@pytest.mark.parametrize('fileorthing', [True, False])
def test_stdout_stderr_exitcode(fileorthing):
    newpath = op.pathsep.join(('.', os.environ['PATH']))
    with tempdir.tempdir(), \
         mock.patch.dict(os.environ, {'PATH' : newpath}):

        create_mock_command(0)

        # default: stdout=true, stderr=true, exitcode=False
        run_command(fileorthing, ('Standard output\n', 'Standard error\n'))

        run_command(
            fileorthing,
            ('Standard output\n', 'Standard error\n', 0),
            exitcode=True)

        run_command(fileorthing, 'Standard error\n',  stdout=False)
        run_command(fileorthing, 'Standard output\n', stderr=False)

        # exitcode=False will cause an error
        # to be raised on non-0 exit codes
        create_mock_command(99)
        with pytest.raises(RuntimeError):
            run_command(fileorthing)

        run_command(fileorthing,
                    ('Standard output\n', 'Standard error\n', 99),
                    exitcode=True)


@pytest.mark.parametrize('fileorthing', [True, False])
def test_log(fileorthing):
    newpath = op.pathsep.join(('.', os.environ['PATH']))
    with tempdir.tempdir(), \
         mock.patch.dict(os.environ, {'PATH' : newpath}):

        # default: stdout/err is teed to current process
        create_mock_command(0)
        with CaptureStdout() as cap:
            run_command(fileorthing, None)
        assert cap.stdout == 'Standard output\n'
        assert cap.stderr == 'Standard error\n'

        # disable tee
        with CaptureStdout() as cap:
            result = run_command(
                fileorthing,
                ('Standard output\n', 'Standard error\n'),
                log={'tee' : False})
        assert cap.stdout == ''
        assert cap.stderr == ''

        # forward stdout/err somewhere
        # else, and record command
        stdout = StringIO()
        stderr = StringIO()
        cmd    = StringIO()

        with CaptureStdout() as cap:
            result = run_command(
                fileorthing,
                ('Standard output\n', 'Standard error\n'),
                log={'stdout' : stdout,
                     'stderr' : stderr,
                     'cmd'    : cmd})
        assert cap.stdout == 'Standard output\n'
        assert cap.stderr == 'Standard error\n'
        stdout.seek(0)
        stderr.seek(0)
        cmd   .seek(0)
        assert stdout.read() == 'Standard output\n'
        assert stderr.read() == 'Standard error\n'
        assert cmd   .read() == 'mock_command\n'


@pytest.mark.parametrize('fileorthing', [True, False])
def test_cmdonly(fileorthing):
    newpath = op.pathsep.join(('.', os.environ['PATH']))
    with tempdir.tempdir(), \
         mock.patch.dict(os.environ, {'PATH' : newpath}):

        create_mock_command(0)
        run_command(fileorthing, ['mock_command'], cmdonly=True)


@pytest.mark.parametrize('fileorthing', [True, False])
def test_wrapperconfig(fileorthing):
    newpath = op.pathsep.join(('.', os.environ['PATH']))
    with tempdir.tempdir(), \
         mock.patch.dict(os.environ, {'PATH' : newpath}):

        create_mock_command(0)

        # default: stdout=true, stderr=true, exitcode=False
        run_command(fileorthing, ('Standard output\n', 'Standard error\n'))

        with wrappers.wrapperconfig(stdout=False):
            run_command(fileorthing, 'Standard error\n')
            run_command(fileorthing, ('Standard error\n', 0), exitcode=True)

        with wrappers.wrapperconfig(stderr=False):
            run_command(fileorthing, 'Standard output\n')
            run_command(fileorthing, ('Standard output\n', 0), exitcode=True)

        # check that default behaviour is restored
        run_command(fileorthing, ('Standard output\n', 'Standard error\n'))
