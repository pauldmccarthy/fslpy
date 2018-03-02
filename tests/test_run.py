#!/usr/bin/env python
#
# test_run.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path as op
import            os
import            textwrap

# python 3
try:  from unittest import mock
# python 2
except ImportError: import mock

import pytest

import fsl.utils.tempdir                  as tempdir
from   fsl.utils.platform import platform as fslplatform
import fsl.utils.run                      as run

from . import make_random_image


def test_run():

    test_script = textwrap.dedent("""
    #!/bin/bash

    echo "standard output - arguments: $@"
    echo "standard error" >&2
    exit {}
    """).strip()

    with tempdir.tempdir():

        # return code == 0
        with open('script.sh', 'wt') as f:
            f.write(test_script.format(0))
        os.chmod('script.sh', 0o755)

        expstdout = "standard output - arguments: 1 2 3"
        expstderr = "standard error"

        # test:
        #   - single string
        #   - packed sequence
        #   - unpacked sequence
        assert run.run('./script.sh 1 2 3').strip() == expstdout
        assert run.run(('./script.sh', '1', '2', '3')) == expstdout
        assert run.run(*('./script.sh', '1', '2', '3')) == expstdout

        # test stdout/stderr
        stdout, stderr = run.run('./script.sh 1 2 3', err=True)
        assert stdout.strip() == expstdout
        assert stderr.strip() == expstderr

        # test return code
        stdout, ret = run.run('./script.sh 1 2 3', ret=True)
        assert stdout.strip() == expstdout
        assert ret == 0
        stdout, stderr, ret = run.run('./script.sh 1 2 3', err=True, ret=True)
        assert stdout.strip() == expstdout
        assert stderr.strip() == expstderr
        assert ret == 0

        # return code != 0
        with open('./script.sh', 'wt') as f:
            f.write(test_script.format(255))
        os.chmod('./script.sh', 0o755)

        with pytest.raises(RuntimeError):
            run.run('./script.sh 1 2 3')

        stdout, ret = run.run('./script.sh 1 2 3', ret=True)
        assert stdout.strip() == expstdout
        assert ret == 255


def test_dryrun():

    test_script = textwrap.dedent("""
    #!/bin/bash
    touch foo
    """).strip()

    with tempdir.tempdir():
        with open('./script.sh', 'wt') as f:
            f.write(test_script)
        os.chmod('./script.sh', 0o755)

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
    echo $@
    exit 0
    """).strip()

    old_fsldir = fslplatform.fsldir

    try:
        with tempdir.tempdir():

            make_random_image('image.nii.gz')

            # no FSLDIR - should error
            fslplatform.fsldir = None
            with pytest.raises(run.FSLNotPresent):
                run.runfsl('fslhd image')


            # FSLDIR/bin exists - should be good
            fsldir = op.abspath('./fsl')
            fslhd  = op.join(fsldir, 'bin', 'fslhd')
            os.makedirs(op.join(fsldir, 'bin'))
            with open(fslhd, 'wt') as f:
                f.write(test_script)
            os.chmod(fslhd, 0o777)

            fslplatform.fsldir = fsldir
            path = op.pathsep.join((fsldir, os.environ['PATH']))
            with mock.patch.dict(os.environ, {'PATH' : path}):
                assert run.runfsl('fslhd image').strip() == 'image'
    finally:
        fslplatform.fsldir = old_fsldir
