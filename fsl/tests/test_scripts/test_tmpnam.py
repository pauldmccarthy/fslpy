#!/usr/bin/env python
"""Unit tests for the tmpnam utility.

These tests periodically  reset the ``tempfile.tempdir`` cache. This may
be dangerous, but doesn't seem to cause  me any problems.
"""


import contextlib
import os
import os.path as op
import tempfile

from unittest import mock

import pytest

from fsl.utils.tempdir import indir

from fsl.tests import CaptureStdout

from fsl.scripts import tmpnam


@contextlib.contextmanager
def reset_tempfile():
    try:
        tempfile.tempdir = None
        yield
    finally:
        tempfile.tempdir = None


# call tmpnam, expect it to work, check that
# a new file with prefix "expect" was created
def expect_success(args, env, expect):

    result = None

    try:

        with reset_tempfile(), \
             CaptureStdout() as cap, \
             mock.patch.dict(os.environ, env, clear=True):
            assert tmpnam.main(args) == 0

        result = cap.stdout.strip()

        print(f'Command: tmpnam {" ".join(args)}')
        print(f'Result:  {result}')

        assert op.exists(result), result
        assert result.startswith(expect), (result, expect)

    finally:
        if result is not None and op.exists(result):
            os.remove(result)


# call tmpnam, expect it to fail
def expect_failure(args, env):

    with reset_tempfile(), \
         mock.patch.dict(os.environ, env, clear=True):
        assert tmpnam.main(args) != 0


def test_without_tmpdir():

    env = os.environ.copy()
    env.pop('TMPDIR', None)

    with tempfile.TemporaryDirectory() as scratch, \
        indir(scratch):

        scratch = op.abspath(op.realpath(scratch))

        somedir = op.join(scratch, 'somedir').rstrip('/')
        os.mkdir(somedir)

        # Note: Assuming that tempfile will revert
        # to /tmp/ if the $TMPDIR variable is not
        # set. This is platform dependent.
        expect_success([],                           env, '/tmp/fsl_')
        expect_success(['prefix'],                   env, f'{scratch}/prefix_')
        expect_success(['somedir'],                  env, f'{somedir}_')
        expect_success(['somedir/'],                 env, f'{somedir}/fsl_')
        expect_success(['somedir/prefix'],           env, f'{somedir}/prefix_')
        expect_success([op.join(somedir, 'prefix')], env, f'{somedir}/prefix_')

        expect_failure(['non/existent/dir'],    env)
        expect_failure(['/non/existent/dir'],   env)
        expect_failure(['too', 'many', 'args'], env)


def test_with_tmpdir():

    with tempfile.TemporaryDirectory() as scratch, \
        indir(scratch):

        scratch = op.abspath(op.realpath(scratch))

        tmpdir  = op.join(scratch, 'tmpdir') .rstrip('/')
        somedir = op.join(scratch, 'somedir').rstrip('/')

        env = os.environ.copy()
        env['TMPDIR'] = tmpdir

        os.mkdir(tmpdir)
        os.mkdir(somedir)

        expect_success([],                 env, f'{tmpdir}/fsl_')
        expect_success(['/tmp/']      ,    env, f'{tmpdir}/fsl_')
        expect_success(['/tmp/prefix'],    env, f'{tmpdir}/prefix_')
        expect_success(['prefix'],         env, f'{scratch}/prefix_')
        expect_success(['somedir'],        env, f'{scratch}/somedir_')
        expect_success(['somedir/'],       env, f'{somedir}/fsl_')
        expect_success(['somedir/prefix'], env, f'{somedir}/prefix_')
