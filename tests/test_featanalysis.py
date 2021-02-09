#!/usr/bin/env python
#
# test_featanalysis.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import              os
import os.path   as op
import itertools as it
import              glob
import              shutil
import              textwrap
import              collections

import numpy     as np

import pytest

import tests
import fsl.data.featanalysis as featanalysis
import fsl.data.featdesign   as featdesign
import fsl.data.image        as fslimage
import fsl.utils.path        as fslpath


def test_isFEATImage():
    paths = ['analysis.feat/filtered_func_data.nii.gz',
             'analysis.feat/filtered_func_data.txt',
             'analysis.feat/design.fsf',
             'analysis.feat/design.mat',
             'analysis.feat/design.con',
             'analysis.bleat/filtered_func_data.nii.gz']

    with tests.testdir(paths) as testdir:
        for p in paths:
            expected = p == 'analysis.feat/filtered_func_data.nii.gz'
            assert featanalysis.isFEATImage(op.join(testdir, p)) == expected


def test_isFEATDir():

    # We need these files for a directory
    # to be considered a FEAT directory
    paths = ['analysis.feat/filtered_func_data.nii.gz',
             'analysis.feat/design.fsf',
             'analysis.feat/design.mat',
             'analysis.feat/design.con']

    with tests.testdir(paths) as testdir:
        assert featanalysis.isFEATDir(op.join(testdir, 'analysis.feat'))

    # If the directory does not end in .feat,
    # then it's not a feat directory
    with tests.testdir([p.replace('feat', 'bleat') for p in paths]) as testdir:
        assert not featanalysis.isFEATDir(op.join(testdir, 'analysis.bleat'))

    # If the directory doesn't exist, then
    # it's not a feat directory
    assert not featanalysis.isFEATDir('nonexistent.feat')

    # If any of the above files are not
    # present, it is not a FEAT directory
    perms = it.chain(it.combinations(paths, 1),
                     it.combinations(paths, 2),
                     it.combinations(paths, 3))
    for p in perms:
        with tests.testdir(p) as testdir:
            assert not featanalysis.isFEATDir(
                op.join(testdir, 'analysis.feat'))


def test_hasStats():

    with tests.testdir(['analysis.feat/stats/zstat1.nii.gz']) as testdir:
        featdir = op.join(testdir, 'analysis.feat')
        assert featanalysis.hasStats(featdir)

    with tests.testdir(['analysis.feat/stats/zstat1.txt']) as testdir:
        featdir = op.join(testdir, 'analysis.feat')
        assert not featanalysis.hasStats(featdir)


def test_hasMelodicDir():
    paths = ['analysis.feat/filtered_func_data.ica/melodic_IC.nii.gz']
    with tests.testdir(paths) as testdir:
        featdir = op.join(testdir, 'analysis.feat')
        assert featanalysis.hasMelodicDir(featdir)


def test_getAnalysisDir():

    paths = ['analysis.feat/filtered_func_data.nii.gz',
             'analysis.feat/design.fsf',
             'analysis.feat/design.mat',
             'analysis.feat/design.con']

    testpaths = ['analysis.feat/filtered_func_data.nii.gz',
                 'analysis.feat/stats/zstat1.nii.gz',
                 'analysis.feat/logs/feat4_post',
                 'analysis.feat/.ramp.gif']

    with tests.testdir(paths) as testdir:
        expected = op.join(testdir, 'analysis.feat')
        for t in testpaths:
            t = op.join(testdir, t)
            assert featanalysis.getAnalysisDir(t) == expected


def test_getTopLevelAnalysisDir():
    testcases = [
        ('analysis.feat/filtered_func_data.ica/melodic_IC.nii.gz', 'analysis.feat'),
        ('analysis.feat/filtered_func_data.nii.gz', 'analysis.feat'),
        ('analysis.gfeat/cope1.feat/stats/zstat1.nii.gz', 'analysis.gfeat'),
        ('filtered_func_data.ica/melodic_mix', 'filtered_func_data.ica'),
        ('rest.ica/filtered_func_data.ica/melodic_IC.nii.gz', 'rest.ica')
    ]

    for path, expected in testcases:
        assert featanalysis.getTopLevelAnalysisDir(path) == expected


def test_getReportFile():

    testcases = [(['analysis.feat/report.html'], True),
                 (['analysis.feat/filtered_func_data.nii.gz'], False)]

    for paths, expected in testcases:
        with tests.testdir(paths) as testdir:

            featdir = op.join(testdir, 'analysis.feat')

            if expected:
                expected = op.join(featdir, 'report.html')
            else:
                expected = None

            assert featanalysis.getReportFile(featdir) == expected


def test_loadContrasts():
    # (design.con contents, expected names, expected vectors)
    goodtests = [
        ("""
         /ContrastName1 c1
         /ContrastName2 c2
         /ContrastName3 c3
         /NumContrasts 3
         /Matrix
         1 0 0
         0 1 0
         0 0 1
         """,
         ['c1', 'c2', 'c3'],
         [[1, 0, 0], [0, 1, 0], [0, 0, 1]]),
        ("""
         /NumContrasts 2
         /Matrix
         1 0 0 0
         0 1 0 0
         """,
         ['1', '2'],
         [[1, 0, 0, 0], [0, 1, 0, 0]]),
        ("""
         /NumContrasts 1
         /ContrastName1 My contrast
         /Matrix
         5
         """,
         ['My contrast'], [[5]])
    ]
    badtests = [
        """
        /Matrix
        1 0 0
        0 1 0
        """,
        """
        /NumContrasts 2
        /Matrix
        1 0
        0 1 1
        """,
        """
        /NumContrasts 3
        /Matrix
        1 0 0
        0 1 1
        """,
    ]

    with pytest.raises(Exception):
        featanalysis.loadContrasts('no file')

    with tests.testdir() as testdir:
        featdir = op.join(testdir, 'analysis.feat')
        for contents, expnames, expvectors in goodtests:
            designcon = op.join(featdir, 'design.con')
            tests.make_dummy_file(designcon, textwrap.dedent(contents).strip())

            result = featanalysis.loadContrasts(featdir)
            assert result[0] == expnames
            assert result[1] == expvectors

        for contents in badtests:
            designcon = op.join(featdir, 'design.con')
            tests.make_dummy_file(designcon, textwrap.dedent(contents).strip())

            with pytest.raises(Exception):
                featanalysis.loadContrasts(featdir)


def test_loadSettings():

    contents = """
    set random_setting true
    any lines that don't start with "set" should be ignored
    # regardless of whether they are commented or not
    set fmri(blah) 0.66
    set something     "quoted"
    set somethingelse 'quotedagain'
    set fmri_thing(no) none
    # set comment commented out
    set athing with spaces in the value
    """

    expected = collections.OrderedDict((
        ('random_setting', 'true'),
        ('blah',           '0.66'),
        ('something',      'quoted'),
        ('somethingelse',  'quotedagain'),
        ('fmri_thing(no)', 'none'),
        ('athing',         'with spaces in the value'),
    ))

    contents = textwrap.dedent(contents).strip()

    with pytest.raises(Exception):
        featanalysis.loadSettings('no file')

    with tests.testdir() as testdir:
        featdir = op.join(testdir, 'analysis.feat')
        designfsf = op.join(featdir, 'design.fsf')
        tests.make_dummy_file(designfsf, contents)
        assert featanalysis.loadSettings(featdir) == expected
        assert featanalysis.loadFsf(designfsf) == expected


def test_loadDesign():

    datadir = op.join(op.dirname(__file__), 'testdata', 'test_feat')
    featdir = op.join(datadir, '1stlevel_1.feat')

    settings = featanalysis.loadSettings(featdir)
    design   = featanalysis.loadDesign(featdir, settings)

    assert isinstance(design, featdesign.FEATFSFDesign)
    assert len(design.getEVs())     == 10
    assert design.getDesign().shape == (45, 10)


def test_getThresholds():
    datadir  = op.join(op.dirname(__file__), 'testdata', 'test_feat')
    featdir  = op.join(datadir, '1stlevel_1.feat')
    settings = featanalysis.loadSettings(featdir)

    thresholds = featanalysis.getThresholds(settings)
    assert np.isclose(thresholds['p'], 0.05)
    assert np.isclose(thresholds['z'], 2.3)


def test_isFirstLevelAnalysis():
    datadir  = op.join(op.dirname(__file__), 'testdata', 'test_feat')
    featdirs = ['1stlevel_1.feat',  '1stlevel_2.feat', '1stlevel_3.feat',
                '2ndlevel_1.gfeat', '2ndlevel_2.gfeat']

    for featdir in featdirs:

        expected = featdir.startswith('1')
        featdir  = op.join(datadir, featdir)
        settings = featanalysis.loadSettings(featdir)

        assert featanalysis.isFirstLevelAnalysis(settings) == expected


def test_loadClusterResults():
    datadir  = op.join(op.dirname(__file__), 'testdata', 'test_feat')
    featdirs = ['1stlevel_1.feat',  '1stlevel_2.feat', '1stlevel_3.feat',
                '2ndlevel_1.gfeat/cope1.feat', '2ndlevel_1.gfeat/cope2.feat',
                '2ndlevel_2.gfeat/cope1.feat', '2ndlevel_2.gfeat/cope2.feat']
    ncontrasts = [2, 2, 2, 1, 1, 1, 1]
    nclusters  = [[1, 5], [2, 2], [3, 5], [7], [1], [10], [27]]

    with pytest.raises(Exception):
        featanalysis.loadClusterResults('notafeatdir')

    for i, featdir in enumerate(featdirs):

        firstlevel = featdir.startswith('1')
        featdir    = op.join(datadir, featdir)

        with tests.testdir() as testdir:

            # work from a copy of the test data directory
            newfeatdir = op.join(testdir, 'analysis.feat')
            shutil.copytree(op.join(datadir, featdir), newfeatdir)
            featdir = newfeatdir

            # For higher level analyses, the
            # loadClusterResults function peeks
            # at the FEAT input data file
            # header, so we have to generate it.
            if not firstlevel:
                datafile = op.join(featdir, 'filtered_func_data.nii.gz')
                data  = np.random.randint(1, 10, (91, 109, 91))
                xform = np.array([[-2, 0, 0,   90],
                                  [ 0, 2, 0, -126],
                                  [ 0, 0, 2,  -72],
                                  [ 0, 0, 0,    1]])
                fslimage.Image(data, xform=xform).save(datafile)

            settings = featanalysis.loadSettings(featdir)
            for c in range(ncontrasts[i]):
                clusters = featanalysis.loadClusterResults(
                    featdir, settings, c)

                assert len(clusters) == nclusters[i][c]

            # Test calling the function on a feat dir
            # which doesn't have any cluster results
            if i == len(featdirs) - 1:
                for clustfile in glob.glob(op.join(featdir, 'cluster*txt')):
                    os.remove(clustfile)
                assert featanalysis.loadClusterResults(
                    featdir, settings, 0) is None

    # The above loop just checks that the number of
    # clusters loaded for each analysis was correct.
    # Below we check that the cluster data was loaded
    # correctly, just for one analysis
    featdir  = op.join(datadir, '1stlevel_1.feat')
    settings = featanalysis.loadSettings(featdir)
    cluster  = featanalysis.loadClusterResults(featdir, settings, 0)[0]
    expected = {
        'index'    : 1,
        'nvoxels'  : 296,
        'p'        : 1.79e-27,
        'logp'     : 26.7,
        'zmax'     : 6.03,
        'zmaxx'    : 34,
        'zmaxy'    : 10,
        'zmaxz'    : 1,
        'zcogx'    : 31.4,
        'zcogy'    : 12.3,
        'zcogz'    : 1.72,
        'copemax'  : 612,
        'copemaxx' : 34,
        'copemaxy' : 10,
        'copemaxz' : 1,
        'copemean' : 143
    }

    for k, v in expected.items():
        assert np.isclose(v, getattr(cluster, k))


def test_getDataFile():
    paths = ['analysis.feat/filtered_func_data.nii.gz',
             'analysis.feat/design.fsf',
             'analysis.feat/design.mat',
             'analysis.feat/design.con']

    with tests.testdir(paths) as testdir:
        featdir = op.join(testdir, 'analysis.feat')
        expect  = op.join(featdir, 'filtered_func_data.nii.gz')

        assert featanalysis.getDataFile(featdir) == expect

    paths = ['analysis.feat/filtered_func_data.txt',
             'analysis.feat/design.fsf',
             'analysis.feat/design.mat',
             'analysis.feat/design.con']

    with tests.testdir(paths) as testdir:
        featdir = op.join(testdir, 'analysis.feat')

        with pytest.raises(fslpath.PathError):
            assert featanalysis.getDataFile(featdir)


def test_getMelodicFile():
    testcases = [
        (['analysis.feat/filtered_func_data.ica/melodic_IC.nii.gz'], True),
        (['analysis.feat/filtered_func_data.ica/melodic_IC.txt'], False),
    ]

    for paths, shouldPass in testcases:
        with tests.testdir(paths) as testdir:
            featdir = op.join(testdir, 'analysis.feat')
            icadir  = op.join(featdir, 'filtered_func_data.ica')
            expect  = op.join(icadir,  'melodic_IC.nii.gz')

            if shouldPass:
                assert featanalysis.getMelodicFile(featdir) == expect
            else:
                with pytest.raises(fslpath.PathError):
                    featanalysis.getMelodicFile(featdir)



def test_getResidualFile():
    testcases = [
        (['analysis.feat/stats/res4d.nii.gz'], True),
        (['analysis.feat/stats/res4d.txt'], False),
    ]

    for paths, shouldPass in testcases:
        with tests.testdir(paths) as testdir:
            featdir = op.join(testdir, 'analysis.feat')
            expect  = op.join(featdir, 'stats', 'res4d.nii.gz')

            if shouldPass:
                assert featanalysis.getResidualFile(featdir) == expect
            else:
                with pytest.raises(fslpath.PathError):
                    featanalysis.getResidualFile(featdir)


def test_getPEFile():
    testcases = [
        (['analysis.feat/stats/pe1.nii.gz',
          'analysis.feat/stats/pe2.nii.gz'], True),
        (['analysis.feat/stats/pe1.nii.gz'], True),
        (['analysis.feat/stats/pe0.nii.gz'], False),
        (['analysis.feat/stats/pe1.txt'],    False),
    ]

    for paths, shouldPass in testcases:
        with tests.testdir(paths) as testdir:
            featdir = op.join(testdir, 'analysis.feat')

            for pei in range(len(paths)):
                expect = op.join(
                    featdir, 'stats', 'pe{}.nii.gz'.format(pei + 1))

                if shouldPass:
                    assert featanalysis.getPEFile(featdir, pei) == expect
                else:
                    with pytest.raises(fslpath.PathError):
                        featanalysis.getPEFile(featdir, pei)


def test_getCOPEFile():
    testcases = [
        (['analysis.feat/stats/cope1.nii.gz',
          'analysis.feat/stats/cope2.nii.gz'], True),
        (['analysis.feat/stats/cope1.nii.gz'], True),
        (['analysis.feat/stats/cope0.nii.gz'], False),
        (['analysis.feat/stats/cope1.txt'],    False),
    ]

    for paths, shouldPass in testcases:
        with tests.testdir(paths) as testdir:
            featdir = op.join(testdir, 'analysis.feat')

            for ci in range(len(paths)):
                expect = op.join(
                    featdir, 'stats', 'cope{}.nii.gz'.format(ci + 1))

                if shouldPass:
                    assert featanalysis.getCOPEFile(featdir, ci) == expect
                else:
                    with pytest.raises(fslpath.PathError):
                        featanalysis.getCOPEFile(featdir, ci)


def test_getZStatFile():
    testcases = [
        (['analysis.feat/stats/zstat1.nii.gz',
          'analysis.feat/stats/zstat2.nii.gz'], True),
        (['analysis.feat/stats/zstat1.nii.gz'], True),
        (['analysis.feat/stats/zstat0.nii.gz'], False),
        (['analysis.feat/stats/zstat1.txt'],    False),
    ]

    for paths, shouldPass in testcases:
        with tests.testdir(paths) as testdir:
            featdir = op.join(testdir, 'analysis.feat')

            for zi in range(len(paths)):
                expect = op.join(
                    featdir, 'stats', 'zstat{}.nii.gz'.format(zi + 1))

                if shouldPass:
                    assert featanalysis.getZStatFile(featdir, zi) == expect
                else:
                    with pytest.raises(fslpath.PathError):
                        featanalysis.getZStatFile(featdir, zi)


def test_getClusterMaskFile():
    testcases = [
        (['analysis.feat/cluster_mask_zstat1.nii.gz',
          'analysis.feat/cluster_mask_zstat2.nii.gz'], True),
        (['analysis.feat/cluster_mask_zstat1.nii.gz'], True),
        (['analysis.feat/cluster_mask_zstat0.nii.gz'], False),
        (['analysis.feat/cluster_mask_zstat1.txt'],    False),
    ]

    for paths, shouldPass in testcases:
        with tests.testdir(paths) as testdir:
            featdir = op.join(testdir, 'analysis.feat')

            for ci in range(len(paths)):
                expect = op.join(
                    featdir, 'cluster_mask_zstat{}.nii.gz'.format(ci + 1))

                if shouldPass:
                    assert featanalysis.getClusterMaskFile(featdir, ci) == expect
                else:
                    with pytest.raises(fslpath.PathError):
                        featanalysis.getClusterMaskFile(featdir, ci)
