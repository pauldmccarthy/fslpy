#!/usr/bin/env python
#
# test_fsl_mrs.py -
#
# Author: Vasilis Karlaftis <vasilis.karlaftis@ndcn.ox.ac.uk>
#

import pytest
import os
import json
import numpy as np
import nibabel as nib

import fsl.wrappers as fw
import fsl.data.image as fslimage
import fsl.utils.tempdir as tempdir
from fsl.tests.test_wrappers import testenv


# Tests may be executed without the fsl_mrs
# libs, but test modules need to be importable.
try:
    from nifti_mrs.nifti_mrs import NIFTI_MRS
except ImportError:
    NIFTI_MRS = None


pytestmark = pytest.mark.mrstest


def test_fsl_mrs():
    with testenv('fsl_mrs') as fsl_mrs:
        # test simple call
        result = fw.fsl_mrs('data', 'basis', 'output')
        expected = f'{fsl_mrs} --data data --output output --basis basis'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.fsl_mrs('data', 'basis', 'output', h2o='h2o', tissue_frac=['WM', 'GM', 'CSF'],
                            overwrite=True, config='fit_config.txt', ignore=['Gln', 'NAA'],
                            keep=['GABA', 'GSH'], combine=[['Cr', 'PCr'], ['PCh', 'GPC']],
                            metab_groups=['H2O', 'Mac'], ind_scale=['Cr', 'PCr'])
        expected = f'{fsl_mrs} --data data --output output --basis basis --h2o h2o --tissue_frac'\
                    ' WM GM CSF --overwrite --config fit_config.txt --ignore Gln NAA --keep GABA GSH'\
                    ' --combine Cr PCr --combine PCh GPC --metab_groups H2O Mac --ind_scale Cr PCr'
        assert result.stdout[0] == expected


def test_fsl_mrsi():
    with testenv('fsl_mrsi') as fsl_mrsi:
        # test simple call
        result = fw.fsl_mrsi('data', 'basis', 'output')
        expected = f'{fsl_mrsi} --data data --output output --basis basis'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.fsl_mrsi('data', 'basis', 'output', h2o='h2o', tissue_frac=['WM', 'GM', 'CSF'],
                             overwrite=True, config='fit_config.txt', ignore=['Gln', 'NAA'],
                             keep=['GABA', 'GSH'], combine=[['Cr', 'PCr'], ['PCh', 'GPC']],
                             metab_groups=['H2O', 'Mac'], ind_scale=['Cr', 'PCr'])
        expected = f'{fsl_mrsi} --data data --output output --basis basis --h2o h2o --tissue_frac'\
                    ' WM GM CSF --overwrite --config fit_config.txt --ignore Gln NAA --keep GABA GSH'\
                    ' --combine Cr PCr --combine PCh GPC --metab_groups H2O Mac --ind_scale Cr PCr'
        assert result.stdout[0] == expected


def test_fsl_mrs_preproc():
    with testenv('fsl_mrs_preproc') as fsl_mrs_preproc:
        # test simple call
        result = fw.fsl_mrs_preproc('data', 'reference', 'output')
        expected = f'{fsl_mrs_preproc} --data data --reference reference --output output'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.fsl_mrs_preproc('data', 'reference', 'output', quant='quant', truncate_fid='1',
                                    remove_water=True, report=True, overwrite=True)
        expected = f'{fsl_mrs_preproc} --data data --reference reference --output output --quant'\
                    ' quant --truncate-fid 1 --remove-water --report --overwrite'
        assert result.stdout[0] == expected


def test_fsl_mrs_preproc_edit():
    with testenv('fsl_mrs_preproc_edit') as fsl_mrs_preproc_edit:
        # test simple call
        result = fw.fsl_mrs_preproc_edit('data', 'reference', 'output')
        expected = f'{fsl_mrs_preproc_edit} --data data --reference reference --output output'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.fsl_mrs_preproc_edit('data', 'reference', 'output', quant='quant', truncate_fid='1',
                                         remove_water=True, report=True, overwrite=True)
        expected = f'{fsl_mrs_preproc_edit} --data data --reference reference --output output --quant'\
                    ' quant --truncate-fid 1 --remove-water --report --overwrite'
        assert result.stdout[0] == expected


def test_svs_segment():
    with testenv('svs_segment') as svs_segment:
        # test simple call
        result = fw.svs_segment('svs')
        expected = f'{svs_segment} svs'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.svs_segment('svs', anat='anat', output='output', no_normalisation=True)
        expected = f'{svs_segment} svs --anat anat --output output --no_normalisation'
        assert result.stdout[0] == expected

        # similar call but with single dashed arguments
        result = fw.svs_segment('svs', a='anat', o='output', m=True)
        expected = f'{svs_segment} svs --anat anat --output output --mask_only'
        assert result.stdout[0] == expected


def test_mrsi_segment():
    with testenv('mrsi_segment') as mrsi_segment:
        # test simple call
        result = fw.mrsi_segment('mrsi')
        expected = f'{mrsi_segment} mrsi'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.mrsi_segment('mrsi', anat='anat', output='output', no_normalisation=True)
        expected = f'{mrsi_segment} mrsi --anat anat --output output --no_normalisation'
        assert result.stdout[0] == expected

        # same call but with single dashed arguments
        result = fw.mrsi_segment('mrsi', a='anat', o='output', no_normalisation=True)
        expected = f'{mrsi_segment} mrsi --anat anat --output output --no_normalisation'
        assert result.stdout[0] == expected


def test_fsl_dynmrs():
    with testenv('fsl_dynmrs') as fsl_dynmrs:
        # test simple call
        result = fw.fsl_dynmrs('data', 'basis', 'output', 'dyn_config', 'time_variables')
        expected = f'{fsl_dynmrs} --data data --basis basis --output output --dyn_config dyn_config'\
                    ' --time_variables time_variables'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.fsl_dynmrs('data', 'basis', 'output', 'dyn_config', ['time_variables1' , 'time_variables2'],
                               baseline_order=0, spatial_mask='mask', metab_groups=['H2O', 'Mac'], parallel='off',
                               report=True)
        expected = f'{fsl_dynmrs} --data data --basis basis --output output --dyn_config dyn_config'\
                    ' --time_variables time_variables1 time_variables2 --baseline_order 0 --spatial-mask mask'\
                    ' --metab_groups H2O Mac --parallel off --report'
        assert result.stdout[0] == expected


def test_basis2spec():
    with testenv('basis2spec') as basis2spec:
        # test simple call
        result = fw.basis2spec('basis', 'reference', 'output')
        expected = f'{basis2spec} --basis basis --reference reference --output output'
        print(result)
        print('this is it^')
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.basis2spec('basis', 'reference', 'output', linewidth='5.0', ignore=['Gln', 'NAA'])
        expected = f'{basis2spec} --basis basis --reference reference --output output --linewidth 5.0'\
                    ' --ignore Gln NAA'
        assert result.stdout[0] == expected


def test_fmrs_stats():
    with testenv('fmrs_stats') as fmrs_stats:
        # test simple call
        result = fw.fmrs_stats('data', 'output')
        expected = f'{fmrs_stats} --data data --output output'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.fmrs_stats(['data1', 'data2'], 'output', fl_contrasts='fl_contrasts.json', hl_design='hl_design.mat',
                               hl_contrasts='hl_contrasts.con', hl_contrast_names=['cont1', 'cont2'],
                               mean_contrasts=[['beta0', 'beta1'], ['beta2', 'beta3']],
                               combine=[['NAA', 'NAAG'], ['Cr', 'PCr'], ['PCh', 'GPC']],
                               overwrite=True)
        expected = f'{fmrs_stats} --data data1 data2 --output output --fl-contrasts fl_contrasts.json --hl-design'\
                    ' hl_design.mat --hl-contrasts hl_contrasts.con --hl-contrast-names cont1 cont2'\
                    ' --mean-contrasts beta0 beta1 --mean-contrasts beta2 beta3'\
                    ' --combine NAA NAAG --combine Cr PCr --combine PCh GPC --overwrite'
        assert result.stdout[0] == expected


def test_fileOrNiftiMRS():
    @fw.wrapperutils.fileOrNiftiMRS('img1', 'img2', 'output')
    def func(img1, **kwargs):
        img1   = nib.load(img1)
        img2   = nib.load(kwargs['img2'])
        output = nib.nifti1.Nifti1Image(
            np.asanyarray(img1.dataobj) * np.asanyarray(img2.dataobj),
            img1.affine,
            img1.header.copy())
        nib.save(output, kwargs['output'])

    with tempdir.tempdir():

        img1     = nib.nifti1.Nifti1Image(
            np.array([[1,  2], [ 3,  4]], dtype=np.int32), np.eye(4))
        img2     = nib.nifti1.Nifti1Image(
            np.array([[5,  6], [ 7,  8]], dtype=np.int32), np.eye(4))
        img3     = nib.nifti1.Nifti1Image(
            np.array([[1,  2], [ 3,  4]], dtype=np.int32), np.eye(4))
        expected = np.array([[5, 12], [21, 32]], dtype=np.int32)
        img1.header.extensions.append(
            nib.nifti1.Nifti1Extension(
                44,
                json.dumps({
                    'ResonantNucleus'       : ['1H'],
                    'SpectrometerFrequency' : [123.456],
                }).encode('utf-8')))
        img1.header['intent_name'] = 'mrs_v0_2'.encode()
        nib.save(img1, 'img1.nii')
        img2.header.extensions.append(
            nib.nifti1.Nifti1Extension(
                44,
                json.dumps({
                    'ResonantNucleus'       : ['1H'],
                    'SpectrometerFrequency' : [123.456],
                }).encode('utf-8')))
        img2.header['intent_name'] = 'mrs_v0_2'.encode()
        nib.save(img2, 'img2.nii')

        # file  file  file
        func('img1.nii', img2='img2.nii', output='output.nii')
        assert np.all(np.asanyarray(nib.load('output.nii').dataobj) == expected)
        os.remove('output.nii')

        # file  file  array
        result = func('img1.nii', img2='img2.nii', output=fw.wrapperutils.LOAD)['output']
        assert np.all(np.asanyarray(result.dataobj) == expected)

        # file  array file
        func('img1.nii', img2=img2, output='output.nii')
        assert np.all(np.asanyarray(nib.load('output.nii').dataobj) == expected)
        os.remove('output.nii')

        # file  array array
        result = func('img1.nii', img2=img2, output=fw.wrapperutils.LOAD)['output']
        assert np.all(np.asanyarray(result.dataobj) == expected)

        # array file  file
        func(img1, img2='img2.nii', output='output.nii')
        assert np.all(np.asanyarray(nib.load('output.nii').dataobj) == expected)
        os.remove('output.nii')

        # array file  array
        result = func(img1, img2='img2.nii', output=fw.wrapperutils.LOAD)['output']
        assert np.all(np.asanyarray(result.dataobj) == expected)

        # array array file
        func(img1, img2=img2, output='output.nii')
        assert np.all(np.asanyarray(nib.load('output.nii').dataobj) == expected)
        os.remove('output.nii')

        # array array array
        result = func(img1, img2=img2, output=fw.wrapperutils.LOAD)['output']
        assert np.all(np.asanyarray(result.dataobj) == expected)

        # in-memory image, file, file
        result = func(img3, img2='img2.nii', output='output.nii')
        assert np.all(np.asanyarray(nib.load('output.nii').dataobj) == expected)
        os.remove('output.nii')

        # fslimage, file, load
        result = func(fslimage.Image(img1), img2='img2.nii',
                      output=fw.wrapperutils.LOAD)['output']
        assert isinstance(result, fslimage.Image)
        assert np.all(result[:].squeeze() == expected)

        # fslimage, fslimage, load
        result = func(fslimage.Image(img1), img2=fslimage.Image(img2),
                      output=fw.wrapperutils.LOAD)['output']
        assert isinstance(result, fslimage.Image)
        assert np.all(result[:].squeeze() == expected)

        # fslimage, nib.image, load
        result = func(fslimage.Image(img1), img2=img2,
                      output=fw.wrapperutils.LOAD)['output']
        assert isinstance(result, fslimage.Image)
        assert np.all(result[:].squeeze() == expected)

        # nib.image, nib.image, load
        result = func(img1, img2=img2, output=fw.wrapperutils.LOAD)['output']
        assert isinstance(result, nib.nifti1.Nifti1Image)
        assert np.all(np.asanyarray(result.dataobj)[:] == expected)

        # nifti_mrs, fslimage, load
        result = func(NIFTI_MRS(img1, valid_on_creation=False),
                      img2=fslimage.Image(img2),
                      output=fw.wrapperutils.LOAD)['output']
        assert isinstance(result, NIFTI_MRS)
        assert np.all(np.asanyarray(result.image[:].squeeze()) == expected)

        # nib.image, nifti_mrs, load
        result = func(img1,
                      img2=NIFTI_MRS(img2, valid_on_creation=False),
                      output=fw.wrapperutils.LOAD)['output']
        assert isinstance(result, NIFTI_MRS)
        assert np.all(np.asanyarray(result.image[:].squeeze()) == expected)

        # nifti_mrs, nifti_mrs, file
        result = func(NIFTI_MRS(img1, valid_on_creation=False),
                      img2=NIFTI_MRS(img2, valid_on_creation=False),
                      output='output.nii')
        assert np.all(np.asanyarray(NIFTI_MRS('output.nii').image[:].squeeze()) == expected)
        os.remove('output.nii')
