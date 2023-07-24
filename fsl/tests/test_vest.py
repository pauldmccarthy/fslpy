#!/usr/bin/env python
#
# test_vest.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path  as op
import textwrap as tw
import             io
import             shutil
import             tempfile
import             warnings

import numpy    as np
import             pytest

import fsl.data.vest as vest

from tests import tempdir


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

testfile6 = """%BeginInstance
/SavedInstanceClassName /ClassLUT
/PseudoColourmap [
<-color{0.0,1.0,5.0}->
<-color{1.0,2.0,4.0}->
<-color{2.0,3.0,3.0}->
]
>>
%%EndInstance
%%EOF
"""

testfile7 = """%%BeginInstance
/SavedInstanceClassName /ClassLUT
/PseudoColourmap [
<-color{0.0,1.0,5.0}->
<-color{1.0,2.0,4.0}->
<-color{2.0,3.0,3.0}->
]
>>
%%EndInstance
%%EOF
"""


def _createFiles(testdir):

    names = ['testfile1', 'testfile2', 'testfile3', 'testfile4', 'testfile5',
             'testfile6', 'testfile7']
    texts = [ testfile1,   testfile2,   testfile3,   testfile4,   testfile5,
              testfile6,   testfile7]

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
        assert     vest.looksLikeVestLutFile(op.join(testdir, 'testfile6.txt'))
        assert     vest.looksLikeVestLutFile(op.join(testdir, 'testfile7.txt'))

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


def test_generateVest():
    def readvest(vstr):
        lines = vstr.split('\n')
        nrows = [l for l in lines if 'NumPoints' in l][0]
        ncols = [l for l in lines if 'NumWaves'  in l][0]
        nrows = int(nrows.split()[1])
        ncols = int(ncols.split()[1])
        data  = '\n'.join(lines[3:])
        data  = np.loadtxt(io.StringIO(data)).reshape((nrows, ncols))

        return ((nrows, ncols), data)

    # shape, expectedshape
    tests = [
        ((10,   ), ( 1, 10)),
        ((10,  1), (10,  1)),
        (( 1, 10), ( 1, 10)),
        (( 3,  5), ( 3,  5)),
        (( 5,  3), ( 5,  3))
    ]

    for shape, expshape in tests:
        data = np.random.random(shape)
        vstr = vest.generateVest(data)

        gotshape, gotdata = readvest(vstr)

        data = data.reshape(expshape)

        assert expshape == gotshape
        assert np.all(np.isclose(data, gotdata))


def test_loadVestFile():
    def genvest(data, path, shapeOverride=None):
        if shapeOverride is None:
            nrows, ncols = data.shape
        else:
            nrows, ncols = shapeOverride

        with open(path, 'wt') as f:
            f.write(f'/NumWaves {ncols}\n')
            f.write(f'/NumPoints {nrows}\n')
            f.write( '/Matrix\n')

            if np.issubdtype(data.dtype, np.integer): fmt = '%d'
            else:                                     fmt = '%0.12f'

            np.savetxt(f, data, fmt=fmt)

    with tempdir():
        data = np.random.randint(1, 100, (10, 20))
        genvest(data, 'data.vest')
        assert np.all(data == vest.loadVestFile('data.vest'))

        data = np.random.random((20, 10))
        genvest(data, 'data.vest')
        assert np.all(np.isclose(data, vest.loadVestFile('data.vest')))

        # should pass
        vest.loadVestFile('data.vest', ignoreHeader=False)

        # invalid VEST header
        genvest(data, 'data.vest', (10, 20))

        # default behaviour - ignore header
        assert np.all(np.isclose(data, vest.loadVestFile('data.vest')))

        with pytest.raises(ValueError):
            vest.loadVestFile('data.vest', ignoreHeader=False)
