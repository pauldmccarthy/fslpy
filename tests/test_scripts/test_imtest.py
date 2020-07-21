#!/usr/bin/env python
#
# test_imtest.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os
import os.path as op

import fsl.utils.path     as fslpath
from   fsl.utils.tempdir  import tempdir

import fsl.scripts.imtest as imtest

from tests import CaptureStdout, touch


def test_wrongargs():
    cap = CaptureStdout()
    with cap:
        assert imtest.main([]) == 0
    assert cap.stdout.strip() == '0'


def test_imtest():
    # (files, input, expected)
    tests = [
        ('a.nii', 'a',        '1'),
        ('a.nii', 'a.nii',    '1'),
        ('a.nii', 'a.nii.gz', '1'), # imtest is suffix-agnostic

        ('a.img a.hdr', 'a',     '1'),
        ('a.img a.hdr', 'a.img', '1'),
        ('a.img a.hdr', 'a.hdr', '1'),
        ('a.img',       'a',     '0'),
        ('a.img',       'a.img', '0'),
        ('a.img',       'a.hdr', '0'),
        ('a.hdr',       'a',     '0'),
        ('a.hdr',       'a.img', '0'),
        ('a.hdr',       'a.hdr', '0'),

        ('dir/a.nii',           'dir/a', '1'),
        ('dir/a.img dir/a.hdr', 'dir/a', '1'),
    ]

    for files, input, expected in tests:
        with tempdir():
            for f in files.split():
                dirname = op.dirname(f)
                if dirname != '':
                    os.makedirs(dirname, exist_ok=True)
                touch(f)

            cap = CaptureStdout()
            with cap:
                assert imtest.main([input]) == 0

            assert cap.stdout.strip() == expected

    # test that sym-links are
    # followed correctly
    with tempdir():
        touch('image.nii.gz')
        os.symlink('image.nii.gz', 'link.nii.gz')
        cap = CaptureStdout()
        with cap:
            assert imtest.main(['link']) == 0
        assert cap.stdout.strip() == '1'

    # sym-links in sub-directories
    # (old imtest would not work
    # in this scenario)
    with tempdir():
        os.mkdir('subdir')
        impath = op.join('subdir', 'image.nii.gz')
        lnpath = op.join('subdir', 'link.nii.gz')
        touch(impath)
        os.symlink('image.nii.gz', lnpath)
        cap = CaptureStdout()
        with cap:
            assert imtest.main([lnpath]) == 0
        assert cap.stdout.strip() == '1'
