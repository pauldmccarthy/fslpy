#!/usr/bin/env python


import numpy as np

import pytest

import fsl.scripts.resample_image as resample_image


import  fsl.utils.transform as transform
from fsl.utils.tempdir import tempdir
from fsl.data.image    import Image

from .. import make_random_image


def test_resample_image_shape():
    with tempdir():
        img = Image(make_random_image('image.nii.gz', dims=(10, 10, 10)))
        resample_image.main('image resampled -s 20 20 20'.split())
        res = Image('resampled')

        expv2w = transform.concat(
            img.voxToWorldMat,
            transform.scaleOffsetXform([0.5, 0.5, 0.5], 0))

        assert np.all(np.isclose(res.shape, (20, 20, 20)))
        assert np.all(np.isclose(res.pixdim, (0.5, 0.5, 0.5)))
        assert np.all(np.isclose(res.voxToWorldMat, expv2w))
        assert np.all(np.isclose(
            np.array(transform.axisBounds(res.shape, res.voxToWorldMat)) - 0.25,
                     transform.axisBounds(img.shape, img.voxToWorldMat)))

        resample_image.main('image resampled -s 20 20 20 -o corner'.split())
        res = Image('resampled')
        assert np.all(np.isclose(
            transform.axisBounds(res.shape, res.voxToWorldMat),
            transform.axisBounds(img.shape, img.voxToWorldMat)))


def test_resample_image_dim():
    with tempdir():
        img = Image(make_random_image('image.nii.gz', dims=(10, 10, 10)))

        resample_image.main('image resampled -d 0.5 0.5 0.5'.split())

        res = Image('resampled')
        expv2w = transform.concat(
            img.voxToWorldMat,
            transform.scaleOffsetXform([0.5, 0.5, 0.5], 0))

        assert np.all(np.isclose(res.shape, (20, 20, 20)))
        assert np.all(np.isclose(res.pixdim, (0.5, 0.5, 0.5)))
        assert np.all(np.isclose(res.voxToWorldMat, expv2w))


def test_resample_image_ref():
    with tempdir():
        img = Image(make_random_image('image.nii.gz', dims=(10, 10, 10)))
        ref = Image(make_random_image('ref.nii.gz',   dims=(20, 20, 20),
                                      pixdims=(0.5, 0.5, 0.5)))

        resample_image.main('image resampled -r ref'.split())

        res    = Image('resampled')
        expv2w = ref.voxToWorldMat

        assert np.all(np.isclose(res.shape, (20, 20, 20)))
        assert np.all(np.isclose(res.pixdim, (0.5, 0.5, 0.5)))
        assert np.all(np.isclose(res.voxToWorldMat, expv2w))


def test_resample_image_bad_options():
    with tempdir():
        img = Image(make_random_image('image.nii.gz', dims=(10, 10, 10)))

        with pytest.raises(SystemExit) as e:
            resample_image.main('image resampled -d 0.5 0.5 0.5 '
                                '-s 20 20 20'.split())
        assert e.value.code != 0
