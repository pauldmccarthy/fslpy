#!/usr/bin/env python
#
# test_imrm.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os

from fsl.utils.tempdir import tempdir
import fsl.scripts.imrm as imrm

from tests import touch

def test_imrm_usage():
    assert imrm.main([]) != 0


def test_imrm():
    # (files present, command, expected)
    tests = [
        ('a.nii',       'a',       ''),
        ('a.nii.gz',    'a',       ''),
        ('a.img a.hdr', 'a',       ''),
        ('a.img',       'a',       ''),
        ('a.hdr',       'a',       ''),
        ('a.nii b.nii', 'a',       'b.nii'),
        ('a.nii b.nii', 'a b',     ''),
        ('a.nii b.nii', 'a b.nii', ''),

        # suffix doesn't have to be correct
        ('a.nii.gz', 'a.nii',  ''),

        # files don't exist -> no problem
        ('a.nii', 'b',  'a.nii'),
    ]

    for files, command, expected in tests:
        with tempdir():

            for f in files.split():
                touch(f)

            print('files',    files)
            print('command',  command)
            print('expected', expected)

            ret = imrm.main(('imrm ' + command).split())

            assert ret == 0
            assert sorted(os.listdir()) == sorted(expected.split())
