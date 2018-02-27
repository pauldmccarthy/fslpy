#!/usr/bin/env python
#
# test_callfsl.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import               os
import os.path    as op
import subprocess as sp

import numpy      as np
import nibabel    as nib

import mock
import pytest

import fsl.utils.callfsl                  as callfsl
from   fsl.utils.platform import platform as fslplatform

import tests


pytestmark = pytest.mark.fsltest


def setup_module():
    fsldir = os.environ.get('FSLDIR', None)
    if fsldir is None or not op.exists(fsldir):
        raise Exception('FSLDIR is not set - callfsl tests cannot be run')


# mock subprocess.check_output command
# which expects 'fslstats -m filename'
# or 'fslinfo ...'
def mock_check_output(args):
    if args[0].endswith('fslinfo'):
        return 'info'.encode('utf-8')

    img = nib.load(args[-2])
    return str(img.get_data().mean()).encode('utf-8')


def test_callfsl():

    with tests.testdir() as testdir:

        fname = op.join(testdir, 'myimage.nii.gz')

        img   = tests.make_random_image(fname)
        img   = img.get_data()

        # Pass a single string
        cmd    = 'fslstats {} -m'.format(fname)

        with mock.patch('fsl.utils.callfsl.sp.check_output',
                        mock_check_output):
            result = callfsl.callFSL(cmd)

            assert np.isclose(float(result), img.mean())

            # Or pass a list of args
            result = callfsl.callFSL(*cmd.split())
            assert np.isclose(float(result), img.mean())

        # Bad commands
        badcmds = ['fslblob', 'fslstats notafile']

        for cmd in badcmds:
            with pytest.raises((OSError, sp.CalledProcessError)):
                callfsl.callFSL(cmd)

        # No FSL - should crash
        cmd = 'fslinfo {}'.format(fname)
        with mock.patch('fsl.utils.callfsl.sp.check_output',
                        mock_check_output):
            callfsl.callFSL(cmd)
        fslplatform.fsldir = None
        with pytest.raises(Exception):
            callfsl.callFSL(cmd)
