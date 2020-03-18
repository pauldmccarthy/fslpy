#!/usr/bin/env python
#
# test_bids.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import                  json
import os.path   as     op
import itertools as     it
from   pathlib   import Path

import pytest

from fsl.utils.tempdir import tempdir
import fsl.utils.bids  as     fslbids


def test_parseFilename():
    with pytest.raises(ValueError):
        fslbids.parseFilename('bad_file.txt')

    tests = [
        ('sub-01_ses-01_t1w.nii.gz',
         ({'sub' : '01', 'ses' : '01'}, 't1w')),
        ('a-1_b-2_c-3_d-4_e.json',
         ({'a' : '1', 'b' : '2', 'c' : '3', 'd' : '4'}, 'e')),
    ]

    for filename, expect in tests:
        assert fslbids.parseFilename(filename) == expect


def test_isBIDSDir():
    with tempdir():
        assert not fslbids.isBIDSDir('.')
    with tempdir():
        Path('dataset_description.json').touch()
        assert fslbids.isBIDSDir('.')


def test_inBIDSDir():
    with tempdir():
        Path('a/b/c').mkdir(parents=True)
        Path('dataset_description.json').touch()
        assert fslbids.inBIDSDir(Path('.'))
        assert fslbids.inBIDSDir(Path('a'))
        assert fslbids.inBIDSDir(Path('a/b'))
        assert fslbids.inBIDSDir(Path('a/b/c'))
    with tempdir():
        Path('a/b/c').mkdir(parents=True)
        assert not fslbids.inBIDSDir(Path('.'))
        assert not fslbids.inBIDSDir(Path('a'))
        assert not fslbids.inBIDSDir(Path('a/b'))
        assert not fslbids.inBIDSDir(Path('a/b/c'))


def test_isBIDSFile():
    goodfiles = [
        Path('sub-01_ses-01_t1w.nii.gz'),
        Path('sub-01_ses-01_t1w.nii'),
        Path('sub-01_ses-01_t1w.json'),
        Path('a-1_b-2_c-3_d-4_e.nii.gz'),
        Path('sub-01_ses-01_t1w.txt'),
    ]
    badfiles = [
        Path('sub-01_ses-01.nii.gz'),
        Path('sub-01_ses-01_t1w'),
        Path('sub-01_ses-01_t1w.'),
        Path('sub_ses-01_t1w.nii.gz'),
        Path('sub-01_ses_t1w.nii.gz'),
    ]
    with tempdir():
        Path('dataset_description.json').touch()
        for f in goodfiles: assert     fslbids.isBIDSFile(f)
        for f in badfiles:  assert not fslbids.isBIDSFile(f)
    with tempdir():
        for f in it.chain(goodfiles, badfiles):
            assert not fslbids.isBIDSFile(f)


def test_loadMetadata():
    dd    = Path('dataset_description.json')
    t1    = Path('sub-01/func/sub-01_task-stim_bold.nii.gz')
    json1 = Path('sub-01/func/sub-01_task-stim_bold.json')
    json2 = Path('sub-01/sub-01_bold.json')
    json3 = Path('sub-01_t1w.json')
    json4 = Path('sub-01/task-stim_bold.json')
    meta1 = {'a' : '1',   'b' : '2'}
    meta2 = {'a' : '10',  'c' : '3'}
    meta3 = {'a' : '109', 'b' : '99'}
    meta4 = {'c' : '9',   'd' : '5'}

    with tempdir():
        dd.touch()
        Path(op.dirname(t1)).mkdir(parents=True)
        t1.touch()
        assert fslbids.loadMetadata(t1) == {}
        json1.write_text(json.dumps(meta1))
        assert fslbids.loadMetadata(t1) == meta1
        json2.write_text(json.dumps(meta2))
        assert fslbids.loadMetadata(t1) == {**meta2, **meta1}
        json3.write_text(json.dumps(meta3))
        assert fslbids.loadMetadata(t1) == {**meta2, **meta1}
        json4.write_text(json.dumps(meta4))
        assert fslbids.loadMetadata(t1) == {**meta4, **meta2, **meta1}
