#!/usr/bin/env python
#
# test_mghimage.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path as op

import numpy   as np
import nibabel as nib

from . import testdir

import fsl.data.mghimage as fslmgh


def test_looksLikeMGHImage():

    lookLike   = ['test.mgz', 'test.mgh']
    noLookLike = ['test.nii', 'test', 'testmgh.mga', 'test.mgza', 'test.mgha']


    for l  in lookLike:   assert     fslmgh.looksLikeMGHImage(l)
    for nl in noLookLike: assert not fslmgh.looksLikeMGHImage(nl)


def test_MGHImage():

    datadir  = op.join(op.dirname(__file__), 'testdata')
    testfile = op.join(datadir, 'example.mgz')

    img      = fslmgh.MGHImage(testfile)
    nbimg    = nib.load(testfile)

    assert np.all(np.isclose(img[:],            nbimg.get_data()))
    assert np.all(np.isclose(img.voxToWorldMat, nbimg.affine))
