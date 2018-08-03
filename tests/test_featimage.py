#!/usr/bin/env python
#
# test_featimage.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path   as op
import              os
import itertools as it
import              glob
import              shutil

import numpy   as np

import pytest

import tests
import fsl.data.featimage    as featimage
import fsl.data.featdesign   as featdesign
import fsl.data.featanalysis as featanalysis


datadir    = op.join(op.dirname(__file__), 'testdata', 'test_feat')
featdirs   = ['1stlevel_1.feat', '1stlevel_2.feat', '1stlevel_2.feat',
              '1stlevel_realdata.feat',
              '2ndlevel_1.gfeat/cope1.feat', '2ndlevel_1.gfeat/cope2.feat',
              '2ndlevel_2.gfeat/cope1.feat', '2ndlevel_2.gfeat/cope2.feat',
              '2ndlevel_realdata.gfeat/cope1.feat',
              '2ndlevel_realdata.gfeat/cope2.feat']
featdirs = [op.join(*d.split('/')) for d in featdirs]
shapes = [(64,  64,  5, 45),
          (64,  64,  5, 45),
          (64,  64,  5, 45),
          ( 4,   4,  5, 45),
          (91, 109, 91,  3),
          (91, 109, 91,  3),
          (91, 109, 91,  3),
          (91, 109, 91,  3),
          (10,  10, 10,  3),
          (10,  10, 10,  3)]
xforms = [[[-4, 0, 0,    0],
           [ 0, 4, 0,    0],
           [ 0, 0, 6,    0],
           [ 0, 0, 0,    1]]] * 3 + \
         [[[-4, 0, 0, -120],
           [ 0, 4, 0,  120],
           [ 0, 0, 6,    0],
           [ 0, 0, 0,    1]]] * 1 + \
         [[[-2, 0, 0,   90],
           [ 0, 2, 0, -126],
           [ 0, 0, 2,  -72],
           [ 0, 0, 0,    1]]] * 4 + \
         [[[-2, 0, 0,   20],
           [ 0, 2, 0, -102],
           [ 0, 0, 2,   -6],
           [ 0, 0, 0,    1]]] * 2
xforms = [np.array(xf) for xf in xforms]

TEST_ANALYSES = {}
for i, featdir in enumerate(featdirs):
    TEST_ANALYSES[featdir] = {
        'shape' : shapes[i],
        'xform' : xforms[i]
    }


def test_FEATImage_attributes():

    # TEst bad input
    with pytest.raises(Exception):
        featimage.FEATImage('baddir')

    for featdir in TEST_ANALYSES.keys():

        shape = TEST_ANALYSES[featdir]['shape']
        xform = TEST_ANALYSES[featdir]['xform']
        with tests.testdir() as testdir:

            if 'realdata' not in featdir:
                featdir = tests.make_mock_feat_analysis(
                    op.join(datadir, featdir),
                    testdir,
                    shape,
                    xform,
                    pes=False,
                    copes=False,
                    zstats=False,
                    residuals=False,
                    clustMasks=False)
            else:
                featdir = op.join(datadir, featdir)

            # Now create a FEATImage. We validate its
            # attributes against the values returned by
            # the functions in featdesign/featanalysis.
            fi       = featimage.FEATImage(featdir)
            settings = featanalysis.loadSettings(featdir)
            design   = featdesign.FEATFSFDesign(featdir, settings)
            desmat   = design.getDesign()
            evnames  = [ev.title for ev in design.getEVs()]
            contrastnames, contrasts = featanalysis.loadContrasts(featdir)

            assert np.all(np.isclose(fi.shape,         shape))
            assert np.all(np.isclose(fi.voxToWorldMat, xform))

            assert fi.getFEATDir()             == featdir
            assert fi.getAnalysisName()        == op.splitext(op.basename(featdir))[0]
            assert fi.isFirstLevelAnalysis()   == featanalysis.isFirstLevelAnalysis(settings)
            assert fi.getTopLevelAnalysisDir() == featanalysis.getTopLevelAnalysisDir(featdir)
            assert fi.getReportFile()          == featanalysis.getReportFile(featdir)
            assert fi.hasStats()               == featanalysis.hasStats(featdir)
            assert fi.numPoints()              == desmat.shape[0]
            assert fi.numEVs()                 == desmat.shape[1]
            assert fi.evNames()                == evnames
            assert fi.numContrasts()           == len(contrasts)
            assert fi.contrastNames()          == contrastnames
            assert fi.contrasts()              == contrasts
            assert np.all(np.isclose(fi.getDesign(), desmat))

            assert fi.thresholds() == featanalysis.getThresholds(settings)

            for ci in range(len(contrasts)):
                result = fi.clusterResults(ci)
                expect = featanalysis.loadClusterResults(featdir, settings, ci)
                assert len(result) == len(expect)
                assert all([rc.nvoxels == ec.nvoxels for rc, ec in zip(result, expect)])
            del design
            del fi
            fi = None



def test_FEATImage_imageAccessors():

    for featdir in TEST_ANALYSES.keys():

        shape = TEST_ANALYSES[featdir]['shape']
        xform = TEST_ANALYSES[featdir]['xform']
        
        with tests.testdir() as testdir:

            if 'realdata' not in featdir:
                featdir = tests.make_mock_feat_analysis(
                    op.join(datadir, featdir),
                    testdir,
                    shape,
                    xform)
            else:
                featdir = op.join(datadir, featdir)

            shape4D = shape
            shape   = shape4D[:3]

            fi    = featimage.FEATImage(featdir)
            nevs  = fi.numEVs()
            ncons = fi.numContrasts()

            # Testing the FEATImage internal cache
            for i in range(2):
                assert fi.getResiduals().shape == shape4D
                for ev in range(nevs):
                    assert fi.getPE(ev).shape == shape
                for con in range(ncons):
                    assert fi.getCOPE(       con).shape == shape
                    assert fi.getZStats(     con).shape == shape
                    assert fi.getClusterMask(con).shape == shape
            del fi
            fi = None


def test_FEATImage_nostats():

    featdir = op.join(datadir, '1stlevel_nostats.feat')
    shape   = (4, 4, 5, 45)

    with tests.testdir() as testdir:

        featdir = tests.make_mock_feat_analysis(featdir, testdir, shape)
        fi      = featimage.FEATImage(featdir)

        assert fi.getDesign() is None
        assert fi.numPoints() == 0
        assert fi.numEVs()    == 0
        assert fi.evNames()   == []

        with pytest.raises(Exception):
            fi.fit([1, 2, 3], (2, 2, 2))

        with pytest.raises(Exception):
            fi.partialFit([1, 2, 3], (2, 2, 2))
        del fi
        fi = None


def test_FEATImage_fit_firstLevel():

    featdir  = op.join(datadir, '1stlevel_realdata.feat')
    fi       = featimage.FEATImage(featdir)
    expect   = np.array([
        10625.35273455,  10625.35263602,  10625.35248499,  10625.35272602,
        10625.35286707,  10625.35237145,  10625.35244999,  10625.35270435,
        10625.35272762,  10629.03397661,  10685.36428581,  10658.64633521,
        10524.89226543,  10415.61794156,  10373.6671577 ,  10437.10001383,
        10403.88611746,  10226.98548936,  10080.14323091,  10012.89132265,
        9936.530395   ,   9957.92598556,  10090.51140821,  10199.6446317 ,
        10246.67689405,  10261.45133255,  10265.36943466,  10266.22514043,
        10266.32736048,  10264.92716455,  10243.05011597,  10245.62798475,
        10287.91883737,  10325.38456267,  10341.92299781,  10347.17916861,
        10348.58339616,  10348.89634025,  10348.93522057,  10345.25397481,
        10288.9236822 ,  10315.64160242,  10449.39567496,  10558.66999883,
        10597.64918744])

    # bad contrast
    with pytest.raises(Exception):
        fi.fit([1, 2, 3, 4, 5, 6, 7], (2, 2, 2))

    # bad voxel
    with pytest.raises(Exception):
        fi.fit([1, 0, 0, 0], (6, 7, 7))

    result = fi.fit([1, 1, 1, 1], (2, 2, 2))
    assert np.all(np.isclose(result, expect))
    del fi
    fi = None


def test_FEATImage_fit_higherLevel():

    featdir = op.join(datadir, '2ndlevel_realdata.gfeat/cope1.feat')
    fi      = featimage.FEATImage(featdir)
    expect  = np.array([86.37929535, 86.37929535, 86.37929535])
    result = fi.fit([1], (5, 5, 5))

    assert np.all(np.isclose(result, expect))
    del fi
    fi = None


def test_FEATImage_partialFit():

    featdir = op.join(datadir, '1stlevel_realdata.feat')
    fi      = featimage.FEATImage(featdir)
    expect  = np.array([
        10476.23185443,  10825.13542716,  10781.15297632,  11032.96902851,
        11019.47536463,  10856.61537194,  10463.38391362,  10664.79227954,
        10948.11850521,  10712.01568132,  10882.88149773,  10745.65913733,
        10590.78057109,  10524.89948148,  10744.82941967,  10422.96359453,
        10156.39446402,  10219.8339014 ,  10115.32145738,  10494.28109315,
        10121.89555309,  10165.92560409,  10556.70058668,  10198.67478569,
        10045.04934583,   9906.60233353,  10015.75569565,   9864.38786016,
        10241.91219554,  10099.08538293,  10444.7826294 ,  10152.72622847,
        10077.09075815,  10128.63320464,  10087.93203101,  10450.29667654,
        10207.89144059,  10137.98334586,  10387.09965691,  10194.79436483,
        10203.21032619,  10136.1942605 ,  10128.23728873,  10416.78984136,
        10118.51262128])
    result = fi.partialFit([1, 1, 1, 1], (2, 2, 2))

    assert np.all(np.isclose(result, expect))
    del fi
    fi = None


def test_modelFit(seed):

    for i in range(500):

        # 2 evs, 20 timepoints
        # First EV is a boxcar,
        # second is a random regressor
        design       = np.zeros((20, 2))
        design[:, 0] = np.tile([1, 1, 0, 0], 5)
        design[:, 1] = np.random.random(20)

        # demean columns of design matrix
        for ev in range(design.shape[1]):
            design[:, ev] = design[:, ev] - design[:, ev].mean()

        # Generate some random PEs, and
        # generate the data that would
        # have resulted in them
        pes      = np.random.random(2)
        expect   = np.dot(design, pes)
        contrast = [1] * design.shape[1]

        result1 = featimage.modelFit(expect, design, contrast, pes, True)
        result2 = featimage.modelFit(expect, design, contrast, pes, False)

        assert np.all(np.isclose(result1 - expect.mean(), expect))
        assert np.all(np.isclose(result2,                 expect))
