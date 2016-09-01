#!/usr/bin/env python
#
# test_image.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op
import logging


import numpy   as np
import nibabel as nib

import fsl.data.image as fslimage


# Need to test:
#     - Create image from file name (create a temp .nii.gz)
#     - Create image from existing nibabel image
#     - Create image from numpy array
#     - calcRange
#     - loadData

def test_load(testdir):

    assert testdir is not None
    
    fslimage.Image(op.join(testdir, 'nifti_formats', 'compressed'))
    fslimage.Image(op.join(testdir, 'nifti_formats', 'compressed.nii.gz'))
    fslimage.Image(op.join(testdir, 'nifti_formats', 'uncompressed'))
    fslimage.Image(op.join(testdir, 'nifti_formats', 'uncompressed.nii'))
    fslimage.Image(op.join(testdir, 'nifti_formats', 'img_hdr_pair'))
    fslimage.Image(op.join(testdir, 'nifti_formats', 'img_hdr_pair.img'))
    fslimage.Image(op.join(testdir, 'nifti_formats', 'img_hdr_pair.hdr'))


