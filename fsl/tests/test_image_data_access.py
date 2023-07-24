#!/usr/bin/env python
#
# Test/verify data access semantics through Image.__getitem__ and
# Image.__setitem__
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import                   pytest
import numpy          as np
import nibabel        as nib
import fsl.data.image as fslimage

from fsl.utils.tempdir import tempdir


def random_shape():
    shape = []
    ndims = np.random.randint(1, 6)
    maxes = [100, 100, 100, 5, 5]
    for dmax in maxes[:ndims]:
        shape.append(np.random.randint(1, dmax + 1))
    return shape


def random_data_from_slice(shape, slc, dtype=None):
    data = (np.random.random(shape) * 50)[slc]
    if dtype is not None: return data.astype(dtype)
    else:                 return data


def random_slice(shape):
    slc = []
    for sz in shape:
        if sz == 1:
            lo, hi = 0, 1
        else:
            lo = np.random.randint(0,  sz - 1)
            hi = np.random.randint(lo + 1, sz)

        slc.append(slice(lo, hi))
    return tuple(slc)


def create_image(filename, shape, **kwargs):
    data = np.random.random(shape)
    nib.Nifti1Image(data, header=None, affine=np.eye(4))\
       .to_filename(filename)
    return fslimage.Image(filename, **kwargs), data


# Read only data access should defer entirely
# to nibabel, which should keep the image
# data on disk via either indexed_gzip (for
# .nii.gz), or memmap (for .nii)
def test_image_readonly_compressed():
    _test_image_readonly('.nii.gz')

def test_image_readonly_uncompressed():
    _test_image_readonly('.nii')

# suffix in ('.nii', '.nii.gz')
def _test_image_readonly(suffix):

    filename = f'image{suffix}'
    shape    = random_shape()

    with tempdir():
        img, data = create_image(filename, shape)

        for _ in range(50):
            slc    = random_slice(shape)
            sample = img[slc]

            assert np.all(sample == data[slc].reshape(sample.shape))

        assert not img.nibImage.in_memory


# When image data is written, this causes the
# image data to be loaded into memory, with a
# reference/ cache maintained by the Image
# class. If access is entriely through the
# Image class, the nibabel image should never
# use its own cache. Whether the data is
# compressed/uncompressed is irrelevant.
def test_image_read_write_compressed():
    _test_image_read_write('.nii.gz')

def test_image_read_write_uncompressed():
    _test_image_read_write('.nii')

def _test_image_read_write(suffix):

    filename = f'image{suffix}'
    shape    = random_shape()

    with tempdir():
        img, _ = create_image(filename, shape)
        slc    = random_slice(shape)
        data   = random_data_from_slice(shape, slc, img.dtype)

        assert not img.inMemory
        img[slc] = data
        assert img.inMemory
        assert not img.nibImage.in_memory

        assert np.all(np.isclose(img[slc].reshape(data.shape), data))


# Custom data manager - Image class
# does not promise anything
class NoOpDataManager(fslimage.DataManager):
    def __init__(self, shape):
        self.__shape = shape
    def copy(self, nibImage):
        self.__shape = nibImage.shape
        return self
    def __getitem__(self, slc):
        return random_data_from_slice(self.__shape, slc)
    def __setitem__(self, slc, value):
        pass

def test_image_read_write_datamanager():

    filename = 'image.nii.gz'
    shape    = random_shape()

    with tempdir():

        dm     = NoOpDataManager(shape)
        img, _ = create_image(filename, shape, dataMgr=dm)
        slc    = random_slice(shape)

        data     = img[slc]
        img[slc] = data

        # true for this specific DataManager
        assert     img.editable
        assert not img.inMemory
        assert not img.nibImage.in_memory


def test_Image_without_nibabel_object():

    filename = f'image.nii.gz'
    shape    = random_shape()

    with tempdir():
        dm     = NoOpDataManager(shape)
        img, _ = create_image(filename, shape)
        hdr    = img.header

        # We must provide a header and a data manager
        with pytest.raises(ValueError):
            fslimage.Image()
        with pytest.raises(ValueError):
            fslimage.Image(header=hdr)
        with pytest.raises(ValueError):
            fslimage.Image(dataMgr=dm)

        img = fslimage.Image(header=hdr, dataMgr=dm)


def test_3D_indexing(shape=None, img=None):

    # Test that a 3D image looks like a 3D image

    if   shape is None:
        shape = (21, 22, 23)
    elif len(shape) < 3:
        shape = tuple(list(shape) + [1] * (3 - len(shape)))

    if img is None:
        data   = np.random.random(shape)
        nibImg = nib.Nifti1Image(data, np.eye(4))
        img    = fslimage.Image(nibImg)

    assert tuple(img[:]      .shape) == tuple(shape)
    assert tuple(img[:, :]   .shape) == tuple(shape)
    assert tuple(img[:, :, :].shape) == tuple(shape)
    assert tuple(img[:, 0, 0].shape) == (shape[0], )
    assert tuple(img[0, :, 0].shape) == (shape[1], )
    assert tuple(img[0, 0, :].shape) == (shape[2], )
    assert tuple(img[0, :, :].shape) == (shape[1], shape[2])
    assert tuple(img[:, 0, :].shape) == (shape[0], shape[2])
    assert tuple(img[:, :, 0].shape) == (shape[0], shape[1])

    assert type(img[0, 0, 0]) == np.float64

    mask1 = np.zeros(shape, dtype=bool)

    mask1[0, 0, 0] = True
    mask1[1, 0, 0] = True

    assert tuple(img[mask1].shape) == (2, )

    img[0, 0, 0] =  999
    img[:, 0, 0] = [999] * shape[0]
    img[0, :, 0] = [999] * shape[1]
    img[0, 0, :] = [999] * shape[2]
    img[:, 0, 0] = np.array([999] * shape[0])
    img[0, :, 0] = np.array([999] * shape[1])
    img[0, 0, :] = np.array([999] * shape[2])

    img[0, :, :] = np.ones((shape[1], shape[2]))
    img[:, 0, :] = np.ones((shape[0], shape[2]))
    img[:, :, 0] = np.ones((shape[0], shape[1]))

    img[0, :, :] = [[999] * shape[2]] * shape[1]
    img[:, 0, :] = [[999] * shape[2]] * shape[0]
    img[:, :, 0] = [[999] * shape[1]] * shape[0]


def test_3D_4D_indexing():

    # Test indexing with a trailing fourth
    # dimension of length 1 - it should
    # look like a 3D image, but should
    # still accept (valid) 4D slicing.

    # __getitem__ and __setitem__ on
    #   - 3D index
    #   - 4D index
    #   - 3D boolean array
    #   - 4D boolean array
    #
    padShape = (21, 22, 23, 1)
    shape    = padShape[:3]

    data   = np.random.random(shape)
    nibImg = nib.Nifti1Image(data, np.eye(4))
    img    = fslimage.Image(nibImg)

    test_3D_indexing(shape, img)

    assert tuple(img[:, :, :, :].shape) == tuple(shape)

    assert tuple(img[:, 0, 0, 0].shape) == (shape[0], )
    assert tuple(img[:, 0, 0, :].shape) == (shape[0], )

    assert tuple(img[:, :, 0, 0].shape) == (shape[0], shape[1])
    assert tuple(img[:, :, 0, :].shape) == (shape[0], shape[1])

    assert type(img[0, 0, 0, 0]) == np.float64
    assert type(img[0, 0, 0, :]) == np.float64

    mask = np.zeros(padShape, dtype=bool)
    mask[0, 0, 0, 0] = True

    assert type(img[mask])      == np.ndarray
    assert      img[mask].shape == (1, )


def test_3D_len_one_indexing(shape=None, img=None):

    # Testing a 3D image with a third
    # dimension of length 1 - it should
    # look like a 3D image, but should
    # still accept (valid) 2D slicing.

    if shape is None:
        shape = (20, 20, 1)
    elif len(shape) < 3:
        shape = tuple(list(shape) + [1] * (3 - len(shape)))

    if img is None:
        data   = np.random.random(shape)
        nibImg = nib.Nifti1Image(data, np.eye(4))
        img    = fslimage.Image(nibImg)

    test_3D_indexing(shape, img)

    assert type(img[0, 0, :]) == np.ndarray
    assert type(img[0, 0])    == np.ndarray
    assert type(img[0, 0, 0]) == np.float64

    mask = np.zeros(shape[:2], dtype=bool)
    mask[0, 0] = True

    assert type(img[mask])      == np.ndarray
    assert      img[mask].shape == (1, )

    mask = np.zeros(shape, dtype=bool)
    mask[0, 0, 0] = True

    assert type(img[mask])      == np.ndarray
    assert      img[mask].shape == (1, )


def test_2D_indexing():

    # Testing a 2D image - it should
    # look just like a 3D image (the
    # same as is tested above).

    shape  = (20, 20)
    data   = np.random.random(shape[:2])
    nibImg = nib.Nifti1Image(data, np.eye(4))
    img    = fslimage.Image(nibImg)

    test_3D_len_one_indexing(shape, img)


def test_1D_indexing():

    # Testing a 1D image - it should
    # look just like a 3D image (the
    # same as is tested above).

    shape  = (20,)
    data   = np.random.random(shape)
    nibImg = nib.Nifti1Image(data, np.eye(4))
    img    = fslimage.Image(nibImg)

    test_3D_len_one_indexing(shape, img)


def test_4D_indexing(shape=None, img=None):

    if shape is None:
        shape = (20, 21, 22, 23)

    if img is None:

        data   = np.random.random(shape)
        nibImg = nib.Nifti1Image(data, affine=np.eye(4))
        img    = fslimage.Image(nibImg)

    assert tuple(img[:]         .shape) == tuple(shape)
    assert tuple(img[:, :]      .shape) == tuple(shape)
    assert tuple(img[:, :, :]   .shape) == tuple(shape)
    assert tuple(img[:, :, :, :].shape) == tuple(shape)

    assert tuple(img[:, 0, 0, 0].shape) == (shape[0], )
    assert tuple(img[0, :, 0, 0].shape) == (shape[1], )
    assert tuple(img[0, 0, :, 0].shape) == (shape[2], )
    assert tuple(img[0, 0, 0, :].shape) == (shape[3], )


    assert tuple(img[0, :, :, :].shape) == (shape[1], shape[2], shape[3])
    assert tuple(img[:, 0, :, :].shape) == (shape[0], shape[2], shape[3])
    assert tuple(img[:, :, 0, :].shape) == (shape[0], shape[1], shape[3])
    assert tuple(img[:, :, :, 0].shape) == (shape[0], shape[1], shape[2])

    assert type(img[0, 0, 0, 0]) == np.float64

    mask1 = np.zeros(shape, dtype=bool)

    mask1[0, 0, 0, 0] = True
    mask1[1, 0, 0, 0] = True

    assert tuple(img[mask1].shape) == (2, )

    img[0, 0, 0, 0] =  999

    img[:, 0, 0, 0] = [999] * shape[0]
    img[0, :, 0, 0] = [999] * shape[1]
    img[0, 0, :, 0] = [999] * shape[2]
    img[0, 0, 0, :] = [999] * shape[3]

    img[:, 0, 0, 0] = np.array([999] * shape[0])
    img[0, :, 0, 0] = np.array([999] * shape[1])
    img[0, 0, :, 0] = np.array([999] * shape[2])
    img[0, 0, 0, :] = np.array([999] * shape[3])


    img[0, :, :, :] = np.ones((shape[1], shape[2], shape[3]))
    img[:, 0, :, :] = np.ones((shape[0], shape[2], shape[3]))
    img[:, :, 0, :] = np.ones((shape[0], shape[1], shape[3]))
    img[:, :, :, 0] = np.ones((shape[0], shape[1], shape[2]))

    img[0, :, :, :] = [[[999] * shape[3]] * shape[2]] * shape[1]
    img[:, 0, :, :] = [[[999] * shape[3]] * shape[2]] * shape[0]
    img[:, :, 0, :] = [[[999] * shape[3]] * shape[1]] * shape[0]
    img[:, :, :, 0] = [[[999] * shape[2]] * shape[1]] * shape[0]


def test_expectedShape():

    tests = [
        ((slice(None), ), (10,),
         (1, (10, ))),

        ((slice(None), slice(None)),
         (10, 10), (2, (10, 10))),

        ((slice(None), slice(None), slice(None)),
         (10, 10, 10), (3, (10, 10, 10))),

        ((slice(None), slice(None), slice(None)),
         (10, 10, 10), (3, (10, 10, 10))),

        ((slice(None), slice(None), slice(None), slice(None)),
         (10, 10, 10, 10), (4, (10, 10, 10, 10))),

        ((1, slice(None), slice(None)),
         (10, 10, 10), (2, (10, 10))),

        ((slice(1, 3), slice(None), slice(None)),
         (10, 10, 10), (3, (2, 10, 10))),

        ((slice(None), 1, slice(None)),
         (10, 10, 10), (2, (10, 10))),

        ((slice(None), slice(1, 3), slice(None)),
         (10, 10, 10), (3, (10, 2, 10))),

        ((slice(None), slice(None), 1),
         (10, 10, 10), (2, (10, 10))),

        ((slice(None), slice(None), slice(1, 3), ),
         (10, 10, 10), (3, (10, 10, 2))),

        ((slice(None), slice(None), slice(1, 20), ),
         (10, 10, 10), (3, (10, 10, 9))),
    ]

    for slc, shape, exp in tests:

        explen, exp = exp
        gotlen, got = fslimage.expectedShape(slc, shape)

        assert explen     == gotlen
        assert tuple(exp) == tuple(got)
