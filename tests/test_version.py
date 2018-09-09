#!/usr/bin/env python
#
# test_version.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op
import            textwrap

import pytest

from . import testdir

import fsl.version as fslversion


def test_parseVersionString():

    tests = [
        ('0.0.0',                [0,   0, 0]),
        ('0.0.10',               [0,   0, 10]),
        ('10.0.10',              [10,  0, 10]),
        ('10.10.10',             [10, 10, 10]),
        ('10.10.10.dev',         [10, 10, 10]),
        ('10.10.10.dev0',        [10, 10, 10]),
        ('10.10.10.dev0',        [10, 10, 10]),
        ('10.10.10+build1',      [10, 10, 10]),
        ('10.10.10+buildB',      [10, 10, 10]),
        ('10.10.10.dev0+build4', [10, 10, 10]),


        # old-style hotfix release numbers
        ('10.10.10a',    [10, 10, 10]),
        ('10.10.10dev',  [10, 10, 10]),
    ]

    for verstr, expected in tests:
        assert fslversion.parseVersionString(verstr) == expected


def test_parseVersionString_bad():

    tests = [
        '5',
        '5.5',
        '5.5.5.5',
        '5.5.5.abc',
        '5.a.5',
        'a.5.5',
        '5.5.a',
        '5.5.a',
        '5.5+build0',
    ]

    for test in tests:
        with pytest.raises(Exception):
            fslversion.parseVersionString(test)


def test_compareVersions():
    tests = [
        ('0.0.0',    '0.0.0',    0),
        ('0.0.10',   '0.0.10',   0),
        ('0.10.0',   '0.10.0',   0),
        ('10.0.0',   '10.0.0',   0),
        ('10.0.10',  '10.0.10',  0),
        ('10.10.0',  '10.10.0',  0),
        ('10.10.10', '10.10.10', 0),

        ('0.0.0',  '0.0.1',  -1),
        ('0.0.0',  '0.1.0',  -1),
        ('0.0.5',  '0.1.0',  -1),
        ('0.0.5',  '0.1.5',  -1),
        ('0.0.5',  '0.1.10', -1),

        ('0.0.0',  '1.0.0',  -1),
        ('0.0.5',  '1.0.0',  -1),
        ('0.0.5',  '1.0.5',  -1),
        ('0.0.5',  '1.0.10', -1),

        ('0.1.0',  '0.1.1',  -1),
        ('0.1.1',  '0.1.2',  -1),
        ('0.1.10', '0.2.0',  -1),

        ('0.9.9', '1.0.0', -1),
        ('0.9.9', '1.9.9', -1),
        ('1.9.9', '2.0.0', -1),
    ]

    for v1, v2, expected in tests:
        assert fslversion.compareVersions(v1, v2) ==  expected
        assert fslversion.compareVersions(v2, v1) == -expected

def test_compareVersions_ignorePoint():

    tests = [

        ('0.0.0', '0.0.0',   0),
        ('0.0.0', '0.0.5',   0),
        ('0.0.0', '0.1.0',  -1),
        ('0.0.0', '0.1.5',  -1),

        ('0.1.0', '0.1.10',  0),
        ('0.1.0', '0.2.0',  -1),
        ('0.1.0', '0.2.10', -1),

        ('1.0.0', '1.0.10',  0),
        ('1.0.0', '1.0.10',  0),
        ('1.0.0', '1.1.0',  -1),
        ('1.0.0', '1.1.10', -1),
        ('1.0.0', '2.0.0',  -1),
        ('1.0.0', '2.0.10', -1),
    ]


    for v1, v2, expected in tests:
        assert fslversion.compareVersions(v1, v2, ignorePoint=True) ==  expected
        assert fslversion.compareVersions(v2, v1, ignorePoint=True) == -expected


def test_patchVersion():

    intext = textwrap.dedent("""
    line 1
    # line 2
    version = bob
    __version__ = abcde
    __version__ = '0.1.2'
    """).strip()

    newver  = '1.2.3'
    exptext = textwrap.dedent("""
    line 1
    # line 2
    version = bob
    __version__ = abcde
    __version__ = '1.2.3'
    """).strip()

    with testdir() as td:

        testfile = op.join(td, 'file.txt')

        with open(testfile, 'wt') as f:
            f.write(intext)

        fslversion.patchVersion(testfile, newver)

        with open(testfile, 'rt') as f:
            assert f.read().strip()  == exptext
