#!/usr/bin/env python
#
# test_image.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op

import pytest
import glob

import numpy   as np
import nibabel as nib

from nibabel.spatialimages import ImageFileError

import fsl.data.constants as constants
import fsl.data.image     as fslimage
import fsl.utils.path     as fslpath


# Need to test:
#     - Create image from file name (create a temp .nii.gz)
#     - Create image from existing nibabel image
#     - Create image from numpy array
#     - calcRange
#     - loadData

def test_load(testdir):

    assert testdir is not None

    shouldPass = ['compressed',
                  'compressed.nii.gz',
                  'uncompressed',
                  'uncompressed.nii',
                  'img_hdr_pair',
                  'img_hdr_pair.img',
                  'img_hdr_pair.hdr',
                  'compressed_img_hdr_pair',
                  'compressed_img_hdr_pair.img.gz',
                  'compressed_img_hdr_pair.hdr.gz',
                  'ambiguous.nii',
                  'ambiguous.hdr',
                  'ambiguous.img',
                  'ambiguous.hdr.gz',
                  'ambiguous.img.gz']
    shouldRaise = [('notexist',        fslpath.PathError),
                   ('notexist.nii.gz', fslpath.PathError),
                   ('ambiguous',       fslpath.PathError),
                   ('notnifti',        ImageFileError),
                   ('notnifti.nii.gz', ImageFileError)]
    
    # Not raising an error means the test passes
    for fname in shouldPass:
        fslimage.Image(op.join(testdir, 'nifti_formats', fname))

    # These should raise an error
    for fname, exc in shouldRaise:
        with pytest.raises(exc):
            fslimage.Image(op.join(testdir, 'nifti_formats', fname))
            


def test_Image_atts(testdir):

    allowedExts = fslimage.ALLOWED_EXTENSIONS

    # (file, dims, pixdims)
    tests = [
        ('MNI152_T1_0.5mm',                           (364, 436, 364),   (0.5, 0.5, 0.5),      np.uint8),
        ('MNI152_T1_1mm',                             (182, 218, 182),   (1.0, 1.0, 1.0),      np.int16),
        ('MNI152_T1_2mm',                             (91,  109, 91),    (2.0, 2.0, 2.0),      np.int16),
        ('MNI152_T1_2mm_4D',                          (91,  109, 91, 5), (2.0, 2.0, 2.0, 1.0), np.int16),
        (op.join('nifti2D', 'MNI152_T1_2mm_sliceXY'), (91,  109, 1),     (2.0, 2.0, 2.0),      np.int16),
        (op.join('nifti2D', 'MNI152_T1_2mm_sliceXZ'), (91,  1,   91),    (2.0, 2.0, 2.0),      np.int16),
        (op.join('nifti2D', 'MNI152_T1_2mm_sliceYZ'), (1,   109, 91),    (2.0, 2.0, 2.0),      np.int16)]

    for path, dims, pixdims, dtype in tests:

        path = op.abspath(op.join(testdir, path))
        i    = fslimage.Image(path)

        assert tuple(i.shape)                       == tuple(dims)
        assert tuple(i.pixdim)                      == tuple(pixdims)
        assert tuple(i.nibImage.shape)              == tuple(dims)
        assert tuple(i.nibImage.header.get_zooms()) == tuple(pixdims)

        assert i.dtype      == dtype
        assert i.name       == op.basename(path)
        assert i.dataSource == fslpath.addExt(path, allowedExts, mustExist=True)


def test_looksLikeImage():

    # (file, expected)
    tests = [
        ('blah',        False),
        ('blah.moo',    False),
        ('blah.nii',    True),
        ('blah.nii.gz', True),
        ('blah.hdr',    True),
        ('blah.img',    True),
        ('blah.hdr.gz', True),
        ('blah.img.gz', True),
    ]

    for path, expected in tests:
        assert fslimage.looksLikeImage(path) == expected


def test_addExt(testdir):

    default = fslimage.defaultExt()

    # (file, mustExist, expected)
    tests = [
        ('blah',                           False, 'blah{}'.format(default)),
        ('blah.nii',                       False, 'blah.nii'),
        ('blah.nii.gz',                    False, 'blah.nii.gz'),
        ('blah.img',                       False, 'blah.img'),
        ('blah.hdr',                       False, 'blah.hdr'),
        ('blah.img.gz',                    False, 'blah.img.gz'),
        ('blah.hdr.gz',                    False, 'blah.hdr.gz'),
        ('compressed',                     True,  'compressed.nii.gz'),
        ('compressed.nii.gz',              True,  'compressed.nii.gz'),
        ('uncompressed',                   True,  'uncompressed.nii'),
        ('uncompressed.nii',               True,  'uncompressed.nii'),
        ('img_hdr_pair',                   True,  'img_hdr_pair.img'),
        ('img_hdr_pair.hdr',               True,  'img_hdr_pair.hdr'),
        ('img_hdr_pair.img',               True,  'img_hdr_pair.img'),
        ('compressed_img_hdr_pair',        True,  'compressed_img_hdr_pair.img.gz'),
        ('compressed_img_hdr_pair.img.gz', True,  'compressed_img_hdr_pair.img.gz'),
        ('compressed_img_hdr_pair.hdr.gz', True,  'compressed_img_hdr_pair.hdr.gz'),
        ('ambiguous.nii',                  True,  'ambiguous.nii'),
        ('ambiguous.nii.gz',               True,  'ambiguous.nii.gz'),
        ('ambiguous.img',                  True,  'ambiguous.img'),
        ('ambiguous.hdr',                  True,  'ambiguous.hdr'),
        ('ambiguous.img.gz',               True,  'ambiguous.img.gz'),
        ('ambiguous.hdr.gz',               True,  'ambiguous.hdr.gz')]

    for path, mustExist, expected in tests:
        if mustExist:
            path     = op.join(testdir, 'nifti_formats', path)
            expected = op.join(testdir, 'nifti_formats', expected)

        assert fslimage.addExt(path, mustExist) == expected

    with pytest.raises(fslimage.PathError):
        path = op.join(testdir, 'nifti_formats', 'ambiguous')
        fslimage.addExt(path, mustExist=True)


def test_Image_orientation(testdir):

    neuro = op.join(testdir, 'dtifit', 'neuro', 'dti_FA')
    radio = op.join(testdir, 'dtifit', 'radio', 'dti_FA')

    neuro = fslimage.Image(neuro)
    radio = fslimage.Image(radio)

    assert     neuro.isNeurological()
    assert not radio.isNeurological()

    # Both images should have the
    # same orientation in the
    # world coordinate system
    assert neuro.getOrientation(0, np.eye(4))           == constants.ORIENT_L2R
    assert neuro.getOrientation(1, np.eye(4))           == constants.ORIENT_P2A
    assert neuro.getOrientation(2, np.eye(4))           == constants.ORIENT_I2S
    assert radio.getOrientation(0, np.eye(4))           == constants.ORIENT_L2R
    assert radio.getOrientation(1, np.eye(4))           == constants.ORIENT_P2A
    assert radio.getOrientation(2, np.eye(4))           == constants.ORIENT_I2S

    # The radio image should be
    # l/r flipped in the voxel
    # coordinate system
    assert neuro.getOrientation(0, neuro.voxToWorldMat) == constants.ORIENT_L2R
    assert neuro.getOrientation(1, neuro.voxToWorldMat) == constants.ORIENT_P2A
    assert neuro.getOrientation(2, neuro.voxToWorldMat) == constants.ORIENT_I2S
    
    assert radio.getOrientation(0, radio.voxToWorldMat) == constants.ORIENT_R2L
    assert radio.getOrientation(1, radio.voxToWorldMat) == constants.ORIENT_P2A
    assert radio.getOrientation(2, radio.voxToWorldMat) == constants.ORIENT_I2S 


def test_Image_sqforms(testdir):

    benchmark   = fslimage.Image(op.join(testdir, 'MNI152_T1_2mm.nii.gz'))
    nosform     = fslimage.Image(op.join(testdir, 'MNI152_T1_2mm_nosform.nii.gz'))
    noqform     = fslimage.Image(op.join(testdir, 'MNI152_T1_2mm_noqform.nii.gz'))
    nosqform    = fslimage.Image(op.join(testdir, 'MNI152_T1_2mm_nosqform.nii.gz'))
    
    scalemat    = np.diag([2,   2,   2,   1])
    invScalemat = np.diag([0.5, 0.5, 0.5, 1])

    assert np.all(np.isclose(nosform.voxToWorldMat,  benchmark.voxToWorldMat))
    assert np.all(np.isclose(nosform.worldToVoxMat,  benchmark.worldToVoxMat))
    assert np.all(np.isclose(noqform.voxToWorldMat,  benchmark.voxToWorldMat))
    assert np.all(np.isclose(noqform.worldToVoxMat,  benchmark.worldToVoxMat))
    assert np.all(np.isclose(nosqform.voxToWorldMat, scalemat))
    assert np.all(np.isclose(nosqform.worldToVoxMat, invScalemat))
    

def test_2D_images(testdir):

    tests = [('MNI152_T1_2mm_sliceXY.nii.gz',          (91, 109, 1),    (2.0, 2.0, 2.0)),
             ('MNI152_T1_2mm_sliceXZ.nii.gz',          (91, 1,   91),   (2.0, 2.0, 2.0)),
             ('MNI152_T1_2mm_sliceYZ.nii.gz',          (1,  109, 91),   (2.0, 2.0, 2.0)),
             ('MNI152_T1_2mm_sliceXY_4D.nii.gz',       (91, 109, 1, 5), (2.0, 2.0, 2.0, 1.0)),

             # When you create an XY slice with
             # fslroi, it sets nifti/dim0 to 2.
             # This should still be read in as
             # a 3D image.
             ('MNI152_T1_2mm_sliceXY_bad_dim0.nii.gz', (91, 109, 1),  (2.0, 2.0, 2.0))]

    for fname, shape, pixdim in tests:

        fname  = op.join(testdir, 'nifti2D', fname)
        image  = fslimage.Image(fname)
        
        assert len(shape)  == len(image   .shape)
        assert len(shape)  == len(image[:].shape)
        assert len(pixdim) == len(image   .pixdim)

        assert tuple(map(float, shape))  == tuple(map(float, image   .shape))
        assert tuple(map(float, shape))  == tuple(map(float, image[:].shape))
        assert tuple(map(float, pixdim)) == tuple(map(float, image   .pixdim))
