#!/usr/bin/env python
#
# test_ensure.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import pathlib

import numpy   as np
import nibabel as nib

import fsl.utils.tempdir as tempdir
import fsl.utils.ensure  as ensure

from . import make_random_image


def test_ensureIsImage():

    with tempdir.tempdir():
        img = make_random_image('image.nii')

        assert ensure.ensureIsImage(img) is img

        loaded = [ensure.ensureIsImage(             'image.nii'),
                  ensure.ensureIsImage(             'image'),
                  ensure.ensureIsImage(pathlib.Path('image')),
                  ensure.ensureIsImage(pathlib.Path('image.nii'))]

        for l in loaded:
            assert isinstance(l, nib.nifti1.Nifti1Image)
            assert np.all(np.asanyarray(img.dataobj) == np.asanyarray(l.dataobj))

        l = None
        loaded = None
        img = None
