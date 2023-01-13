#!/usr/bin/env python
#
# test_melodicimage.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

from __future__ import division

import os.path as op

import numpy   as np
import nibabel as nib

import pytest

import tests
import fsl.data.image           as fslimage
import fsl.data.melodicimage    as meli
import fsl.data.melodicanalysis as mela


def _create_dummy_melodic_analysis(basedir,
                                   shape4D=(10, 10, 10, 10),
                                   timepoints=20,
                                   tr=2,
                                   with_data=True,
                                   with_reportfile=True,
                                   with_meanfile=True,
                                   ic_prefix='melodic_IC'):

    tldir      = op.join(basedir, 'toplevel.ica')
    meldir     = op.join(tldir,   'analysis.ica')
    datafile   = op.join(tldir,   'filtered_func_data.nii.gz')
    reportfile = op.join(tldir,   'report.html')
    meanfile   = op.join(meldir,  'mean.nii.gz')
    icfile     = op.join(meldir,  '{}.nii.gz'.format(ic_prefix))
    mixfile    = op.join(meldir,  'melodic_mix')
    ftmixfile  = op.join(meldir,  'melodic_FTmix')

    # Create stub files, and the directory structure
    tests.make_dummy_files([icfile, mixfile, ftmixfile])

    nics = shape4D[-1]

    icimg = np.zeros(shape4D)
    for ic in range(nics):
        icimg[..., ic] = ic

    # rows=timepoints
    # coluumns=ICs
    mixdata = np.zeros((timepoints, nics))

    # rows=frequencies
    # columns=ICs
    if timepoints % 2: nfreqs = int(np.ceil(timepoints / 2.0))
    else:              nfreqs = timepoints // 2

    ftmixdata = np.zeros((nfreqs, nics))

    for ic in range(nics):
        mixdata[  :, ic] = ic
        ftmixdata[:, ic] = ic

    np.savetxt(mixfile,   mixdata)
    np.savetxt(ftmixfile, ftmixdata)
    fslimage.Image(icimg).save(icfile)

    if with_data:
        dataimg = np.zeros(list(shape4D[:3]) + [timepoints], dtype=np.int32)
        for t in range(timepoints):
            dataimg[..., t] = t

        hdr = nib.nifti1.Nifti1Header()
        hdr['pixdim'][4] = tr

        img = fslimage.Image(dataimg, header=hdr, xform=np.eye(4))
        img.save(datafile)

    if with_reportfile:
        tests.make_dummy_file(reportfile)

    if with_meanfile:
        nvoxels = np.prod(shape4D[:3])
        data = np.arange(0, nvoxels).reshape(shape4D[:3]).astype(np.int32)
        fslimage.Image(data).save(meanfile)

    return meldir


def test_MelodicImage_create():

    # non existent
    with pytest.raises(Exception):
        meli.MelodicImage('badfile')

    # bad file
    paths = ['analysis.ica/melodic_IC.nii.gz',
             'analysis.ica/melodic_mix',
             'analysis.ica/melodic_FTmix']
    paths = [op.join(*p.split('/')) for p in paths]
    with tests.testdir(paths) as testdir:
        path = op.join(testdir, 'analysis.ica', 'melodic_IC.nii.gz')
        with pytest.raises(Exception):
            meli.MelodicImage(path)

    for ic_prefix in ['melodic_IC', 'melodic_oIC']:

        with tests.testdir() as testdir:
            meldir      = _create_dummy_melodic_analysis(testdir,
                                                         ic_prefix=ic_prefix)
            icfile      = op.join(meldir, '{}.nii.gz'.format(ic_prefix))
            icfilenosuf = op.join(meldir, ic_prefix)

            # Should be able to specify the
            # melodic dir, or the IC image
            i = meli.MelodicImage(meldir)
            i = meli.MelodicImage(icfile)
            i = meli.MelodicImage(icfilenosuf)
            i = None


def test_MelodicImage_atts():

    with tests.testdir() as testdir:
        meldir = _create_dummy_melodic_analysis(testdir)
        img    = meli.MelodicImage(meldir)

        assert img.shape  == (10, 10, 10, 10)
        assert img.pixdim == ( 1,  1,  1,  1)
        assert np.all(img.voxToWorldMat == np.eye(4))
        assert img.numComponents() == 10
        assert img.getMelodicDir() == meldir

        assert img.getReportFile()          == mela.getReportFile(meldir)
        assert img.getTopLevelAnalysisDir() == mela.getTopLevelAnalysisDir(meldir)
        assert img.getDataFile()            == mela.getDataFile(meldir)
        assert img.getMeanFile()            == mela.getMeanFile(meldir)

        img = None


def test_MelodicImage_componentData():
    with tests.testdir() as testdir:
        meldir = _create_dummy_melodic_analysis(testdir)
        img    = meli.MelodicImage(meldir)
        nics   = img.numComponents()

        expectTS = mela.getComponentTimeSeries(  meldir)
        expectPS = mela.getComponentPowerSpectra(meldir)

        for ic in range(nics):
            assert np.all(img.getComponentTimeSeries(   ic) == expectTS[:, ic])
            assert np.all(img.getComponentPowerSpectrum(ic) == expectPS[:, ic])

        img = None


def test_MelodicImage_tr():

    # If data file not present, tr should default to 1.0
    with tests.testdir() as testdir:
        meldir = _create_dummy_melodic_analysis(testdir, with_data=False)
        img    = meli.MelodicImage(meldir)

        assert img.tr == 1

        img = None

    # Otherwise, it should be set to the datafile tr
    with tests.testdir() as testdir:
        meldir = _create_dummy_melodic_analysis(testdir, tr=5)
        img    = meli.MelodicImage(meldir)
        assert img.tr == 5

        img = None

    # The TR can be updated
    with tests.testdir() as testdir:

        cbCalled = [False]
        def trChanged(*a):
            cbCalled[0] = True

        meldir = _create_dummy_melodic_analysis(testdir, with_data=False)
        img    = meli.MelodicImage(meldir)

        img.register('cbname', trChanged, topic='tr')

        img.tr = 8

        assert cbCalled[0]
        assert img.tr == 8

        img = None
