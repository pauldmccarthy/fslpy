#!/usr/bin/env python
#
# Test/verify data access semantics through Image.__getitem__ and
# Image.__setitem__
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


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

    filename = f'image.nii.gz'
    shape    = random_shape()

    with tempdir():

        dm     = NoOpDataManager(shape)
        img, _ = create_image(filename, shape, dataMgr=dm)
        slc    = random_slice(shape)

        data     = img[slc]
        img[slc] = data

        # true for this specific DataManager
        assert not img.inMemory
        assert not img.nibImage.in_memory
