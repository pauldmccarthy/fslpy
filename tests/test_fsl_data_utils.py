#!/usr/bin/env python
#
# test_fsl_data_utils.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import            shutil
import            os
import os.path as op

import numpy   as np

import fsl.utils.tempdir        as tempdir
import fsl.data.utils           as dutils

import fsl.utils.path           as fslpath
import fsl.data.image           as fslimage
import fsl.data.vtk             as fslvtk
import fsl.data.gifti           as fslgifti
import fsl.data.freesurfer      as fslfs
import fsl.data.mghimage        as fslmgh
import fsl.data.featimage       as featimage
import fsl.data.melodicimage    as melimage
import fsl.data.dtifit          as dtifit
import fsl.data.melodicanalysis as melanalysis
import fsl.data.featanalysis    as featanalysis

from . import (touch,
               make_mock_feat_analysis,
               make_mock_melodic_analysis,
               make_mock_dtifit_analysis)


def test_guessType():

    def asrt(path, cls):
        restype, respath = dutils.guessType(path)

        assert restype is cls

        if path.startswith('fsleyes://'):
            path = path[10:]

        # image path might not have an extension

        try:
            path = fslimage.addExt(path, mustExist=True)
        except fslimage.PathError:
            pass

        assert respath == op.abspath(path)

    with tempdir.tempdir() as td:

        touch('foo.nii')
        asrt('foo',               fslimage.Image)
        asrt('foo.nii',           fslimage.Image)
        asrt('fsleyes://foo',     fslimage.Image)
        asrt('fsleyes://foo.nii', fslimage.Image)
        os.remove('foo.nii')


        touch('foo.vtk')
        asrt('foo.vtk', fslvtk.VTKMesh)
        os.remove('foo.vtk')

        touch('foo.surf.gii')
        asrt('foo.surf.gii', fslgifti.GiftiMesh)
        os.remove('foo.surf.gii')

        touch('lh.pial')
        asrt('lh.pial', fslfs.FreesurferMesh)
        os.remove('lh.pial')

        touch('foo.mgz')
        asrt('foo.mgz', fslmgh.MGHImage)
        os.remove('foo.mgz')

        make_mock_melodic_analysis('filtered_func_data.ica',
                                   (10, 10, 10, 10),
                                   20)
        asrt('filtered_func_data.ica/melodic_IC',        melimage.MelodicImage)
        asrt('filtered_func_data.ica/melodic_IC.nii.gz', melimage.MelodicImage)
        asrt('filtered_func_data.ica',                   melimage.MelodicImage)
        asrt('filtered_func_data.ica/',                  melimage.MelodicImage)
        shutil.rmtree('filtered_func_data.ica')

        featdir = op.join(op.dirname(__file__),
                          'testdata', 'test_feat', '1stlevel_1.feat')
        make_mock_feat_analysis(featdir,
                                td,
                                (10, 10, 10, 10))
        asrt('1stlevel_1.feat/filtered_func_data',        featimage.FEATImage)
        asrt('1stlevel_1.feat/filtered_func_data.nii.gz', featimage.FEATImage)
        asrt('1stlevel_1.feat',                           featimage.FEATImage)

        make_mock_dtifit_analysis('dti', (10, 10, 10))
        asrt('dti', dtifit.DTIFitTensor)
        shutil.rmtree('dti')

        asrt('noexist', None)

        touch('norecognise')
        asrt('norecognise', None)
        touch('norecognise.txt')
        asrt('norecognise.txt', None)
        os.remove('norecognise')
        os.remove('norecognise.txt')


def test_makeWriteable():
    robuf = bytes(    b'\01\02\03\04')
    wbuf  = bytearray(b'\01\02\03\04')

    roarr = np.ndarray((4,), dtype=np.uint8, buffer=robuf)
    warr  = np.ndarray((4,), dtype=np.uint8, buffer=wbuf)

    warr.flags['WRITEABLE'] = False

    rocopy = dutils.makeWriteable(roarr)
    wcopy  = dutils.makeWriteable(warr)

    assert rocopy.base is not roarr.base
    assert wcopy .base is     warr .base

    rocopy[1] = 100
    wcopy[ 1] = 100
