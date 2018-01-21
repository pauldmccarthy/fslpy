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


def test_MGHImage():

    datadir  = op.join(op.dirname(__file__), 'testdata')
    testfile = op.join(datadir, 'example.mgz')

    # Load from a file
    img      = fslmgh.MGHImage(testfile)
    nbimg    = nib.load(testfile)

    assert np.all(np.isclose(img[:],            nbimg.get_data()))
    assert np.all(np.isclose(img.voxToWorldMat, nbimg.affine))
    assert img.mghImageFile == testfile

    # Load from an in-memory nibabel object
    img = fslmgh.MGHImage(nbimg)
    assert np.all(np.isclose(img[:],            nbimg.get_data()))
    assert np.all(np.isclose(img.voxToWorldMat, nbimg.affine))
    assert img.mghImageFile is None
