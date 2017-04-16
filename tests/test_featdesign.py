#!/usr/bin/env python
#
# test_featdesign.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Test data sets (in testdata/test_feat) were generated with FSL 5.0.9, and
then 'cleaned' to remove unnecessary files and reduce size, with the following
commands:

First level analyses:

    find . -name "*png" -delete
    find . -name "*ppm" -delete
    find . -name "*html" -delete
    rm -r logs .files tsplot .ramp.gif
    for f in `find . -name "*nii.gz"`; do
        echo $f > $f
    done

Second level analyses:

    find . -name "*png" -delete
    find . -name "*ppm" -delete
    find . -name "*html" -delete
    rm -r logs .files  .ramp.gif
    for f in `find . -name "*nii.gz"`; do
        echo $f > $f
    done

Second level cope?.feats:
    rm -r logs .files tsplot .ramp.gif
    


`1stlevel_1.feat`

 - 45 time points
 - 10 EVs in total:
   - 2 stimulus EVs
   - 2 temporal derivative EVs
   - 6 Standard motion parameters
 - 2 contrasts - one on each stimulus EV

`1stlevel_2.feat`

 - 45 time points
 - 11 EVs in total:
   - 2 stimulus EVs
   - 2 temporal derivative EVs
   - 1 voxelwise EV
   - 6 Standard motion parameters
 - 2 contrasts - one on each stimulus EV 

`1stlevel_3.feat`
 - 45 time points
 - 32 EVs in total:
   - 2 stimulus EVs
   - 1 Temporal derivative EV on first
   - 2 gamma basis functions on second
   - 24 Standard+extended motion parameters
   - 2 Confound EVs
   - 1 Voxelwise confound EV
 - 2 contrasts - one on each stimulus EV

`2ndlevel_1.feat`
 - Three inputs
 - Two copes
 - One main EV - group average

`2ndlevel_1.feat`
 - Three inputs
 - Two copes
 - One main EV - group average
 - One voxelwise EV
"""


import              os
import os.path   as op
import itertools as it
import              glob
import              shutil
import numpy     as np

import pytest

import tests
import fsl.data.image        as fslimage
import fsl.data.featdesign   as featdesign
import fsl.data.featanalysis as featanalysis


datadir = op.join(op.dirname(__file__), 'testdata', 'test_feat')



def test_FEATFSFDesign():

    featdirs = ['1stlevel_1.feat', '1stlevel_2.feat', '1stlevel_3.feat',
                '2ndlevel_1.gfeat', '2ndlevel_2.gfeat']
    nevs     = [10, 11, 32, 1, 2]
    shapes   = [(45, 10), (45, 11), (45, 32), (3, 1), (3, 2)]    

    for featdir, nev, shape in zip(featdirs, nevs, shapes):
        featdir  = op.join(datadir, featdir)
        settings = featanalysis.loadSettings(featdir)

        # We can't load the voxelwise EVs
        # here, because all of the .nii.gz
        # files in the test directory are
        # stubs. Voxelwise EVs get tested
        # in the test_FEATFSFDesign_firstLevelVoxelwiseEV
        # function
        des = featdesign.FEATFSFDesign(featdir,
                                       loadVoxelwiseEVs=False)

        # Can also specify the design.fsf settings
        featdesign.FEATFSFDesign(featdir,
                                 settings=settings,
                                 loadVoxelwiseEVs=False)

        assert len(des.getEVs()) == nev
        assert des.getDesign().shape == shape
        assert des.getDesign((10, 10, 3)).shape == shape


def test_FEATFSFDesign_firstLevelVoxelwiseEV(seed):

    template = op.join(datadir, '1stlevel_2.feat')

    with tests.testdir() as testdir:

        # Set up some test data - we make
        # a copy of the feat directory,
        # and generate some dummy data for
        # the voxelwise EVs.
        featdir    = op.join(testdir, '1stlevel_2.feat')
        shape4D    = (64, 64, 5, 45)
        shape      = shape4D[:3]

        featdir = tests.make_mock_feat_analysis(
            template, testdir, shape4D,
            indata=False,
            pes=False,
            copes=False,
            zstats=False,
            residuals=False,
            clusterMasks=False)

        # Now load the design, and make sure that
        # the voxel EVs are filled correctly
        design    = featdesign.FEATFSFDesign(featdir)
        voxevIdxs = [ev.index for ev in design.getEVs()
                     if isinstance(ev, (featdesign.VoxelwiseEV,
                                        featdesign.VoxelwiseConfoundEV))]

        randVoxels = np.vstack([np.random.randint(0, s, 10) for s in shape]).T

        for voxel in randVoxels:

            voxel  = [int(v) for v in voxel]
            offset = np.ravel_multi_index(voxel, shape)
            matrix = design.getDesign(voxel)

            for i, evidx in enumerate(voxevIdxs):
                expect = np.arange(i, i + 45) + offset
                assert np.all(np.isclose(matrix[:, evidx], expect))


def test_getFirstLevelEVs_1():
    featdir  = op.join(datadir, '1stlevel_1.feat')
    settings = featanalysis.loadSettings(featdir)
    matrix   = featdesign.loadDesignMat(op.join(featdir, 'design.mat'))

    expected = [(featdesign.NormalEV,             {'index' : 0, 'origIndex' : 0}),
                (featdesign.TemporalDerivativeEV, {'index' : 1}),
                (featdesign.NormalEV,             {'index' : 2, 'origIndex' : 1}),
                (featdesign.TemporalDerivativeEV, {'index' : 3}),
                (featdesign.MotionParameterEV,    {'index' : 4, 'motionIndex' : 0}),
                (featdesign.MotionParameterEV,    {'index' : 5, 'motionIndex' : 1}),
                (featdesign.MotionParameterEV,    {'index' : 6, 'motionIndex' : 2}),
                (featdesign.MotionParameterEV,    {'index' : 7, 'motionIndex' : 3}),
                (featdesign.MotionParameterEV,    {'index' : 8, 'motionIndex' : 4}),
                (featdesign.MotionParameterEV,    {'index' : 9, 'motionIndex' : 5})]

    evs = featdesign.getFirstLevelEVs(featdir, settings, matrix)
    assert len(evs) == 10

    for i, (evtype, atts) in enumerate(expected):

        assert isinstance(evs[i], evtype)
        for k, v in atts.items():
            assert getattr(evs[i], k) == v


def test_getFirstLevelEVs_2():
    featdir  = op.join(datadir, '1stlevel_2.feat')
    settings = featanalysis.loadSettings(featdir)
    matrix   = featdesign.loadDesignMat(op.join(featdir, 'design.mat'))

    expected = [(featdesign.NormalEV,             {'index' : 0, 'origIndex' : 0}),
                (featdesign.TemporalDerivativeEV, {'index' : 1}),
                (featdesign.NormalEV,             {'index' : 2, 'origIndex' : 1}),
                (featdesign.TemporalDerivativeEV, {'index' : 3}),
                (featdesign.VoxelwiseEV,          {'index' : 4, 'origIndex' : 2}),
                (featdesign.MotionParameterEV,    {'index' : 5,  'motionIndex' : 0}),
                (featdesign.MotionParameterEV,    {'index' : 6,  'motionIndex' : 1}),
                (featdesign.MotionParameterEV,    {'index' : 7,  'motionIndex' : 2}),
                (featdesign.MotionParameterEV,    {'index' : 8,  'motionIndex' : 3}),
                (featdesign.MotionParameterEV,    {'index' : 9,  'motionIndex' : 4}),
                (featdesign.MotionParameterEV,    {'index' : 10, 'motionIndex' : 5})]

    evs = featdesign.getFirstLevelEVs(featdir, settings, matrix)
    assert len(evs) == 11

    for i, (evtype, atts) in enumerate(expected):

        assert isinstance(evs[i], evtype)
        for k, v in atts.items():
            assert getattr(evs[i], k) == v


def test_getFirstLevelEVs_3():
    featdir  = op.join(datadir, '1stlevel_3.feat')
    settings = featanalysis.loadSettings(featdir)
    matrix   = featdesign.loadDesignMat(op.join(featdir, 'design.mat'))

    expected = [(featdesign.NormalEV,             {'index' : 0, 'origIndex' : 0}),
                (featdesign.TemporalDerivativeEV, {'index' : 1}),
                (featdesign.NormalEV,             {'index' : 2, 'origIndex' : 1}),
                (featdesign.BasisFunctionEV,      {'index' : 3}),
                (featdesign.BasisFunctionEV,      {'index' : 4}),
                (featdesign.VoxelwiseConfoundEV,  {'index' : 5, 'voxIndex'     : 0}),
                (featdesign.MotionParameterEV,    {'index' : 6,  'motionIndex' : 0}),
                (featdesign.MotionParameterEV,    {'index' : 7,  'motionIndex' : 1}),
                (featdesign.MotionParameterEV,    {'index' : 8,  'motionIndex' : 2}),
                (featdesign.MotionParameterEV,    {'index' : 9,  'motionIndex' : 3}),
                (featdesign.MotionParameterEV,    {'index' : 10, 'motionIndex' : 4}),
                (featdesign.MotionParameterEV,    {'index' : 11, 'motionIndex' : 5}),
                (featdesign.MotionParameterEV,    {'index' : 12, 'motionIndex' : 6}),
                (featdesign.MotionParameterEV,    {'index' : 13, 'motionIndex' : 7}),
                (featdesign.MotionParameterEV,    {'index' : 14, 'motionIndex' : 8}),
                (featdesign.MotionParameterEV,    {'index' : 15, 'motionIndex' : 9}),
                (featdesign.MotionParameterEV,    {'index' : 16, 'motionIndex' : 10}),
                (featdesign.MotionParameterEV,    {'index' : 17, 'motionIndex' : 11}),
                (featdesign.MotionParameterEV,    {'index' : 18, 'motionIndex' : 12}),
                (featdesign.MotionParameterEV,    {'index' : 19, 'motionIndex' : 13}),
                (featdesign.MotionParameterEV,    {'index' : 20, 'motionIndex' : 14}),
                (featdesign.MotionParameterEV,    {'index' : 21, 'motionIndex' : 15}),
                (featdesign.MotionParameterEV,    {'index' : 22, 'motionIndex' : 16}),
                (featdesign.MotionParameterEV,    {'index' : 23, 'motionIndex' : 17}),
                (featdesign.MotionParameterEV,    {'index' : 24, 'motionIndex' : 18}),
                (featdesign.MotionParameterEV,    {'index' : 25, 'motionIndex' : 19}),
                (featdesign.MotionParameterEV,    {'index' : 26, 'motionIndex' : 20}),
                (featdesign.MotionParameterEV,    {'index' : 27, 'motionIndex' : 21}),
                (featdesign.MotionParameterEV,    {'index' : 28, 'motionIndex' : 22}),
                (featdesign.MotionParameterEV,    {'index' : 29, 'motionIndex' : 23}),
                (featdesign.ConfoundEV,           {'index' : 30, 'confIndex'   : 0}),
                (featdesign.ConfoundEV,           {'index' : 31, 'confIndex'   : 1})]
    

    evs = featdesign.getFirstLevelEVs(featdir, settings, matrix)
    
    assert len(evs) == 32

    for i, (evtype, atts) in enumerate(expected):

        print(i, evs[i])

        assert isinstance(evs[i], evtype)
        for k, v in atts.items():
            assert getattr(evs[i], k) == v


def test_getHigherLevelEVs_1():

    featdir  = op.join(datadir, '2ndlevel_1.gfeat')
    settings = featanalysis.loadSettings(featdir)
    matrix   = featdesign.loadDesignMat(op.join(featdir, 'design.mat'))

    evs = featdesign.getHigherLevelEVs(featdir, settings, matrix)

    assert len(evs) == 1
    assert isinstance(evs[0], featdesign.NormalEV)
    assert evs[0].index     == 0
    assert evs[0].origIndex == 0
 
    


def test_getHigherLevelEVs_2():

    featdir  = op.join(datadir, '2ndlevel_2.gfeat')
    settings = featanalysis.loadSettings(featdir)
    matrix   = featdesign.loadDesignMat(op.join(featdir, 'design.mat'))

    evs = featdesign.getHigherLevelEVs(featdir, settings, matrix)

    assert len(evs) == 2
    assert isinstance(evs[0], featdesign.NormalEV)
    assert evs[0].index     == 0
    assert evs[0].origIndex == 0
    assert isinstance(evs[1], featdesign.VoxelwiseEV)



def test_loadDesignMat():

    analyses = ['1stlevel_1.feat', '1stlevel_2.feat', '1stlevel_3.feat',
                '2ndlevel_1.gfeat', '2ndlevel_2.gfeat']
    shapes   = [(45, 10), (45, 11), (45, 32), (3, 1), (3, 2)]

    for analysis, shape in zip(analyses, shapes):
        featdir = op.join(datadir, analysis)
        fname   = op.join(featdir, 'design.mat')
        mat     = featdesign.loadDesignMat(fname)

        assert mat.shape == shape

    nonfile = op.join(datadir, 'non-existent-file')
    badfile = op.join(datadir, '1stlevel_1.feat', 'design.fsf') 
    with pytest.raises(Exception):
        featdesign.loadDesignMat(nonfile)

    with pytest.raises(Exception):
        featdesign.loadDesignMat(badfile) 
