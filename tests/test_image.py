#!/usr/bin/env python
#
# test_image.py - Unit tests for the fsl.data.image module.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Unit tests for the fsl.data.image module. """


import              os
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


def make_image(filename=None,
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

    if filename is not None:

        if op.splitext(filename)[1] == '':
            if imgtype == 0: filename = '{}.img'.format(filename)
            else:            filename = '{}.nii'.format(filename)

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


def test_create():

    # Test creating:
    #  from a numpy array
    #  from a numpy array + xform
    #  from a numpy array + nibabel header
    #  from a numpy array + nibabel header + xform
    #  from a file
    #  from a nibabel image

    data  = np.random.random((10, 10, 10))
    xform = np.diag([2, 3, 4, 1])

    img = fslimage.Image(data)
    assert np.all(np.isclose(img.pixdim, (1, 1, 1)))
    assert np.all(np.isclose(img.voxToWorldMat, np.eye(4)))
    assert img.niftiVersion == 1

    img = fslimage.Image(data, xform=xform)
    assert np.all(np.isclose(img.pixdim, (2, 3, 4)))
    assert np.all(np.isclose(img.voxToWorldMat, xform))
    assert img.niftiVersion == 1

    for imgType in [0, 1, 2]:

        nimg = make_image(imgtype=imgType, pixdims=(5, 6, 7))
        nhdr = nimg.header

        img = fslimage.Image(data, header=nhdr)
        assert img.niftiVersion == imgType
        assert np.all(np.isclose(img.pixdim, (5, 6, 7)))

        img = fslimage.Image(data, header=nhdr, xform=xform)
        assert img.niftiVersion == imgType
        assert np.all(np.isclose(img.pixdim, (2, 3, 4)))

    for imgtype in [0, 1, 2]:
        testdir = tempfile.mkdtemp()
        try:
            fname = op.join(testdir, 'myimage')
            nimg  = make_image(fname, imgtype, pixdims=(2, 3, 4))

            img = fslimage.Image(fname)
            assert img.niftiVersion == imgtype
            assert np.all(np.isclose(img.pixdim, (2, 3, 4)))

            img = fslimage.Image(nimg)
            assert img.niftiVersion == imgtype
            assert np.all(np.isclose(img.pixdim, (2, 3, 4)))

        finally:
            shutil.rmtree(testdir)


def test_bad_create():

    class BadThing(object):
        pass

    # Bad header object
    with pytest.raises(Exception):
        fslimage.Image(
            np.random.random((10, 10, 10)),
            header=BadThing())

    # Bad data
    with pytest.raises(Exception):
        fslimage.Image(BadThing())

    # Bad data
    with pytest.raises(Exception):
        fslimage.Image(np.random.random(10, 10, 10, 10, 10))

    # Bad xform
    with pytest.raises(Exception):
        fslimage.Image(np.random.random(10, 10, 10),
                       xform=BadThing())
    # Bad xform
    with pytest.raises(Exception):
        fslimage.Image(np.random.random(10, 10, 10),
                       xform=np.eye(3))

    with pytest.raises(Exception):
        fslimage.Image(np.random.random(10, 10, 10),
                       xform=np.eye(5))


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

    tests = it.product(dims, pixdims, dtypes)
    tests = list(tests)
    paths = ['test{:03d}'.format(i) for i in range(len(tests))]

    for path, atts in zip(paths, tests):

        dims, pixdims, dtype = atts

        ndims   = len(dims)
        pixdims = pixdims[:ndims]

        path = op.abspath(op.join(testdir, path))
        make_image(path, imgtype, dims, pixdims, dtype)

    try:

        for path, atts in zip(paths, tests):

            dims, pixdims, dtype = atts

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

def  test_Image_atts2_analyze(): _test_Image_atts2(0)
def  test_Image_atts2_nifti1():  _test_Image_atts2(1)
def  test_Image_atts2_nifti2():  _test_Image_atts2(2)
def _test_Image_atts2(imgtype):

    # See fsl.utils.constants for the meanings of these codes
    xyzUnits  = [0, 1, 2, 3]
    timeUnits = [8, 16, 24, 32, 40, 48]
    intents   = [0, 2, 1007, 2005, 2006, 2016]

    for xyzu, timeu, intent in it.product(xyzUnits, timeUnits, intents):

        nimg = make_image(imgtype=imgtype)

        # Analyze images do not have units or intent
        if imgtype != 0:
            nimg.header.set_xyzt_units(xyzu, timeu)
            nimg.header['intent_code'] = intent
            nimg.update_header()

        img = fslimage.Image(nimg)

        if imgtype == 0:
            assert img.xyzUnits  == constants.NIFTI_UNITS_MM
            assert img.timeUnits == constants.NIFTI_UNITS_SEC
            assert img.intent    == constants.NIFTI_INTENT_NONE
        else:
            assert img.xyzUnits  == xyzu
            assert img.timeUnits == timeu
            assert img.intent    == intent


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


def test_removeExt():

    exts = ['.nii.gz', '.nii', '.img', '.img.gz', '.hdr', '.hdr.gz']

    for e in exts:
        prefix = 'blob'
        fname  = '{}{}'.format(prefix, e)

        assert fslimage.removeExt(fname) == prefix


def test_getExt():

    exts = ['.nii.gz', '.nii', '.img', '.img.gz', '.hdr', '.hdr.gz']

    for e in exts:
        prefix = 'blob'
        fname  = '{}{}'.format(prefix, e)

        assert fslimage.getExt(fname) == e


def test_splitExt():

    exts = ['.nii.gz', '.nii', '.img', '.img.gz', '.hdr', '.hdr.gz']

    for e in exts:
        prefix = 'blob'
        fname  = '{}{}'.format(prefix, e)

        assert fslimage.splitExt(fname) == (prefix, e)


def test_defaultExt():

    fslOutputTypes = ['NIFTI', 'NIFTI_PAIR', 'NIFTI_GZ']
    exts           = ['.nii', '.img', '.nii.gz']

    os.environ.pop('FSLOUTPUTTYPE', None)
    assert fslimage.defaultExt() == '.nii.gz'

    for o, e in zip(fslOutputTypes, exts):

        os.environ['FSLOUTPUTTYPE'] = o

        assert fslimage.defaultExt() == e


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
def  test_Image_sqforms_nifti2_nosqform(): _test_Image_sqforms(2, 0, 0)
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
        expOrient    = constants.ORIENT_UNKNOWN

    # No sform, but valid qform - expect the affine
    elif sformcode == 0 and qformcode > 0:
        expAffine    = affine
        invExpAffine = invAffine
        expCode      = qformcode
        expOrient    = constants.ORIENT_L2R

    # Valid sform (qform irrelevant) - expect the affine
    elif sformcode > 0:
        expAffine    = affine
        invExpAffine = invAffine
        expCode      = sformcode
        expOrient    = constants.ORIENT_L2R

    image = fslimage.Image(imagefile)

    with pytest.raises(ValueError):
        image.getXFormCode('badcode')

    try:
        assert np.all(np.isclose(image.voxToWorldMat,  expAffine))
        assert np.all(np.isclose(image.worldToVoxMat,  invExpAffine))

        assert image.getXFormCode()        == expCode
        assert image.getXFormCode('sform') == sformcode
        assert image.getXFormCode('qform') == qformcode

        assert image.getOrientation(0, image.voxToWorldMat) == expOrient
    finally:
        shutil.rmtree(testdir)


def  test_Image_changeXform_analyze():         _test_Image_changeXform(0)
def  test_Image_changeXform_nifti1():          _test_Image_changeXform(1)
def  test_Image_changeXform_nifti1_nosqform(): _test_Image_changeXform(1, 0, 0)
def  test_Image_changeXform_nifti2():          _test_Image_changeXform(2)
def _test_Image_changeXform(imgtype, sformcode=None, qformcode=None):
    """Test changing the Nifti.voxToWorldMat attribute. """

    testdir   = tempfile.mkdtemp()
    imagefile = op.join(testdir, 'image')

    image = make_image(imagefile, imgtype)

    if imgtype > 0:

        if sformcode is not None: image.set_sform(image.affine, sformcode)
        if qformcode is not None: image.set_qform(image.affine, qformcode)
        image.update_header()
        nib.save(image, imagefile)

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

    if imgtype > 0:
        expSformCode = image.get_sform(coded=True)[1]
        expQformCode = image.get_qform(coded=True)[1]

        if sformcode == 0:
            expSformCode = constants.NIFTI_XFORM_ALIGNED_ANAT
    else:
        expSformCode = constants.NIFTI_XFORM_ANALYZE
        expQformCode = constants.NIFTI_XFORM_ANALYZE

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
        assert img.getXFormCode('sform') == expSformCode
        assert img.getXFormCode('qform') == expQformCode
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


def test_Image_voxelsToScaledVoxels():

    imgTypes = [0, 1, 2]
    dims     = [(10, 10, 10)]
    pixdims  = [(-1, 1, 1),
                ( 1, 1, 1),
                (-2, 2, 2),
                ( 2, 2, 2),
                (-3, 4, 5),
                ( 3, 4, 5)]

    def expect(itype, dims, pixdims):
        xf = np.eye(4)
        xf[0, 0] = abs(pixdims[0])
        xf[1, 1] =     pixdims[1]
        xf[2, 2] =     pixdims[2]

        if itype > 0 and pixdims[0] > 0:
            xf[0, 0] = -pixdims[0]
            xf[0, 3] =  pixdims[0] * (dims[0] - 1)

        return xf

    for imgType, dim, pixdim in it.product(imgTypes, dims, pixdims):
        nimg = make_image(imgtype=imgType, dims=dim, pixdims=pixdim)
        img  = fslimage.Image(nimg)

        expected = expect(imgType, dim, pixdim)
        result   = img.voxelsToScaledVoxels()

        assert np.all(np.isclose(result, expected))


def test_Image_sameSpace():

    imgTypes = [0, 1, 2]
    dims     = [(10, 10),
                (10, 10, 10),
                (10, 10, 10, 10)]
    pixdims = [(2, 2, 2, 1),
               (2, 3, 4, 1)]

    for (imgType,
         dim1,
         dim2,
         pixdim1,
         pixdim2) in it.product(imgTypes, dims, dims, pixdims, pixdims):

        expected = dim1[:3] == dim2[:3] and pixdim1[:3] == pixdim2[:3]

        img1 = fslimage.Image(make_image(imgtype=imgType, dims=dim1, pixdims=pixdim1))
        img2 = fslimage.Image(make_image(imgtype=imgType, dims=dim2, pixdims=pixdim2))

        assert img1.sameSpace(img2) == expected
        assert img2.sameSpace(img1) == expected

def  test_Image_save_analyze(seed): _test_Image_save(0)
def  test_Image_save_nifti1( seed): _test_Image_save(1)
def  test_Image_save_nifti2( seed): _test_Image_save(2)
def _test_Image_save(imgtype):

    def randvox():
        return (np.random.randint(0, 10),
                np.random.randint(0, 10),
                np.random.randint(0, 10))

    def randvoxes(num):
        rvoxes = []

        while len(rvoxes) < num:
            rvox = randvox()
            if rvox not in rvoxes:
                rvoxes.append(rvox)
        return rvoxes


    testdir   = tempfile.mkdtemp()
    if imgtype == 0:
        filename  = op.join(testdir, 'blob.img')
        filename2 = op.join(testdir, 'blob_copy.img')
    else:
        filename  = op.join(testdir, 'blob.nii')
        filename2 = op.join(testdir, 'blob_copy.nii')

    xform = np.eye(4)
    xform[:3, 3] = [-10, 20, 30]
    xform[ 0, 0] = 33
    xform[ 1, 1] = 55
    xform[ 2, 2] = 38

    try:
        make_image(filename, imgtype)

        # Using mmap can cause a "Bus error"
        # under docker. No idea why.
        img = fslimage.Image(filename, mmap=False)

        randvoxes = randvoxes(5)
        randvals  = [np.random.random() for i in range(5)]

        for (x, y, z), v in zip(randvoxes, randvals):
            img[x, y, z] = v

        if imgtype > 0:
            img.voxToWorldMat = xform

        # Save to original location, and
        # to a different location
        targets = [None, filename, filename2]

        for t in targets:

            img.save(t)

            if t is None: expDataSource = filename
            else:         expDataSource = t

            assert img.saveState
            assert img.dataSource == expDataSource

            if imgtype > 0:
                assert np.all(np.isclose(img.voxToWorldMat, xform))

            for (x, y, z), v in zip(randvoxes, randvals):
                assert np.isclose(img[x, y, z], v)

            # Load the image back in
            img2 = fslimage.Image(img.dataSource)

            assert img.saveState
            assert img.dataSource == expDataSource

            if imgtype > 0:
                assert np.all(np.isclose(img.voxToWorldMat, xform))

            for (x, y, z), v in zip(randvoxes, randvals):
                assert np.isclose(img[x, y, z], v)


    finally:
        shutil.rmtree(testdir)
