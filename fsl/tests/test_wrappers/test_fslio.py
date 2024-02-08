#!/usr/bin/env python
#
# test_fslio.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path as op

from unittest import mock

from fsl.utils.tempdir import tempdir

from fsl.tests import make_random_image

import fsl.wrappers as fw


def test_fslio_wrappers():
    with tempdir(), mock.patch.dict('os.environ', FSLOUTPUTTYPE='NIFTI_GZ'):
        make_random_image('image.nii.gz')

        fw.imcp('image', 'image2')
        assert op.exists('image2.nii.gz')

        fw.imln('image', 'imagelink')
        assert op.islink('imagelink.nii.gz')

        fw.immv('image2', 'image3')
        assert not op.exists('image2.nii.gz')
        assert     op.exists('image3.nii.gz')

        assert sorted(fw.imglob('image*')) == ['image', 'image3', 'imagelink']

        fw.imrm('image3')
        assert not op.exists('image3.nii.gz')

        assert fw.imtest('image')
