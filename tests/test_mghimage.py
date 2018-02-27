#!/usr/bin/env python
#
# test_mghimage.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path as op
import            shutil

import numpy   as np
import nibabel as nib

import fsl.utils.tempdir as tempdir
import fsl.data.mghimage as fslmgh
import fsl.data.image    as fslimage


datadir = op.join(op.abspath(op.dirname(__file__)), 'testdata')


def test_MGHImage():

    testfile = op.join(datadir, 'example.mgz')

    # Load from a file
    img      = fslmgh.MGHImage(testfile)
    nbimg    = nib.load(testfile)

    assert np.all(np.isclose(img[:],            nbimg.get_data()))
    assert np.all(np.isclose(img.voxToWorldMat, nbimg.affine))
    assert img.name         == op.basename(testfile)
    assert img.dataSource   == testfile
    assert img.mghImageFile == testfile

    # Load from an in-memory nibabel object
    img = fslmgh.MGHImage(nbimg)
    assert np.all(np.isclose(img[:],            nbimg.get_data()))
    assert np.all(np.isclose(img.voxToWorldMat, nbimg.affine))
    assert img.dataSource   is None
    assert img.mghImageFile is None


def test_MGHImage_save():

    testfile = op.join(datadir, 'example.mgz')

    with tempdir.tempdir():

        shutil.copy(testfile, 'example.mgz')

        testfile = 'example.mgz'

        img = fslmgh.MGHImage(testfile)

        img.save()

        expfile = op.abspath(fslimage.addExt('example', mustExist=False))

        assert img.dataSource == op.abspath(expfile)
