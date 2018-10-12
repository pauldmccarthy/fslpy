#!/usr/bin/env python
#
# test_vest.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path as op
import            shutil
import            tempfile
import            warnings

import numpy   as np
import            pytest

import fsl.data.vest as vest


testfile1 = """%!VEST-LUT
%%BeginInstance
<<
/SavedInstanceClassName /ClassLUT
/PseudoColorMinimum 0.00
/PseudoColorMaximum 1.00
/PseudoColorMinControl /Low
/PseudoColorMaxControl /High
/PseudoColormap [
<-color{0.00,0.00,0.00}->
<-color{0.01,0.01,0.01}->
<-color{0.02,0.02,0.02}->
<-color{0.03,0.03,0.03}->
<-color{0.04,0.04,0.04}->
]
>>

%%EndInstance
%%EOF
"""
testfile1Colours = np.array([
    [0.00, 0.00, 0.00],
    [0.01, 0.01, 0.01],
    [0.02, 0.02, 0.02],
    [0.03, 0.03, 0.03],
    [0.04, 0.04, 0.04]])


testfile2 = """%!VEST-LUT
%%BeginInstance
<<
/SavedInstanceClassName /ClassLUT
/PseudoColorMinimum 0.00
/PseudoColorMaximum 1.00
/PseudoColorMinControl /Low
/PseudoColorMaxControl /High
/PseudoColormap [
<-color{0.0,0.0,0.0}->
]
>>

%%EndInstance
%%EOF
"""
testfile2Colours = np.array([[0.0, 0.0, 0.0]])


testfile3 = """%!VEST-LUT
%%BeginInstance
<<
/PseudoColormap [
<-color{0.0,0.0,0.0}->
<-color{0.5,0.2,0.6}->
]
>>

%%EndInstance
%%EOF
"""
testfile3Colours = np.array([
    [0.0, 0.0, 0.0],
    [0.5, 0.2, 0.6]])


testfile4 = """%!VEST-LUT
%%BeginInstance
<<
/SavedInstanceClassName /ClassLUT
/PseudoColorMinimum 0.00
/PseudoColorMaximum 1.00
/PseudoColorMinControl /Low
/PseudoColorMaxControl /High
/PseudoColormap [
<-color{0.0,1.0,5.0}->
<-color{1.0,2.0,4.0}->
<-color{2.0,3.0,3.0}->
<-color{3.0,4.0,2.0}->
<-color{4.0,5.0,1.0}->
]
>>

%%EndInstance
%%EOF
"""
testfile4Colours = np.array([
    [0.0, 1.0, 5.0],
    [1.0, 2.0, 4.0],
    [2.0, 3.0, 3.0],
    [3.0, 4.0, 2.0],
    [4.0, 5.0, 1.0]])


testfile5 = """Obviously not a VEST file"""


def _createFiles(testdir):

    names = ['testfile1', 'testfile2', 'testfile3', 'testfile4', 'testfile5']
    texts = [ testfile1,   testfile2,   testfile3,   testfile4,   testfile5]

    for name, text in zip(names, texts):
        filename = op.join(testdir, '{}.txt'.format(name))
        with open(filename, 'wt') as f:
            f.write(text)



def test_looksLikeVestLutFile():

    testdir = tempfile.mkdtemp()

    try:

        _createFiles(testdir)

        assert     vest.looksLikeVestLutFile(op.join(testdir, 'testfile1.txt'))
        assert     vest.looksLikeVestLutFile(op.join(testdir, 'testfile2.txt'))
        assert     vest.looksLikeVestLutFile(op.join(testdir, 'testfile3.txt'))
        assert     vest.looksLikeVestLutFile(op.join(testdir, 'testfile4.txt'))
        assert not vest.looksLikeVestLutFile(op.join(testdir, 'testfile5.txt'))

    finally:
        shutil.rmtree(testdir)


def test_loadVestLutFile():

    testdir   = tempfile.mkdtemp()
    testfiles = [
        op.join(testdir, 'testfile1.txt'),
        op.join(testdir, 'testfile2.txt'),
        op.join(testdir, 'testfile3.txt'),
        op.join(testdir, 'testfile4.txt'),
        op.join(testdir, 'testfile5.txt')]
    testdata = [
        testfile1Colours,
        testfile2Colours,
        testfile3Colours,
        testfile4Colours]

    try:
        _createFiles(testdir)

        with pytest.raises(Exception):
            vest.loadVestLutFile(testfiles[4])
            vest.loadVestLutFile(testfiles[4], normalise=False)

        for i in range(4):
            f       = testfiles[i]
            d       = testdata[ i]

            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                dnorm   = (d - d.min()) / (d.max() - d.min())
                lutnorm = vest.loadVestLutFile(f)
                lut     = vest.loadVestLutFile(f, normalise=False)

            assert lut.shape     == d.shape
            assert lutnorm.shape == dnorm.shape
            assert np.all(np.isclose(lut,     d))

            if (d.max() - d.min()) != 0:
                assert np.all(np.isclose(lutnorm, dnorm))
            else:
                assert np.all(np.isnan(dnorm))
                assert np.all(np.isnan(lutnorm))

    finally:
        shutil.rmtree(testdir)
