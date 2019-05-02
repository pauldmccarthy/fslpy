#!/usr/bin/env python


import itertools as it
import os.path   as op
import numpy     as np

import pytest

import fsl.data.image           as     fslimage
import fsl.utils.transform      as     transform
import fsl.utils.image.resample as     resample
from   fsl.utils.tempdir        import tempdir


from . import make_random_image


def test_resample(seed):

    with tempdir() as td:

        fname = op.join(td, 'test.nii')

        # Random base image shapes
        for i in range(25):

            shape = np.random.randint(5, 50, 3)
            make_random_image(fname, shape)
            img = fslimage.Image(fname, mmap=False)

            # bad shape
            with pytest.raises(ValueError):
                resample.resample(img, (10, 10))
            with pytest.raises(ValueError):
                resample.resample(img, (10, 10, 10, 10))

            # resampling to the same shape should be a no-op
            samei, samex = resample.resample(img, shape)
            assert np.all(samei == img[:])
            assert np.all(samex == img.voxToWorldMat)

            # Random resampled image shapes
            for j in range(10):

                rshape        = np.random.randint(5, 50, 3)
                resampled, xf = resample.resample(img, rshape, order=0)

                img.save('base.nii.gz')
                fslimage.Image(resampled, xform=xf,
                               mmap=False).save('res.nii.gz')

                assert tuple(resampled.shape) == tuple(rshape)

                # We used nearest neighbour interp, so the
                # values in the resampled image should match
                # corresponding values in the original. Let's
                # check some whynot.
                restestcoords = np.array([
                    np.random.randint(0, rshape[0], 100),
                    np.random.randint(0, rshape[1], 100),
                    np.random.randint(0, rshape[2], 100)]).T

                resx,  resy,  resz  = restestcoords.T
                resvals  = resampled[resx, resy, resz]

                res2orig = transform.concat(img.worldToVoxMat, xf)

                origtestcoords = transform.transform(restestcoords, res2orig)

                # remove any coordinates which are out of
                # bounds in the original image space, or
                # are right on a voxel boundary (where the
                # nn interp could have gone either way), or
                # have value == 0 in the resampled space.
                out = ((origtestcoords < 0)            |
                       (origtestcoords >= shape - 0.5) |
                       (np.isclose(np.modf(origtestcoords)[0], 0.5)))
                out = np.any(out, axis=1) | (resvals == 0)

                origtestcoords = np.array(origtestcoords.round(), dtype=np.int)

                origtestcoords = origtestcoords[~out, :]
                restestcoords  = restestcoords[ ~out, :]

                resx,  resy,  resz  = restestcoords.T
                origx, origy, origz = origtestcoords.T

                origvals = img[:][origx, origy, origz]
                resvals  = resampled[resx, resy, resz]

                assert np.all(np.isclose(resvals, origvals))

        del img
        img = None


def test_resample_4d(seed):

    fname = 'test.nii.gz'

    with tempdir():

        make_random_image(fname, (10, 10, 10, 10))

        # resample one volume
        img = fslimage.Image(fname)
        slc = (slice(None), slice(None), slice(None), 3)
        resampled = resample.resample(img, img.shape[:3], slc)[0]
        assert np.all(resampled == img[..., 3])

        # resample up
        resampled = resample.resample(img, (15, 15, 15), slc)[0]
        assert tuple(resampled.shape) == (15, 15, 15)

        # resample down
        resampled = resample.resample(img, (5, 5, 5), slc)[0]
        assert tuple(resampled.shape) == (5, 5, 5)

        # resample the entire image
        resampled = resample.resample(img, (15, 15, 15, 10), None)[0]
        assert tuple(resampled.shape) == (15, 15, 15, 10)

        resampled = resample.resample(img, (5, 5, 5, 10), None)[0]
        assert tuple(resampled.shape) == (5, 5, 5, 10)

        # resample along the fourth dim
        resampled = resample.resample(img, (15, 15, 15, 15), None)[0]
        assert tuple(resampled.shape) == (15, 15, 15, 15)

        resampled = resample.resample(img, (5, 5, 5, 15), None)[0]
        assert tuple(resampled.shape) == (5, 5, 5, 15)

        del img
        del resampled
        img = None
        resampled = None


def test_resample_origin(seed):
    with tempdir() as td:
        fname = op.join(td, 'test.nii')

        make_random_image(fname, (10, 10, 10))
        img = fslimage.Image(fname)

        # with origin='corner', image
        # bounding boxes should match
        for i in range(25):
            shape = np.random.randint(5, 50, 3)
            res = resample.resample(img, shape, origin='corner')
            res = fslimage.Image(res[0], xform=res[1])
            imgb = transform.axisBounds(img.shape, img.voxToWorldMat)
            resb = transform.axisBounds(res.shape, res.voxToWorldMat)
            assert np.all(np.isclose(imgb, resb, rtol=1e-5, atol=1e-5))

        # with origin='centre' image
        # bounding boxes should be offset
        # by (size_resampled - size_orig) / 2
        for i in range(25):
            shape = np.random.randint(5, 50, 3)
            res = resample.resample(img, shape, origin='centre')
            res = fslimage.Image(res[0], xform=res[1])
            off = (np.array(img.shape) / np.array(res.shape) - 1) / 2
            imgb = np.array(transform.axisBounds(img.shape, img.voxToWorldMat))
            resb = np.array(transform.axisBounds(res.shape, res.voxToWorldMat))
            assert np.all(np.isclose(imgb, resb + off, rtol=1e-5, atol=1e-5))

        # with origin='corner', using
        # linear interp, when we down-
        # sample an image to a shape
        # that divides evenly into the
        # original shape, a downsampled
        # voxel should equal the average
        # of the original voxels inside
        # it.
        res = resample.resample(img, (5, 5, 5), smooth=False, origin='corner')[0]
        for x, y, z in it.product(range(5), range(5), range(5)):
            block = img[x * 2: x * 2 + 2,
                        y * 2: y * 2 + 2,
                        z * 2: z * 2 + 2]
            assert np.isclose(res[x, y, z], block.mean())


def test_resampleToPixdims():
    pass


def test_resampleToReference():
    pass
