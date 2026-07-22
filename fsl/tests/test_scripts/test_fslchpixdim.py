#!/usr/bin/env python

import numpy as np

from fsl.scripts       import fslchpixdim
from fsl.data.image    import Image
from fsl.utils.tempdir import tempdir
from fsl.tests         import make_random_image


def check(image, pixdim):
    xform    = image.getAffine('voxel', 'world')
    expxform = np.diag(list(pixdim[:3]) + [1])
    assert np.all(np.isclose(image.pixdim, pixdim))
    assert np.all(np.isclose(xform,        expxform))


def test_fslchpixdim_xyz():
    with tempdir():
        img = Image(make_random_image('image.nii.gz', pixdims=(1, 1, 1)))
        check(img, [1, 1, 1])
        fslchpixdim.main(('image', '1.5', '1.5', '1.5'))
        check(Image('image'), [1.5, 1.5, 1.5])


def test_fslchpixdim_xyzt():
    with tempdir():
        img = Image(make_random_image('image.nii.gz',
                                      dims=(10, 10, 10, 10),
                                      pixdims=(1, 1, 1, 1)))
        check(img, [1, 1, 1, 1])
        fslchpixdim.main(('image', '2', '2', '2', '4'))
        check(Image('image'), [2, 2, 2, 4])


def test_fslchpixdim_xyzt_out():
    with tempdir():
        img = Image(make_random_image('input.nii.gz',
                                      dims=(10, 10, 10, 10),
                                      pixdims=(1, 1, 1, 1)))
        check(img, [1, 1, 1, 1])
        fslchpixdim.main(('input', '2', '2', '2', '4', 'output'))
        check(Image('input'), [1, 1, 1, 1])
        check(Image('output'), [2, 2, 2, 4])


def test_fslchpixdim_zeros():
    with tempdir():
        img = Image(make_random_image('image.nii.gz',
                                      dims=(10, 10, 10, 10),
                                      pixdims=(2, 3, 4, 5)))
        check(img, [2, 3, 4, 5])
        fslchpixdim.main(('image', '0', '0', '0', '0'))
        check(Image('image'), [2, 3, 4, 5])


def test_fslchpixdim_5d():
    with tempdir():
        img = Image(make_random_image('input.nii.gz',
                                      dims=(10, 10, 10, 10, 10),
                                      pixdims=(1, 1, 1, 1, 1)))
        check(img, [1, 1, 1, 1, 1])
        fslchpixdim.main(('input', '2', '2', '2', '0', 'output'))
        check(Image('output'), [2, 2, 2, 1, 1])

        fslchpixdim.main(('input', '2', '2', '2', '4', 'output'))
        check(Image('output'), [2, 2, 2, 4, 1])
