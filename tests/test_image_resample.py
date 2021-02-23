#!/usr/bin/env python


import itertools as it
import numpy     as np

import pytest

import scipy.ndimage       as ndimage

import fsl.data.image           as     fslimage
import fsl.transform.affine     as     affine
import fsl.utils.image.resample as     resample

from . import make_random_image

def random_affine():
    return affine.compose(
        0.25   + 4.75      * np.random.random(3),
        -50    + 100       * np.random.random(3),
        -np.pi + 2 * np.pi * np.random.random(3))



def test_resample(seed):

    # Random base image shapes
    for i in range(25):

        shape = np.random.randint(5, 50, 3)
        img = fslimage.Image(make_random_image(dims=shape))

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

            res2orig = affine.concat(img.worldToVoxMat, xf)

            origtestcoords = affine.transform(restestcoords, res2orig)

            # remove any coordinates which are out of
            # bounds in the original image space, or
            # are right on a voxel boundary (where the
            # nn interp could have gone either way), or
            # have value == 0 in the resampled space.
            out = ((origtestcoords < 0)            |
                   (origtestcoords >= shape - 0.5) |
                   (np.isclose(np.modf(origtestcoords)[0], 0.5)))
            out = np.any(out, axis=1) | (resvals == 0)

            origtestcoords = np.array(origtestcoords.round(), dtype=int)

            origtestcoords = origtestcoords[~out, :]
            restestcoords  = restestcoords[ ~out, :]

            resx,  resy,  resz  = restestcoords.T
            origx, origy, origz = origtestcoords.T

            origvals = img[:][origx, origy, origz]
            resvals  = resampled[resx, resy, resz]

            assert np.all(np.isclose(resvals, origvals))


def test_resample_4d(seed):

    # resample one volume
    img = fslimage.Image(make_random_image(dims=(10, 10, 10, 10)))
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


def test_resample_origin(seed):

    img = fslimage.Image(make_random_image(dims=(10, 10, 10)))

    # with origin='corner', image
    # bounding boxes should match
    for i in range(25):
        shape = np.random.randint(5, 50, 3)
        res = resample.resample(img, shape, origin='corner')
        res = fslimage.Image(res[0], xform=res[1])
        imgb = affine.axisBounds(img.shape, img.voxToWorldMat)
        resb = affine.axisBounds(res.shape, res.voxToWorldMat)
        assert np.all(np.isclose(imgb, resb, rtol=1e-5, atol=1e-5))

    # with origin='centre' image
    # bounding boxes should be offset
    # by (size_resampled - size_orig) / 2
    for i in range(25):
        shape = np.random.randint(5, 50, 3)
        res = resample.resample(img, shape, origin='centre')
        res = fslimage.Image(res[0], xform=res[1])
        off = (np.array(img.shape) / np.array(res.shape) - 1) / 2
        imgb = np.array(affine.axisBounds(img.shape, img.voxToWorldMat))
        resb = np.array(affine.axisBounds(res.shape, res.voxToWorldMat))
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

    img          = fslimage.Image(make_random_image(dims=(10, 10, 10)))
    imglo, imghi = affine.axisBounds(img.shape, img.voxToWorldMat)
    oldpix       = np.array(img.pixdim, dtype=float)
    oldshape     = np.array(img.shape,  dtype=float)

    for i, origin in it.product(range(25), ('centre', 'corner')):

        # random pixdims in the range 0.1 - 5.0
        newpix   = 0.1 + 4.9 * np.random.random(3)
        expshape = np.round(oldshape * (oldpix / newpix))

        res = resample.resampleToPixdims(img, newpix, origin=origin)
        res = fslimage.Image(res[0], xform=res[1])
        reslo, reshi = affine.axisBounds(res.shape, res.voxToWorldMat)
        resfov       = reshi - reslo
        expfov       = newpix * res.shape

        assert np.all(np.isclose(res.shape,  expshape))
        assert np.all(np.isclose(res.pixdim, newpix))
        assert np.all(np.isclose(resfov, expfov, rtol=1e-2, atol=1e-2))

        if origin == 'corner':
            assert np.all(np.isclose(imglo, reslo))
            assert np.all(np.isclose(reshi, reslo + expfov,
                                     rtol=1e-2, atol=1e-2))



def test_resampleToReference1():

    # Basic test - output has same
    # dimensions/space as reference
    for i in range(25):

        ishape = np.random.randint(5, 50, 3)
        rshape = np.random.randint(5, 50, 3)
        iv2w   = random_affine()
        rv2w   = random_affine()
        img    = fslimage.Image(make_random_image(dims=ishape, xform=iv2w))
        ref    = fslimage.Image(make_random_image(dims=rshape, xform=rv2w))
        res    = resample.resampleToReference(img, ref)
        res    = fslimage.Image(res[0], header=ref.header)

        assert res.sameSpace(ref)


def test_resampleToReference2():

    # More specific test - output
    # data gets transformed correctly
    # into reference space
    img          = np.zeros((5, 5, 5), dtype=float)
    img[1, 1, 1] = 1
    img          = fslimage.Image(img)

    refv2w = affine.scaleOffsetXform([1, 1, 1], [-1, -1, -1])
    ref    = np.zeros((5, 5, 5), dtype=float)
    ref    = fslimage.Image(ref, xform=refv2w)
    res    = resample.resampleToReference(img, ref, order=0)

    exp          = np.zeros((5, 5, 5), dtype=float)
    exp[2, 2, 2] = 1

    assert np.all(np.isclose(res[0], exp))


def test_resampleToReference3():

    # Test resampling image to ref
    # with mismatched dimensions
    imgdata = np.random.randint(0, 65536, (5, 5, 5))
    img     = fslimage.Image(imgdata, xform=affine.scaleOffsetXform(
        (2, 2, 2), (0.5, 0.5, 0.5)))

    # reference/expected data when
    # resampled to ref (using nn interp).
    # Same as image, upsampled by a
    # factor of 2
    refdata = np.repeat(np.repeat(np.repeat(imgdata, 2, 0), 2, 1), 2, 2)
    refdata = np.array([refdata] * 8).transpose((1, 2, 3, 0))
    ref     = fslimage.Image(refdata)

    # We should be able to use a 4D reference
    resampled, xform = resample.resampleToReference(img, ref, order=0, mode='nearest')
    assert np.all(resampled == ref.data[..., 0])

    # If resampling a 4D image with a 3D reference,
    # the fourth dimension should be passed through
    resampled, xform = resample.resampleToReference(ref, img, order=0, mode='nearest')
    exp = np.array([imgdata] * 8).transpose((1, 2, 3, 0))
    assert np.all(resampled == exp)

    # When resampling 4D to 4D, only the
    # first 3 dimensions should be resampled
    imgdata = np.array([imgdata] * 15).transpose((1, 2, 3, 0))
    img     = fslimage.Image(imgdata, xform=img.voxToWorldMat)
    exp     = np.array([refdata[..., 0]] * 15).transpose((1, 2, 3, 0))
    resampled, xform = resample.resampleToReference(img, ref, order=0, mode='nearest')
    assert np.all(resampled == exp)


def test_resampleToReference4():

    # the image and ref are out of
    # alignment, but this affine
    # will bring them into alignment
    img2ref = affine.scaleOffsetXform([2, 2, 2], [10, 10, 10])

    imgdata = np.random.randint(0, 65536, (5, 5, 5))
    refdata = np.zeros((5, 5, 5))
    img     = fslimage.Image(imgdata)
    ref     = fslimage.Image(refdata, xform=img2ref)

    # Without the affine, the image
    # will be out of the FOV of the
    # reference
    resampled, xform = resample.resampleToReference(img, ref)
    assert np.all(resampled == 0)

    # But applying the affine will
    # cause them to overlap
    # perfectly in world coordinates
    resampled, xform = resample.resampleToReference(img, ref, matrix=img2ref)
    assert np.all(resampled == imgdata)
