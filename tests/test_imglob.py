#!/usr/bin/env python
#
# test_imglob.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import pytest

import fsl.scripts.imglob as imglob

from . import testdir


def test_imglob_shouldPass():

    # (files to create, paths, output, expected)
    tests = [

        # normal usage, one file
        ('file.hdr file.img', 'file',  None,     'file'),
        ('file.hdr file.img', 'file', 'prefix',  'file'),
        ('file.hdr file.img', 'file', 'primary', 'file.hdr'),
        ('file.hdr file.img', 'file', 'all',     'file.hdr file.img'),

        # incomplete file pair
        ('file.hdr', 'file',               'prefix',  'file'),
        ('file.hdr', 'file.hdr',           'prefix',  'file'),
        ('file.hdr', 'file.img',           'prefix',  'file'),
        ('file.hdr', 'file',               'primary', 'file.hdr'),
        ('file.hdr', 'file.hdr',           'primary', 'file.hdr'),
        ('file.hdr', 'file.img',           'primary', 'file.hdr'),
        ('file.hdr', 'file',               'all',     'file.hdr'),
        ('file.hdr', 'file.hdr',           'all',     'file.hdr'),
        ('file.hdr', 'file.img',           'all',     'file.hdr'),

        # same file specified multiple times
        ('file.hdr file.img', 'file file',              'prefix',  'file'),
        ('file.hdr file.img', 'file file.img',          'prefix',  'file'),
        ('file.hdr file.img', 'file file.img file.hdr', 'prefix',  'file'),
        ('file.hdr file.img', 'file file',              'primary', 'file.hdr'),
        ('file.hdr file.img', 'file file.img',          'primary', 'file.hdr'),
        ('file.hdr file.img', 'file file.img file.hdr', 'primary', 'file.hdr'),
        ('file.hdr file.img', 'file file',              'all',     'file.hdr file.img'),
        ('file.hdr file.img', 'file file.img',          'all',     'file.hdr file.img'),
        ('file.hdr file.img', 'file file.img file.hdr', 'all',     'file.hdr file.img'),

        # multiple files same prefix
        ('file.hdr file.img file.nii', 'file', 'prefix',  'file'),
        ('file.hdr file.img file.nii', 'file', 'primary', 'file.hdr file.nii'),
        ('file.hdr file.img file.nii', 'file', 'all',     'file.hdr file.img file.nii'),

        # multiple files
        ('file1.hdr file1.img file2.nii', 'file1', 'prefix',  'file1'),
        ('file1.hdr file1.img file2.nii', 'file1', 'primary', 'file1.hdr'),
        ('file1.hdr file1.img file2.nii', 'file1', 'all',     'file1.hdr file1.img'),

        ('file1.hdr file1.img file2.nii', 'file1 file2', 'prefix',  'file1 file2'),
        ('file1.hdr file1.img file2.nii', 'file1 file2', 'primary', 'file1.hdr file2.nii'),
        ('file1.hdr file1.img file2.nii', 'file1 file2', 'all',     'file1.hdr file1.img file2.nii'),

        # no file
        ('file.nii', 'bag', 'prefix',  ''),
        ('file.nii', 'bag', 'primary', ''),
        ('file.nii', 'bag', 'all',     ''),

        # incomplete prefix
        ('file.nii', 'fi', 'prefix',  ''),
        ('file.nii', 'fi', 'primary', ''),
        ('file.nii', 'fi', 'all',     ''),
    ]


    for to_create, paths, output, expected in tests:
        with testdir(to_create.split()) as td:

            paths    = paths.split()
            expected = expected.split()
            result   = imglob.imglob(paths, output)

            assert sorted(result) == sorted(expected)


def test_imglob_shouldFail():

    with pytest.raises(ValueError):
        imglob.imglob([], 'bag')
