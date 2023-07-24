#!/usr/bin/env python
#
# test_transform_flirt.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import itertools as it
import os.path as op

import numpy as np

import fsl.data.image       as fslimage
import fsl.transform.flirt  as flirt
import fsl.transform.affine as affine
import fsl.utils.tempdir    as tempdir

from .test_affine import readlines

from .. import make_random_image


datadir = op.join(op.dirname(__file__), 'testdata')


def test_read_write():
    with tempdir.tempdir():
        aff = np.random.random((4, 4))
        flirt.writeFlirt(aff, 'aff.mat')
        got = flirt.readFlirt('aff.mat')
        assert np.all(np.isclose(aff, got))


def test_fromFlirt():

    src = affine.compose(np.random.randint( 1,  5,  3),
                         np.random.randint(-20, 20, 3),
                         np.random.random(3) - 0.5)
    ref = affine.compose(np.random.randint( 1,  5,  3),
                         np.random.randint(-20, 20, 3),
                         np.random.random(3) - 0.5)

    src      = fslimage.Image(make_random_image(xform=src))
    ref      = fslimage.Image(make_random_image(xform=ref))
    flirtmat = affine.concat(ref.getAffine('world', 'fsl'),
                             src.getAffine('fsl',   'world'))


    spaces = it.permutations(('voxel', 'fsl', 'world'), 2)

    for from_, to in spaces:
        got = flirt.fromFlirt(flirtmat, src, ref, from_, to)
        exp = affine.concat(ref.getAffine('fsl', to),
                            flirtmat,
                            src.getAffine(from_, 'fsl'))

        assert np.all(np.isclose(got, exp))


def test_toFlirt():

    src = affine.compose(np.random.randint( 1,  5,  3),
                         np.random.randint(-20, 20, 3),
                         np.random.random(3) - 0.5)
    ref = affine.compose(np.random.randint( 1,  5,  3),
                         np.random.randint(-20, 20, 3),
                         np.random.random(3) - 0.5)

    src      = fslimage.Image(make_random_image(xform=src))
    ref      = fslimage.Image(make_random_image(xform=ref))
    flirtmat = affine.concat(ref.getAffine('world', 'fsl'),
                             src.getAffine('fsl',   'world'))


    spaces = it.permutations(('voxel', 'fsl', 'world'), 2)

    for from_, to in spaces:
        xform = affine.concat(ref.getAffine('world', to),
                              src.getAffine(from_, 'world'))
        got = flirt.toFlirt(xform, src, ref, from_, to)

        assert np.all(np.isclose(got, flirtmat))


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

        result = flirt.flirtMatrixToSform(flirtMat, srcImg, refImg)

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

        result1 = flirt.sformToFlirtMatrix(srcImg1, refImg, srcXformOvr)
        result2 = flirt.sformToFlirtMatrix(srcImg2, refImg)

        assert np.all(np.isclose(result1, expected))
        assert np.all(np.isclose(result2, expected))
