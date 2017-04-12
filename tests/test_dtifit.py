#!/usr/bin/env python
#
# test_dtifit.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op
import numpy   as np

import pytest

import tests
import fsl.data.dtifit as dtifit
import fsl.data.image  as fslimage


def test_getDTIFitDataPrefix_and_isDTIFitPath():

    def make_dtifit_dir(dir, prefix, suffixes):
        for s in suffixes:
            path = op.join(dir, '{}{}'.format(prefix, s))
            with open(path, 'wt') as f:
                f.write(path) 

    prefixes    = ['dti', 'blob', 'random-prefix', '01234']
    suffixes    = ['_V1.nii', '_V2.nii', '_V3.nii',
                   '_L1.nii', '_L2.nii', '_L3.nii']
    badSuffixes = ['_V1.txt', '_V2.nii', '_V3.nii',
                   '_L1.txt', '_L2.tar', '_L3.nii'] 


    # Valid dtifit directories
    with tests.testdir() as testdir:
        for p in prefixes:
            
            tests.cleardir(testdir)
            make_dtifit_dir(testdir, p, suffixes)
            assert dtifit.getDTIFitDataPrefix(testdir) == p
            assert dtifit.isDTIFitPath(testdir)

    # Invalid dtifit dir - one file missing
    with tests.testdir() as testdir:
        make_dtifit_dir(testdir, 'dti', suffixes[:-1])
        assert dtifit.getDTIFitDataPrefix(testdir) is None
        assert not dtifit.isDTIFitPath(testdir)

    # Invalid dtifit dir - non-nifti files
    with tests.testdir() as testdir:
        make_dtifit_dir(testdir, 'dti', badSuffixes)
        assert dtifit.getDTIFitDataPrefix(testdir) is None
        assert not dtifit.isDTIFitPath(testdir)

    # Ambiguous dtifit dir - multiple
    # potential prefixes. Should return
    # the first (alphabetical) one.
    with tests.testdir() as testdir:
        make_dtifit_dir(testdir, 'dti1', suffixes)
        make_dtifit_dir(testdir, 'dti2', suffixes)
        assert dtifit.getDTIFitDataPrefix(testdir) == 'dti1'
        assert dtifit.isDTIFitPath(testdir)


def test_looksLikeTensorImage():
    # dtifit outputs one of two formats:
    #   - the eigenvectors/values of the tensor matrix
    #   - the raw values of the tensor matrix
    #
    # looksLikeTensorImage tests for the latter

    testcases = [((10, 10, 10),    False),
                 ((10, 10, 10, 5), False),
                 ((10, 10, 10, 6), True)]

    with tests.testdir() as testdir:

        fname = op.join(testdir, 'tensor_image.nii')

        for dims, expected in testcases:

            tests.make_random_image(fname, dims=dims)
            img = fslimage.Image(fname)

            assert dtifit.looksLikeTensorImage(img) == expected


def test_decomposeTensorMatrix():

    # A few tensor matrices
    tensorMatrices = np.array([
        [ 0.0032335606, -0.0000166876, 0.0000524589, 0.0032367723,  0.0000392826,  0.0028319934],
        [ 0.0016628219,  0.0001651855, 0.0000678183, 0.0001300842, -0.0000293543,  0.0000450112],
        [ 0.0006679352, -0.0000149214, 0.0000335666, 0.0007552942, -0.0003789219,  0.0008345888]])

    # Expected eigenvalues and vectors
    expEigVals = np.array([
        [0.003252062,  0.0032290765,  0.002821188],
        [0.0016829496, 0.00012794147, 0.000027026183],
        [0.0011783227, 0.00066605647, 0.00041343897]])

    expEigVecs = np.array([
        [[ 0.701921939849854, -0.711941838264465,  0.021080270409584],
         [-0.700381875038147, -0.695301055908203, -0.16131255030632 ],
         [-0.129502296447754, -0.098464585840702,  0.986678183078766]],
        [[-0.993700802326202, -0.104962401092052, -0.039262764155865], 
         [-0.081384353339672,  0.916762292385101, -0.391054302453995],
         [-0.077040620148182,  0.385395616292953,  0.919529736042023]],
        [[ 0.068294189870358, -0.666985750198364,  0.741933941841125],
         [ 0.996652007102966,  0.079119503498077, -0.020613647997379],
         [ 0.044952429831028, -0.740857720375061, -0.670156061649323]]])

    tensorMatrices = tensorMatrices.reshape(1, 1, 3, 6)
    expEigVals     = expEigVals    .reshape(1, 1, 3, 3)
    expEigVecs     = expEigVecs    .reshape(1, 1, 3, 3, 3)
 
    v1, v2, v3, l1, l2, l3 = dtifit.decomposeTensorMatrix(tensorMatrices)

    expV1 = expEigVecs[:, :, :, 0]
    expV2 = expEigVecs[:, :, :, 1]
    expV3 = expEigVecs[:, :, :, 2]
    expL1 = expEigVals[:, :, :, 0]
    expL2 = expEigVals[:, :, :, 1]
    expL3 = expEigVals[:, :, :, 2]

    assert np.all(np.isclose(l1, expL1))
    assert np.all(np.isclose(l2, expL2))
    assert np.all(np.isclose(l3, expL3))

    # Vector signs are arbitrary
    for vox in range(3):
        for resvec, expvec in zip([v1, v2, v3], [expV1, expV2, expV3]):
            
            resvec = resvec[:, :, vox]
            expvec = expvec[:, :, vox]

            assert np.all(np.isclose(resvec,  expvec)) or \
                   np.all(np.isclose(resvec, -expvec))


def test_DTIFitTensor():

    with tests.testdir() as testdir:

        with pytest.raises(Exception):
            dtifit.DTIFitTensor(testdir)

        v1file = op.join(testdir, 'dti_V1.nii')
        v2file = op.join(testdir, 'dti_V2.nii')
        v3file = op.join(testdir, 'dti_V3.nii')
        l1file = op.join(testdir, 'dti_L1.nii')
        l2file = op.join(testdir, 'dti_L2.nii')
        l3file = op.join(testdir, 'dti_L3.nii')

        v1 = tests.make_random_image(v1file, (5, 5, 5, 3)).get_data()
        v2 = tests.make_random_image(v2file, (5, 5, 5, 3)).get_data()
        v3 = tests.make_random_image(v3file, (5, 5, 5, 3)).get_data()
        l1 = tests.make_random_image(l1file, (5, 5, 5))   .get_data()
        l2 = tests.make_random_image(l2file, (5, 5, 5))   .get_data()
        l3 = tests.make_random_image(l3file, (5, 5, 5))   .get_data()

        dtiobj = dtifit.DTIFitTensor(testdir)

        assert np.all(np.isclose(dtiobj.V1()[:], v1))
        assert np.all(np.isclose(dtiobj.V2()[:], v2))
        assert np.all(np.isclose(dtiobj.V3()[:], v3))
        assert np.all(np.isclose(dtiobj.L1()[:], l1))
        assert np.all(np.isclose(dtiobj.L2()[:], l2))
        assert np.all(np.isclose(dtiobj.L3()[:], l3))

        v1 = fslimage.Image(v1file)

        assert np.all(np.isclose(dtiobj.voxToWorldMat, v1.voxToWorldMat))
        assert np.all(np.isclose(dtiobj.shape[:3],     v1.shape[:3]))
        assert np.all(np.isclose(dtiobj.pixdim[:3],    v1.pixdim[:3]))
