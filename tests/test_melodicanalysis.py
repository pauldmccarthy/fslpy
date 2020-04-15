#!/usr/bin/env python
#
# test_melodicanalysis.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import              os
import os.path   as op
import itertools as it

import numpy     as np
import pytest

import tests
import fsl.utils.path           as fslpath
import fsl.data.melodicanalysis as mela


def test_isMelodicImage():
    paths = ['analysis.ica/melodic_IC.nii.gz',
             'analysis.ica/melodic_mix',
             'analysis.ica/melodic_FTmix',

             'analysis.blica/melodic_IC.nii.gz',

             'analysis2.ica/melodic_oIC.nii.gz',
             'analysis2.ica/melodic_mix',
             'analysis2.ica/melodic_FTmix',
             'analysis3.ica/melodic_IC.nii.gz',
             'analysis3.ica/melodic_oIC.nii.gz',
             'analysis3.ica/melodic_mix',
             'analysis3.ica/melodic_FTmix']

    with tests.testdir(paths) as testdir:
        for p in paths:
            expected = any([p == 'analysis.ica/melodic_IC.nii.gz',
                            p == 'analysis2.ica/melodic_oIC.nii.gz',
                            p == 'analysis3.ica/melodic_IC.nii.gz',
                            p == 'analysis3.ica/melodic_oIC.nii.gz'])
            assert mela.isMelodicImage(op.join(testdir, p)) == expected


def test_isMelodicDir():
    paths = ['analysis.ica/melodic_IC.nii.gz',
             'analysis.ica/melodic_mix',
             'analysis.ica/melodic_FTmix']

    with tests.testdir(paths) as testdir:
        meldir = op.join(testdir, 'analysis.ica')
        assert mela.isMelodicDir(meldir)

    # melodic_oIC is ok
    with tests.testdir([p.replace('ic_IC', 'ic_oIC') for p in paths]) as testdir:
        meldir = op.join(testdir, 'analysis.ica')
        assert mela.isMelodicDir(meldir)

    # non-.ica prefix is ok
    with tests.testdir([p.replace('.ica', '.blob') for p in paths]) as testdir:
        meldir = op.join(testdir, 'analysis.blob')
        assert mela.isMelodicDir(meldir)

    # Directory must exist!
    assert not mela.isMelodicDir('non-existent.ica')

    # Directory must contain all of the above files
    perms = it.chain(it.combinations(paths, 1),
                     it.combinations(paths, 2))
    for p in perms:
        with tests.testdir(p) as testdir:
            meldir = op.join(testdir, 'analysis.ica')
            assert not mela.isMelodicDir(meldir)

    # same test for melodic_oIC
    for p in perms:
        with tests.testdir([pp.replace('ic_IC', 'ic_oIC') for pp in p]) as testdir:
            meldir = op.join(testdir, 'analysis.ica')
            assert not mela.isMelodicDir(meldir)


def test_getAnalysisDir():
    paths = ['analysis.ica/melodic_IC.nii.gz',
             'analysis.ica/melodic_mix',
             'analysis.ica/melodic_FTmix']

    testpaths = ['analysis.ica/melodic_IC.nii.gz',
                 'analysis.ica/log.txt',
                 'analysis.ica/stats/thresh_zstat1.nii.gz',
                 'analysis.ica/report/00index.html']

    with tests.testdir(paths) as testdir:
        expected = op.join(testdir, 'analysis.ica')
        for tp in testpaths:
            assert mela.getAnalysisDir(op.join(testdir, tp)) == expected

    paths = ['analysis.ica/melodic_blob.nii.gz',
             'analysis.ica/melodic_mix',
             'analysis.ica/melodic_FTmix']

    with tests.testdir(paths) as testdir:
        for tp in testpaths:
            assert mela.getAnalysisDir(op.join(testdir, tp)) is None


def test_getTopLevelAnalysisDir():
    testpaths = [
        ('REST.ica/filtered_func_data.ica/melodic_IC.nii.gz',   'REST.ica'),
        ('REST.ica/filtered_func_data.ica/melodic_mix',         'REST.ica'),
        ('analysis.gica/groupmelodic.ica/melodic_IC.nii.gz',    'analysis.gica'),
        ('analysis.feat/filtered_func_data.ica/melodic_mix',    'analysis.feat'),
        ('not/any/analysis/directories/here/melodic_IC.nii.gz', None),
    ]

    for tp, expected in testpaths:
        assert mela.getTopLevelAnalysisDir(tp) == expected


def test_getDataFile():

    testcases = [(['analysis.ica/filtfunc.ica/melodic_IC.nii.gz',
                   'analysis.ica/filtfunc.ica/melodic_mix',
                   'analysis.ica/filtfunc.ica/melodic_FTmix',
                   'analysis.ica/filtered_func_data.nii.gz'],
                  'analysis.ica/filtfunc.ica',
                  'analysis.ica/filtered_func_data.nii.gz'),
                 (['analysis.feat/filtfunc.ica/melodic_IC.nii.gz',
                   'analysis.feat/filtfunc.ica/melodic_mix',
                   'analysis.feat/filtfunc.ica/melodic_FTmix',
                   'analysis.feat/filtered_func_data.nii.gz'],
                  'analysis.feat/filtfunc.ica',
                  'analysis.feat/filtered_func_data.nii.gz'),
                 (['no/analysis/dirs/here/melodic_IC.nii.gz'],
                   'no/analysis/dirs/here/',
                   None),
                 (['analysis.feat/analysis.ica/melodic_IC.nii.gz',
                   'analysis.feat/analysis.ica/melodic_mix',
                   'analysis.feat/analysis.ica/melodic_FTmix'],
                   'analysis.feat/analysis.ica',
                   None),

    ]

    for paths, meldir, expected in testcases:
        paths = [op.join(*p.split('/')) for p in paths]
        if expected is not None:
            expected = op.join(*expected.split('/'))
        with tests.testdir(paths) as testdir:
            assert mela.getDataFile(meldir) == expected


def test_getMeanFile():
    paths = ['analysis.ica/melodic_IC.nii.gz',
             'analysis.ica/melodic_mix',
             'analysis.ica/melodic_FTmix',
             'analysis.ica/mean.nii.gz']

    paths = [op.join(*p.split('/')) for p in paths]

    with tests.testdir(paths) as testdir:
        meldir   = op.join(testdir, 'analysis.ica')
        expected = op.join(testdir, 'analysis.ica', 'mean.nii.gz')

        assert mela.getMeanFile(meldir) == expected

    paths = ['analysis.ica/melodic_IC.nii.gz',
             'analysis.ica/melodic_mix',
             'analysis.ica/melodic_FTmix',
             'analysis.ica/mean.txt']

    paths = [op.join(*p.split('/')) for p in paths]

    with tests.testdir(paths) as testdir:
        meldir = op.join(testdir, 'analysis.ica')
        with pytest.raises(fslpath.PathError):
            mela.getMeanFile(meldir)


def test_getICFile():
    paths = ['analysis.ica/melodic_IC.nii.gz',
             'analysis.ica/melodic_mix',
             'analysis.ica/melodic_FTmix']

    paths = [op.join(*p.split('/')) for p in paths]

    with tests.testdir(paths) as testdir:
        meldir   = op.join(testdir, 'analysis.ica')
        expected = op.join(testdir, 'analysis.ica', 'melodic_IC.nii.gz')
        assert mela.getICFile(meldir) == expected

    paths = ['analysis.ica/melodic_IC.txt',
             'analysis.ica/melodic_mix',
             'analysis.ica/melodic_FTmix']

    paths = [op.join(*p.split('/')) for p in paths]

    with tests.testdir(paths) as testdir:
        meldir = op.join(testdir, 'analysis.ica')
        with pytest.raises(fslpath.PathError):
            mela.getICFile(meldir)


def test_getMixFile():
    paths = ['analysis.ica/melodic_IC.nii.gz',
             'analysis.ica/melodic_mix',
             'analysis.ica/melodic_FTmix']

    paths = [op.join(*p.split('/')) for p in paths]

    with tests.testdir(paths) as testdir:
        meldir   = op.join(testdir, 'analysis.ica')
        expected = op.join(testdir, 'analysis.ica', 'melodic_mix')
        assert mela.getMixFile(meldir) == expected

    paths = ['analysis.ica/melodic_IC.ni.gz',
             'analysis.ica/melodic_FTmix']
    paths = [op.join(*p.split('/')) for p in paths]

    with tests.testdir(paths) as testdir:
        meldir = op.join(testdir, 'analysis.ica')
        assert mela.getMixFile(meldir) is None

def test_getFTMixFile():
    paths = ['analysis.ica/melodic_IC.nii.gz',
             'analysis.ica/melodic_mix',
             'analysis.ica/melodic_FTmix']
    paths = [op.join(*p.split('/')) for p in paths]

    with tests.testdir(paths) as testdir:
        meldir   = op.join(testdir, 'analysis.ica')
        expected = op.join(testdir, 'analysis.ica', 'melodic_FTmix')
        assert mela.getFTMixFile(meldir) == expected

    paths = ['analysis.ica/melodic_IC.ni.gz',
             'analysis.ica/melodic_mix']
    paths = [op.join(*p.split('/')) for p in paths]

    with tests.testdir(paths) as testdir:
        meldir = op.join(testdir, 'analysis.ica')
        assert mela.getFTMixFile(meldir) is None

def test_getReportFile():
    paths = ['analysis.ica/filtfunc.ica/melodic_IC.nii.gz',
             'analysis.ica/filtfunc.ica/melodic_mix',
             'analysis.ica/filtfunc.ica/melodic_FTmix',
             'analysis.ica/report.html']
    paths = [op.join(*p.split('/')) for p in paths]

    with tests.testdir(paths) as testdir:
        meldir   = op.join(testdir, 'analysis.ica', 'filtfunc.ica')
        expected = op.join(testdir, 'analysis.ica', 'report.html')
        assert op.abspath(mela.getReportFile(meldir)) == expected

    paths = ['analysis.ica/filtfunc.ica/melodic_IC.ni.gz',
             'analysis.ica/filtfunc.ica/melodic_mix',
             'analysis.ica/filtfunc.ica/melodic_FTmix']
    paths = [op.join(*p.split('/')) for p in paths]

    with tests.testdir(paths) as testdir:
        meldir = op.join(testdir, 'analysis.ica')
        assert mela.getReportFile(meldir) is None


def test_getNumComponents():
    paths = ['analysis.ica/melodic_IC.nii.gz',
             'analysis.ica/melodic_mix',
             'analysis.ica/melodic_FTmix']

    with tests.testdir(paths) as testdir:
        meldir = op.join(testdir, 'analysis.ica')
        icfile = op.join(meldir,  'melodic_IC.nii.gz')

        tests.make_random_image(icfile, (10, 10, 10, 17))

        assert mela.getNumComponents(meldir) == 17

    with tests.testdir(paths) as testdir:
        meldir = op.join(testdir, 'analysis.ica')
        with pytest.raises(Exception):
            mela.getNumComponents(meldir)


def test_getComponentTimeSeries():
    paths = ['analysis.ica/melodic_IC.nii.gz',
             'analysis.ica/melodic_mix',
             'analysis.ica/melodic_FTmix']

    with tests.testdir(paths) as testdir:
        meldir  = op.join(testdir, 'analysis.ica')
        mixfile = op.join(meldir,  'melodic_mix')

        data = np.zeros((40, 20))
        for i in range(20):
            data[:, i] = np.arange(i, i + 40)

        np.savetxt(mixfile, data)
        assert np.all(mela.getComponentTimeSeries(meldir) == data)

    with tests.testdir(paths) as testdir:
        meldir = op.join(testdir, 'analysis.ica')
        with pytest.raises(Exception):
            mela.getComponentTimeSeries(meldir)


def test_getComponentPowerSpectra():
    paths = ['analysis.ica/melodic_IC.nii.gz',
             'analysis.ica/melodic_mix',
             'analysis.ica/melodic_FTmix']

    with tests.testdir(paths) as testdir:
        meldir    = op.join(testdir, 'analysis.ica')
        ftmixfile = op.join(meldir,  'melodic_FTmix')

        data = np.zeros((40, 20))
        for i in range(20):
            data[:, i] = np.arange(i, i + 40)

        np.savetxt(ftmixfile, data)
        assert np.all(mela.getComponentPowerSpectra(meldir) == data)

    with tests.testdir(paths) as testdir:
        meldir = op.join(testdir, 'analysis.ica')
        with pytest.raises(Exception):
            mela.getComponentPowerSpectra(meldir)
