#!/usr/bin/env python
#
# test_image.py - Unit tests for the fsl.data.image module.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Unit tests for the fsl.data.image module. """


import os.path   as op
import itertools as it
import              tempfile
import              shutil
import              glob

import pytest

import numpy        as np
import numpy.linalg as npla
import nibabel      as nib

from nibabel.spatialimages import ImageFileError

import fsl.data.constants as constants
import fsl.data.image     as fslimage
import fsl.utils.path     as fslpath

from . import make_random_image
from . import make_dummy_file


def make_image(filename,
               imgtype=1,
               dims=(10, 10, 10),
               pixdims=(1, 1, 1),
               dtype=np.float32):
    """Convenience function which makes an image containing random data.
    Saves and returns the nibabel object.

    imgtype == 0: ANALYZE
    imgtype == 1: NIFTI1
    imgtype == 2: NIFTI2
    """

    if imgtype == 0: filename = '{}.img'.format(filename)
    else:            filename = '{}.nii'.format(filename)

    if   imgtype == 0: hdr = nib.AnalyzeHeader()
    elif imgtype == 1: hdr = nib.Nifti1Header()
    elif imgtype == 2: hdr = nib.Nifti2Header()

    pixdims = pixdims[:len(dims)]

    hdr.set_data_dtype(dtype)
    hdr.set_data_shape(dims)
    hdr.set_zooms([abs(p) for p in pixdims])

    xform = np.eye(4)
    for i, p in enumerate(pixdims):
        xform[i, i] = p
    
    data  = np.array(np.random.random(dims) * 100, dtype=dtype)

    if   imgtype == 0: img = nib.AnalyzeImage(data, xform, hdr)
    elif imgtype == 1: img = nib.Nifti1Image( data, xform, hdr)
    elif imgtype == 2: img = nib.Nifti2Image( data, xform, hdr)

    nib.save(img, filename)

    return img



# Need to test:
#     - Create image from existing nibabel image
#     - Create image from numpy array
#     - calcRange
#     - loadData


def test_load():
    """Create an Image from a file name. """

    # notnifti.nii.gz is just a plain text
    # file, the rest are NIFTI images
    toCreate = ['compressed.nii.gz',
                'uncompressed.nii',
                'img_hdr_pair.img',
                'compressed_img_hdr_pair.img.gz',
                'ambiguous.nii',
                'ambiguous.img',
                'ambiguous.img.gz',
                'notnifti.nii.gz']
    

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

    testdir = tempfile.mkdtemp()

    for f in toCreate:
        
        if f.startswith('notnifti'):
            make_dummy_file(op.join(testdir, f))
        else:
            make_random_image(op.join(testdir, f))
            
    # Not raising an error means the test passes
    try:
        for fname in shouldPass:
            fslimage.Image(op.join(testdir, fname))

        # These should raise an error
        for fname, exc in shouldRaise:
            with pytest.raises(exc):
                fslimage.Image(op.join(testdir, fname))
    finally:
        shutil.rmtree(testdir)


def  test_Image_atts_analyze(): _test_Image_atts(0) 
def  test_Image_atts_nifti1():  _test_Image_atts(1)
def  test_Image_atts_nifti2():  _test_Image_atts(2)
def _test_Image_atts(imgtype):
    """Test that basic Nifti/Image attributes are correct. """
    
    testdir     = tempfile.mkdtemp()
    allowedExts = fslimage.ALLOWED_EXTENSIONS
    fileGroups  = fslimage.FILE_GROUPS

    # (file, dims, pixdims, dtype)
    dtypes = [np.uint8, np.int16, np.int32, np.float32, np.double]
    dims   = [(10,  1,  1),
              (1,  10,  1),
              (1,  1,  10),
              (10,  10, 1),
              (10,  1, 10),
              (1,  10, 10),
              (10, 10, 10),
              (1,   1,  1, 5),
              (10,  10, 1, 5),
              (10,  1, 10, 5),
              (1,  10, 10, 5),
              (10, 10, 10, 5)]
    pixdims = [(0.5, 0.5, 0.5, 2),
               (1.0, 1.0, 1.0, 2),
               (2.0, 2.0, 2.0, 2),
               (1.0, 5.0, 1.0, 3)]

    tests = list(it.product(dims, pixdims, dtypes))
    paths = ['test{:03d}'.format(i) for i in range(len(tests))]
                       
    for path, (dims, pixdims, dtype) in zip(paths, tests):

        ndims   = len(dims)
        pixdims = pixdims[:ndims] 

        path = op.abspath(op.join(testdir, path))
        make_image(path, imgtype, dims, pixdims, dtype)

    try:

        for path, (dims, pixdims, dtype) in zip(paths, tests):

            ndims   = len(dims)
            pixdims = pixdims[:ndims]

            path = op.abspath(op.join(testdir, path))
            i    = fslimage.Image(path)

            assert tuple(i.shape)                       == tuple(dims)
            assert tuple(i.pixdim)                      == tuple(pixdims)
            assert tuple(i.nibImage.shape)              == tuple(dims)
            assert tuple(i.nibImage.header.get_zooms()) == tuple(pixdims)

            assert i.dtype      == dtype
            assert i.name       == op.basename(path)
            assert i.dataSource == fslpath.addExt(path,
                                                  allowedExts=allowedExts,
                                                  mustExist=True,
                                                  fileGroups=fileGroups)
    finally:
        shutil.rmtree(testdir)


def test_looksLikeImage():
    """Test the looksLikeImage function. """

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


def test_addExt():
    """Test the addExt function. """

    default = fslimage.defaultExt()
    testdir = tempfile.mkdtemp()

    toCreate = [
        'compressed.nii.gz',
        'uncompressed.nii',
        'img_hdr_pair.img',
        'compressed_img_hdr_pair.img.gz',
        'ambiguous.nii',
        'ambiguous.nii.gz',
        'ambiguous.img',
        'ambiguous.img.gz'
    ]

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

    for path in toCreate:
        path = op.abspath(op.join(testdir, path))
        make_random_image(path) 

    try:
        for path, mustExist, expected in tests:

            path     = op.abspath(op.join(testdir, path))
            expected = op.abspath(op.join(testdir, expected))

            assert fslimage.addExt(path, mustExist) == expected

        # Make sure that an ambiguous path fails
        with pytest.raises(fslimage.PathError):
            path = op.join(testdir, 'ambiguous')
            fslimage.addExt(path, mustExist=True)
    finally:
        shutil.rmtree(testdir)

def  test_Image_orientation_analyze_neuro(): _test_Image_orientation(0, 'neuro')
def  test_Image_orientation_analyze_radio(): _test_Image_orientation(0, 'radio')
def  test_Image_orientation_nifti1_neuro():  _test_Image_orientation(1, 'neuro')
def  test_Image_orientation_nifti1_radio():  _test_Image_orientation(1, 'radio')
def  test_Image_orientation_nifti2_neuro():  _test_Image_orientation(2, 'neuro')
def  test_Image_orientation_nifti2_radio():  _test_Image_orientation(2, 'radio') 
def _test_Image_orientation(imgtype, voxorient):
    """Test the Nifti.isNeurological and Nifti.getOrientation methods. """

    testdir   = tempfile.mkdtemp()
    imagefile = op.join(testdir, 'image')

    # an image with RAS voxel storage order
    # (affine has a positive determinant)
    # is said to be "neurological", whereas
    # an image with LAS voxel storage order
    # (negative determinant - x axis must
    # be flipped to bring it into RAS nifti
    # world coordinates)) is said to be
    # "radiological".  The make_image function
    # forms the affine from these pixdims.
    if   voxorient == 'neuro': pixdims = ( 1, 1, 1)
    elif voxorient == 'radio': pixdims = (-1, 1, 1)

    make_image(imagefile, imgtype, (10, 10, 10), pixdims, np.float32)

    image = fslimage.Image(imagefile)

    # analyze images are always assumed to be
    # stored in radiological (LAS) orientation
    if imgtype == 0:
        expectNeuroTest       = False
        expectvox0Orientation = constants.ORIENT_R2L
        expectvox1Orientation = constants.ORIENT_P2A
        expectvox2Orientation = constants.ORIENT_I2S
        
    elif voxorient == 'neuro':
        expectNeuroTest       = True
        expectvox0Orientation = constants.ORIENT_L2R
        expectvox1Orientation = constants.ORIENT_P2A
        expectvox2Orientation = constants.ORIENT_I2S
    else:
        expectNeuroTest       = False
        expectvox0Orientation = constants.ORIENT_R2L
        expectvox1Orientation = constants.ORIENT_P2A
        expectvox2Orientation = constants.ORIENT_I2S

    try:

        assert image.isNeurological() == expectNeuroTest

        # All images should have the
        # same orientation in the
        # world coordinate system
        assert image.getOrientation(0, np.eye(4)) == constants.ORIENT_L2R
        assert image.getOrientation(1, np.eye(4)) == constants.ORIENT_P2A
        assert image.getOrientation(2, np.eye(4)) == constants.ORIENT_I2S

        # But the voxel orientation
        # is dependent on the affine
        affine = image.voxToWorldMat
        assert image.getOrientation(0, affine) == expectvox0Orientation
        assert image.getOrientation(1, affine) == expectvox1Orientation
        assert image.getOrientation(2, affine) == expectvox2Orientation

    finally:
        shutil.rmtree(testdir)


def  test_Image_sqforms_nifti1_normal():   _test_Image_sqforms(1, 1, 1)
def  test_Image_sqforms_nifti1_nosform():  _test_Image_sqforms(1, 0, 1)
def  test_Image_sqforms_nifti1_noqform():  _test_Image_sqforms(1, 1, 0)
def  test_Image_sqforms_nifti1_nosqform(): _test_Image_sqforms(1, 1, 0)
def  test_Image_sqforms_nifti2_normal():   _test_Image_sqforms(2, 1, 1)
def  test_Image_sqforms_nifti2_nosform():  _test_Image_sqforms(2, 0, 1)
def  test_Image_sqforms_nifti2_noqform():  _test_Image_sqforms(2, 1, 0)
def  test_Image_sqforms_nifti2_nosqform(): _test_Image_sqforms(2, 1, 0) 
def _test_Image_sqforms(imgtype, sformcode, qformcode):
    """Test the Nifti.getXFormCode method, and the voxToWorldMat/worldToVoxMat
    attributes for NIFTI images with the given sform/qform code combination.
    """

    testdir = tempfile.mkdtemp()

    imagefile = op.abspath(op.join(testdir, 'image.nii.gz'))

    # For an image with no s/q form, we expect the
    # fallback affine - a simple scaling matrix.
    # We add some offsets to the actual affine so
    # we can distinguish it from the fallback affine.
    scaleMat      = np.diag([2,   2,   2,   1])
    invScaleMat   = np.diag([0.5, 0.5, 0.5, 1])
    affine        = np.array(scaleMat)
    affine[:3, 3] = [25, 20, 20]
    invAffine     = npla.inv(affine)

    image = make_image(imagefile, imgtype, (10, 10, 10), (2, 2, 2), np.float32)

    image.set_sform(affine, sformcode)
    image.set_qform(affine, qformcode)
    image.update_header()

    nib.save(image, imagefile)

    # No s or qform - we expect the fallback affine
    if sformcode == 0 and qformcode == 0:
        expAffine    = scaleMat
        invExpAffine = invScaleMat
        expCode      = constants.NIFTI_XFORM_UNKNOWN

    # No sform, but valid qform - expect the affine
    elif sformcode == 0 and qformcode > 0:
        expAffine    = affine
        invExpAffine = invAffine
        expCode      = qformcode

    # Valid sform (qform irrelevant) - expect the affine
    elif sformcode > 0:
        expAffine    = affine
        invExpAffine = invAffine
        expCode      = sformcode 

    image = fslimage.Image(imagefile)
    
    try:
        assert np.all(np.isclose(image.voxToWorldMat,  expAffine))
        assert np.all(np.isclose(image.worldToVoxMat,  invExpAffine))

        assert image.getXFormCode()        == expCode
        assert image.getXFormCode('sform') == sformcode
        assert image.getXFormCode('qform') == qformcode
    finally:
        shutil.rmtree(testdir)


def  test_Image_changeXform_analyze(): _test_Image_changeXform(0) 
def  test_Image_changeXform_nifti1():  _test_Image_changeXform(1)
def  test_Image_changeXform_nifti2():  _test_Image_changeXform(2) 
def _test_Image_changeXform(imgtype):
    """Test changing the Nifti.voxToWorldMat attribute. """

    testdir   = tempfile.mkdtemp()
    imagefile = op.join(testdir, 'image')

    make_image(imagefile, imgtype)

    notified = {}

    def onXform(*a):
        notified['xform'] = True

    def onSave(*a):
        notified['save'] = True

    img = fslimage.Image(imagefile)

    img.register('name1', onXform, 'transform')
    img.register('name2', onSave,  'saveState')

    newXform = np.array([[5, 0, 0, 10],
                         [0, 2, 0, 23],
                         [0, 0, 14, 5],
                         [0, 0, 0, 1]])

    try:

        # Image state should initially be saved
        assert img.saveState

        if imgtype == 0:
            # ANALYZE affine is not editable 
            with pytest.raises(Exception):
                img.voxToWorldMat = newXform
            return

        img.voxToWorldMat = newXform

        invx = npla.inv(newXform)

        # Did we get notified?
        assert notified.get('xform', False)
        assert notified.get('save',  False)
        assert not img.saveState

        # Did the affine get updated?
        assert np.all(np.isclose(img.voxToWorldMat, newXform))
        assert np.all(np.isclose(img.worldToVoxMat, invx))
    finally:
        shutil.rmtree(testdir)


def  test_Image_changeData_analyze(seed): _test_Image_changeData(0)
def  test_Image_changeData_nifti1(seed):  _test_Image_changeData(1)
def  test_Image_changeData_nifti2(seed):  _test_Image_changeData(2) 
def _test_Image_changeData(imgtype):
    """Test that changing image data triggers notification, and also causes
    the dataRange attribute to be updated.
    """

    testdir   = tempfile.mkdtemp()
    imagefile = op.join(testdir, 'image')
    
    make_image(imagefile, imgtype)

    img = fslimage.Image(imagefile)

    notified = {}
    
    def randvox():
        return (np.random.randint(0, img.shape[0]),
                np.random.randint(0, img.shape[1]),
                np.random.randint(0, img.shape[2]))

    def onData(*a):
        notified['data'] = True

    def onSaveState(*a):
        notified['save'] = True

    def onDataRange(*a):
        notified['dataRange'] = True

    img.register('name1', onData,      'data')
    img.register('name2', onSaveState, 'saveState')
    img.register('name3', onDataRange, 'dataRange')

    # Calculate the actual data range
    data   = img.nibImage.get_data()
    dmin   = data.min()
    dmax   = data.max()
    drange = dmax - dmin

    try:

        assert img.saveState
        assert np.all(np.isclose(img.dataRange, (dmin, dmax)))

        randval    = dmin + np.random.random() * drange
        rx, ry, rz = randvox()

        img[rx, ry, rz] = randval

        assert np.isclose(img[rx, ry, rz], randval)
        assert notified.get('data', False)
        assert notified.get('save', False)
        assert not img.saveState

        notified.pop('data')

        newdmin = dmin - 100
        newdmax = dmax + 100

        rx, ry, rz = randvox()
        img[rx, ry, rz] = newdmin

        assert notified.get('data',      False)
        assert notified.get('dataRange', False)
        assert np.isclose(img[rx, ry, rz], newdmin)
        assert np.all(np.isclose(img.dataRange, (newdmin, dmax)))

        notified.pop('data')
        notified.pop('dataRange')

        rx, ry, rz = randvox()
        img[rx, ry, rz] = newdmax

        assert notified.get('data',      False)
        assert notified.get('dataRange', False)
        assert np.isclose(img[rx, ry, rz], newdmax)
        assert np.all(np.isclose(img.dataRange, (newdmin, newdmax)))

    finally:
        shutil.rmtree(testdir)


def  test_Image_2D_analyze(): _test_Image_2D(0)
def  test_Image_2D_nifti1():  _test_Image_2D(1)
def  test_Image_2D_nifti2():  _test_Image_2D(2)
def _test_Image_2D(imgtype):

    testdir = tempfile.mkdtemp()

    # The first shape tests when the
    # nifti dim0 field is set to 2,
    # which happens when you create
    # an XY slice with fslroi. This
    # should still be read in as a
    # 3D image. 
    testdims = [(10, 20),
                (10, 20, 1),
                (10, 1,  20),
                (1,  10, 20),
                (10, 20, 1,  5),
                (10, 1,  20, 5),
                (1,  10, 20, 5)]

    try:

        for shape in testdims:

            pixdim = [2] * len(shape)
                
            imagefile = op.join(testdir, 'image')
            
            make_image(imagefile, imgtype, shape, pixdim)

            image = fslimage.Image(imagefile)

            # 2D should appear as 3D
            if len(shape) == 2:
                shape  = list(shape)  + [1]
                pixdim = list(pixdim) + [1]

            assert len(shape)  == len(image   .shape)
            assert len(shape)  == len(image[:].shape)
            assert len(pixdim) == len(image   .pixdim)

            assert tuple(map(float, shape))  == tuple(map(float, image   .shape))
            assert tuple(map(float, shape))  == tuple(map(float, image[:].shape))
            assert tuple(map(float, pixdim)) == tuple(map(float, image   .pixdim))

    finally:
        shutil.rmtree(testdir)
