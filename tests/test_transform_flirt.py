#!/usr/bin/env python
#
# test_transform_flirt.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op

import numpy as np

import fsl.data.image as fslimage
import fsl.utils.transform as transform
import fsl.utils.tempdir   as tempdir

from .test_transform import readlines


datadir = op.join(op.dirname(__file__), 'testdata')


def test_read_write():
    with tempdir.tempdir():
        aff = np.random.random((4, 4))
        transform.writeFlirt(aff, 'aff.mat')
        got = transform.readFlirt('aff.mat')
        assert np.all(np.isclose(aff, got))


def test_fromFlirt():
    pass


def test_toFlirt():
    pass


def test_flirtMatrixToSform():

    testfile = op.join(datadir, 'test_transform_test_flirtMatrixToSform.txt')
    lines    = readlines(testfile)
    ntests   = len(lines) // 18

    for i in range(ntests):
        tlines    = lines[i * 18: i * 18 + 18]
        srcShape  = [int(  w) for w in tlines[0].split()]
        srcXform  = np.genfromtxt(tlines[1:5])
        refShape  = [int(  w) for w in tlines[5].split()]
        refXform  = np.genfromtxt(tlines[6:10])
        flirtMat  = np.genfromtxt(tlines[10:14])
        expected  = np.genfromtxt(tlines[14:18])

        srcImg = fslimage.Image(np.zeros(srcShape), xform=srcXform)
        refImg = fslimage.Image(np.zeros(refShape), xform=refXform)

        result = transform.flirtMatrixToSform(flirtMat, srcImg, refImg)

        assert np.all(np.isclose(result, expected))


def test_sformToFlirtMatrix():
    testfile = op.join(datadir, 'test_transform_test_flirtMatrixToSform.txt')
    lines    = readlines(testfile)
    ntests   = len(lines) // 18

    for i in range(ntests):
        tlines      = lines[i * 18: i * 18 + 18]
        srcShape    = [int(  w) for w in tlines[0].split()]
        srcXform    = np.genfromtxt(tlines[1:5])
        refShape    = [int(  w) for w in tlines[5].split()]
        refXform    = np.genfromtxt(tlines[6:10])
        expected    = np.genfromtxt(tlines[10:14])
        srcXformOvr = np.genfromtxt(tlines[14:18])

        srcImg1 = fslimage.Image(np.zeros(srcShape), xform=srcXform)
        srcImg2 = fslimage.Image(np.zeros(srcShape), xform=srcXform)
        refImg  = fslimage.Image(np.zeros(refShape), xform=refXform)

        srcImg2.voxToWorldMat = srcXformOvr

        result1 = transform.sformToFlirtMatrix(srcImg1, refImg, srcXformOvr)
        result2 = transform.sformToFlirtMatrix(srcImg2, refImg)

        assert np.all(np.isclose(result1, expected))
        assert np.all(np.isclose(result2, expected))
