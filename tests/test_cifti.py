import pytest
from fsl.data import cifti
import os.path as op
import numpy as np
import nibabel as nib
from numpy import testing
import tests


def test_read_gifti():
    testdir = op.join(op.dirname(__file__), 'testdata')

    shapefile = op.join(testdir, 'example.shape.gii')
    ref_data = nib.load(shapefile).darrays[0].data

    data = cifti.load(shapefile)
    assert isinstance(data, cifti.DenseCifti)
    assert data.arr.shape == (642, )
    testing.assert_equal(data.arr, ref_data)
    testing.assert_equal(data.brain_model_axis.vertex, np.arange(642))
    assert len(data.brain_model_axis.nvertices) == 1
    assert data.brain_model_axis.nvertices['CIFTI_STRUCTURE_OTHER'] == 642

    data = cifti.load(shapefile, mask_values=(ref_data[0], ))
    assert isinstance(data, cifti.DenseCifti)
    assert data.arr.shape == (np.sum(ref_data != ref_data[0]), )
    testing.assert_equal(data.arr, ref_data[ref_data != ref_data[0]])
    testing.assert_equal(data.brain_model_axis.vertex, np.where(ref_data != ref_data[0])[0])
    assert len(data.brain_model_axis.nvertices) == 1
    assert data.brain_model_axis.nvertices['CIFTI_STRUCTURE_OTHER'] == 642

    cifti.load(op.join(testdir, 'example'))


def test_read_nifti():
    mask = np.random.randint(2, size=(10, 10, 10)) > 0
    values = np.random.randn(10, 10, 10)
    for mask_val in (0, np.nan):
        values[~mask] = mask_val
        affine = np.concatenate((np.random.randn(3, 4), np.array([0, 0, 0, 1])[None, :]), axis=0)
        with tests.testdir():
            nib.Nifti1Image(values, affine).to_filename("masked_image.nii.gz")
            data = cifti.load("masked_image")
            assert isinstance(data, cifti.DenseCifti)
            testing.assert_equal(data.arr, values[mask])
            testing.assert_allclose(data.brain_model_axis.affine, affine)
            assert len(data.brain_model_axis.nvertices) == 0
