#!/usr/bin/env python
#
# test_image_advanced.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op
import            time

import mock
import pytest

import numpy   as np
import nibabel as nib

import tests
import fsl.data.image as fslimage


from . import make_random_image


# make sure Image(indexed=True) works
# even if indexed_gzip is not present
@pytest.mark.longtest
def test_image_indexed_no_igzip_threaded():
    with mock.patch.dict('sys.modules', indexed_gzip=None):
        _test_image_indexed(True)

@pytest.mark.longtest
def test_image_indexed_no_igzip_unthreaded():
    with mock.patch.dict('sys.modules', indexed_gzip=None):
        _test_image_indexed(False)


@pytest.mark.longtest
@pytest.mark.igziptest
def test_image_indexed_threaded(  ): _test_image_indexed(True)
@pytest.mark.longtest
@pytest.mark.igziptest
def test_image_indexed_unthreaded(): _test_image_indexed(False)
def _test_image_indexed(threaded):

    with tests.testdir() as testdir:

        filename = op.join(testdir, 'image.nii.gz')

        # Data range grows with volume
        data  = np.zeros((50, 50, 50, 50))
        for vol in range(data.shape[-1]):
            data[..., vol] = vol

        fslimage.Image(data).save(filename)

        img = fslimage.Image(
            filename,
            loadData=False,
            calcRange=False,
            threaded=threaded)

        # First iteration through the image
        start1 = time.time()
        for vol in range(data.shape[-1]):

            img[..., vol]

            if threaded:
                img.getImageWrapper().getTaskThread().waitUntilIdle()

            assert img.dataRange == (0, vol)
        end1 = time.time()

        # Double check that indexed_gzip is
        # being used (the internal _opener
        # attribute is not created until
        # after the first data access)
        try:
            import indexed_gzip as igzip
            assert isinstance(img.nibImage.dataobj._opener.fobj,
                              igzip.IndexedGzipFile)
        except ImportError:
            pass

        # Second iteration through
        start2 = time.time()
        for vol in range(data.shape[-1]):
            img[..., vol]
        end2 = time.time()

        # Second iteration should be much faster!
        assert (end1 - start1) > (end2 - start2)


@pytest.mark.longtest
@pytest.mark.igziptest
def test_image_indexed_read4D_threaded(seed):
    _test_image_indexed_read4D(True)
@pytest.mark.longtest
@pytest.mark.igziptest
def test_image_indexed_read4D_unthreaded(seed):
    _test_image_indexed_read4D(False)
def _test_image_indexed_read4D(threaded):

    with tests.testdir() as testdir:

        filename = op.join(testdir, 'image.nii.gz')

        # Data range grows with volume
        nvols = 50
        data  = np.zeros((50, 50, 50, nvols))
        for vol in range(nvols):
            data[..., vol] = vol

        fslimage.Image(data).save(filename)

        img = fslimage.Image(
            filename,
            loadData=False,
            calcRange=False,
            threaded=threaded)

        # Test reading slice through
        # 4D (e.g. voxel time course)
        #
        # n.b. This is SUPER SLOW!!
        voxels = tests.random_voxels((50, 50, 50), 5)
        for i, xyz in enumerate(voxels):

            x, y, z = [int(v) for v in xyz]
            data    = img[x, y, z, :]

            if threaded:
                img.getImageWrapper().getTaskThread().waitUntilIdle()

            assert np.all(data == np.arange(nvols))

        # double check we're indexing as expected
        try:
            import indexed_gzip as igzip
            assert isinstance(img.nibImage.dataobj._opener.fobj,
                              igzip.IndexedGzipFile)
        except ImportError:
            pass


@pytest.mark.igziptest
@pytest.mark.longtest
def test_image_indexed_save_threaded(  ): _test_image_indexed_save(True)
@pytest.mark.longtest
@pytest.mark.igziptest
def test_image_indexed_save_unthreaded(): _test_image_indexed_save(False)
def _test_image_indexed_save(threaded):

    with tests.testdir() as testdir:

        filename = op.join(testdir, 'image.nii.gz')

        # Data range grows with volume
        data = np.zeros((100, 100, 100, 50))
        for vol in range(data.shape[-1]):
            data[..., vol] = vol

        fslimage.Image(data).save(filename)

        img = fslimage.Image(
            filename,
            loadData=False,
            calcRange=False,
            threaded=threaded)

        # access some data
        img[..., 0]
        img[..., 40]

        # double check that igzip is being used
        try:
            import indexed_gzip as igzip
            assert isinstance(img.nibImage.dataobj._opener.fobj,
                              igzip.IndexedGzipFile)
        except ImportError:
            pass

        if threaded:
            img.getImageWrapper().getTaskThread().waitUntilIdle()

        # make sure the data range is correct
        assert img.dataRange == (0, 40)

        # change some data
        data = np.zeros((100, 100, 100))
        data[:] = 45
        img[..., 40] = data

        if threaded:
            img.getImageWrapper().getTaskThread().waitUntilIdle()

        # save the image
        img.save()

        assert img.dataRange == (0, 45)

        # access the data  - index should
        # get rebuilt to this point
        img[..., 0]
        img[..., 40]

        if threaded:
            img.getImageWrapper().getTaskThread().waitUntilIdle()

        # make sure we got the modified data
        assert img.dataRange == (0, 45)

        img[..., 49]

        if threaded:
            img.getImageWrapper().getTaskThread().waitUntilIdle()

        # make sure we got the modified data
        assert img.dataRange == (0, 49)


        # Finally, reload, and verify the change
        img = fslimage.Image(filename)

        assert np.all(img[..., 40] == 45)


@pytest.mark.longtest
def test_image_no_calcRange_threaded():   _test_image_no_calcRange(True)
@pytest.mark.longtest
def test_image_no_calcRange_unthreaded(): _test_image_no_calcRange(False)
def _test_image_no_calcRange(threaded):

    # Data range grows with volume
    data = np.zeros((100, 100, 100, 50))
    for vol in range(data.shape[-1]):
        data[..., vol] = vol

    img = nib.nifti1.Nifti1Image(data, np.eye(4))
    img.header['cal_min'] = 95
    img.header['cal_max'] = 643

    img = fslimage.Image(img,
                         loadData=False,
                         calcRange=False,
                         threaded=threaded)

    # dataRange should fallback to
    # cal_min/max if it is unknown
    assert img.dataRange == (95, 643)

    for i in [0, 7, 40]:
        img[..., i]
        if threaded:
            img.getImageWrapper().getTaskThread().waitUntilIdle()

        assert img.dataRange == (0, i)


@pytest.mark.longtest
def test_image_calcRange_threaded():   _test_image_calcRange(True)
@pytest.mark.longtest
def test_image_calcRange_unthreaded(): _test_image_calcRange(False)
def _test_image_calcRange(threaded):

    # Testing with a 3D image
    data = np.zeros((10, 10, 10))
    for slc in range(10):
        data[..., slc] = slc + 1
    data[0, 0, 0] = 0

    kwargs = { 'calcRange' : False,
               'loadData'  : False,
               'threaded'  : threaded}

    # Check that calcRange(None) will calculate the full range
    img = fslimage.Image(data, **kwargs)
    img.calcRange()
    if threaded:
        img.getImageWrapper().getTaskThread().waitUntilIdle()
    assert img.dataRange == (0, 10)

    # Check that calcRange(numBiggerThanImage)
    # will calculate the full range
    img = fslimage.Image(data, **kwargs)
    img.calcRange(np.prod(img.shape) * img.dtype.itemsize + 1)
    if threaded:
        img.getImageWrapper().getTaskThread().waitUntilIdle()
    assert img.dataRange == (0, 10)

    # Check that calcRange(smallnum) will
    # calculate the range of the first slice
    img = fslimage.Image(data, **kwargs)
    img.calcRange(100)
    if threaded:
        img.getImageWrapper().getTaskThread().waitUntilIdle()
    assert img.dataRange == (0, 1)

    #########################
    # Testing with a 4D image
    data = np.zeros((10, 10, 10, 10))
    for slc in range(10):
        data[..., slc] = slc + 1
    data[0, 0, 0, 0] = 0

    # Check that calcRange(None) will calculate the full range
    img = fslimage.Image(data, **kwargs)
    img.calcRange()
    if threaded:
        img.getImageWrapper().getTaskThread().waitUntilIdle()
    assert img.dataRange == (0, 10)

    # Check that calcRange(numBiggerThanImage)
    # will calculate the full range
    img = fslimage.Image(data, **kwargs)
    img.calcRange(np.prod(img.shape) * img.dtype.itemsize + 1)
    if threaded:
        img.getImageWrapper().getTaskThread().waitUntilIdle()
    assert img.dataRange == (0, 10)

    # Check that calcRange(smallnum) will
    # calculate the range of the first volume
    img = fslimage.Image(data, **kwargs)
    img.calcRange(100)
    if threaded:
        img.getImageWrapper().getTaskThread().waitUntilIdle()
    assert img.dataRange == (0, 1)
