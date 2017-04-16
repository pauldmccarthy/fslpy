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
              '2ndlevel_1.gfeat/cope1.feat', '2ndlevel_1.gfeat/cope2.feat',
              '2ndlevel_2.gfeat/cope1.feat', '2ndlevel_2.gfeat/cope2.feat']
shapes = [(64,  64,  5, 45),
          (64,  64,  5, 45),
          (64,  64,  5, 45),
          (91, 109, 91,  3),
          (91, 109, 91,  3),
          (91, 109, 91,  3),
          (91, 109, 91,  3)]
xforms = [[[-4, 0, 0,    0],
           [ 0, 4, 0,    0],
           [ 0, 0, 6,    0],
           [ 0, 0, 0,    1]]] * 3 + \
         [[[-2, 0, 0,   90],
           [ 0, 2, 0, -126],
           [ 0, 0, 2,  -72],
           [ 0, 0, 0,    1]]] * 4
xforms = [np.array(xf) for xf in xforms]
              
TEST_ANALYSES = list(zip(
    featdirs,
    shapes,
    xforms))


def test_FEATImage_attributes():

    for i, featdir in enumerate(featdirs):
        with tests.testdir() as testdir:

            featdir = tests.make_mock_feat_analysis(
                op.join(datadir, featdir),
                testdir,
                shapes[i],
                xforms[i],
                pes=False,
                copes=False,
                zstats=False,
                residuals=False,
                clustMasks=False)

            # Now create a FEATImage. We validate its
            # attributes against the values returned by
            # the functions in featdesign/featanalysis.
            fi       = featimage.FEATImage(featdir)
            settings = featanalysis.loadSettings(featdir)
            design   = featdesign.FEATFSFDesign(featdir, settings)
            desmat   = design.getDesign()
            evnames  = [ev.title for ev in design.getEVs()]
            contrastnames, contrasts = featanalysis.loadContrasts(featdir)

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


def test_FEATImage_imageAccessors():

    for i, featdir in enumerate(featdirs):
        with tests.testdir() as testdir:
            featdir = tests.make_mock_feat_analysis(
                op.join(datadir, featdir),
                testdir,
                shapes[i],
                xforms[i])

            shape4D    = shapes[  i]
            shape      = shape4D[:3]

            fi    = featimage.FEATImage(featdir)
            nevs  = fi.numEVs()
            ncons = fi.numContrasts()

            # Testing the FEATImage intenral cache
            for i in range(2):
                assert fi.getResiduals().shape == shape4D

                for ev in range(nevs):
                    assert fi.getPE(ev).shape == shape
                for con in range(ncons):
                    assert fi.getCOPE(       con).shape == shape
                    assert fi.getZStats(     con).shape == shape
                    assert fi.getClusterMask(con).shape == shape
            


def test_FEATImage_fit_firstLevel():
    featdir = ''
    fi      = featimage.FEATImage(featdir) 
    fi.fit(0, (0, 0, 0))


def test_FEATImage_fit_higherLevel():
    featdir = ''
    fi      = featimage.FEATImage(featdir) 
    fi.fit(0, (0, 0, 0)) 


def test_FEATImage_partialFit():
    featdir = ''
    fi      = featimage.FEATImage(featdir) 
    fi.fit(0, (0, 0, 0))


def test_FEATImage_nostats():
    pass 
