#!/usr/bin/env python
#
# test_remove_ext.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import fsl.scripts.remove_ext as remove_ext

from tests import CaptureStdout

def test_usage():
    assert remove_ext.main([]) != 0

def test_remove_ext():
    # (input, expected output)
    tests = [
        ('a',                 'a'),
        ('a.nii',             'a'),
        ('a.nii.gz',          'a'),
        ('a.txt',             'a.txt'),
        ('a.nii b.img c.hdr', 'a b c'),
        ('a.nii b.img b.hdr', 'a b b'),
        ('a b.img c.txt',     'a b c.txt'),
        ('a.nii.gz b c.mnc',  'a b c'),
    ]

    for input, expected in tests:

        cap = CaptureStdout()
        with cap:
            ret = remove_ext.main(input.split())

        assert ret == 0

        got = cap.stdout.split()
        assert sorted(got) == sorted(expected.split())
