#!/usr/bin/env python
#
# test_imln.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os
import os.path as op
from unittest import mock

import pytest

from   fsl.utils.tempdir import tempdir
import fsl.utils.path    as     fslpath
import fsl.scripts.imln  as     imln

from tests import touch


def test_usage():
    assert imln.main([]) != 0
    with mock.patch('sys.argv', []):
        assert imln.main() != 0


def test_imln():

    # (files, command, expected links)
    tests = [
        ('a.nii',    'a.nii    link.nii',    'link.nii'),
        ('a.nii',    'a        link',        'link.nii'),
        ('a.nii',    'a.nii    link',        'link.nii'),
        ('a.nii',    'a        link.nii',    'link.nii'),
        ('a.nii',    'a        link.nii.gz', 'link.nii'),
        ('a.nii.gz', 'a.nii.gz link.nii.gz', 'link.nii.gz'),
        ('a.nii.gz', 'a        link',        'link.nii.gz'),
        ('a.nii.gz', 'a.nii.gz link',        'link.nii.gz'),
        ('a.nii.gz', 'a        link.nii.gz', 'link.nii.gz'),
        ('a.nii.gz', 'a        link.nii',    'link.nii.gz'),

        ('a.img a.hdr', 'a      link',     'link.img link.hdr'),
        ('a.img a.hdr', 'a      link.img', 'link.img link.hdr'),
        ('a.img a.hdr', 'a      link.hdr', 'link.img link.hdr'),
        ('a.img a.hdr', 'a.img  link',     'link.img link.hdr'),
        ('a.img a.hdr', 'a.hdr  link',     'link.img link.hdr'),
        ('a.img a.hdr', 'a.img  link.img', 'link.img link.hdr'),
        ('a.img a.hdr', 'a.hdr  link.hdr', 'link.img link.hdr'),
        ('a.img a.hdr', 'a.img  link.hdr', 'link.img link.hdr'),
        ('a.img a.hdr', 'a.hdr  link.img', 'link.img link.hdr'),
    ]


    for files, command, explinks in tests:
        with tempdir():
            files    = files.split()
            command  = command.split()
            explinks = explinks.split()

            for f in files:
                touch(f)

            assert imln.main(command) == 0

            assert sorted(os.listdir('.')) == sorted(files + explinks)

            for f, l in zip(sorted(files), sorted(explinks)):
                assert op.islink(l)
                assert op.isfile(f) and not op.islink(f)
                assert op.realpath(l) == op.abspath(f)


    # subdirs - imln currently only
    # works with absolute paths (we
    # make all paths absolute below)
    tests = [
        ('dir/a.nii',           'dir/a dir/link', 'dir/link.nii'),
        ('dir/a.img dir/a.hdr', 'dir/a dir/link', 'dir/link.img dir/link.hdr'),
        ('dir/a.nii',           'dir/a link',     'link.nii'),
        ('dir/a.img dir/a.hdr', 'dir/a link',     'link.img link.hdr'),
        ('a.nii',               'a     dir/link', 'dir/link.nii'),
        ('a.img a.hdr',         'a     dir/link', 'dir/link.img dir/link.hdr'),
    ]
    for files, command, explinks in tests:
        with tempdir():
            files    = files.split()
            command  = [op.abspath(c) for c in command.split()]
            explinks = explinks.split()

            os.mkdir('dir')

            for f in files:
                touch(f)

            assert imln.main(command) == 0

            for f, l in zip(sorted(files), sorted(explinks)):
                assert op.islink(l)
                assert op.isfile(f) and not op.islink(f)
                assert op.realpath(l) == op.abspath(f)

    # error cases
    # (files, commnad)
    tests = [
        ('a.img',             'a link'),
        ('a.nii a.img a.hdr', 'a link'),
    ]
    for files, command in tests:
        with tempdir():
            files   = files.split()
            command = command.split()

            for f in files:
                touch(f)

            assert imln.main(command) != 0
            assert sorted(os.listdir('.')) == sorted(files)
