#!/usr/bin/env python
#
# test_transform.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


from __future__ import division

import              glob
import os.path   as op
import itertools as it
import numpy     as np

import six

import pytest

import fsl.utils.transform as transform
import fsl.data.image      as fslimage


datadir = op.join(op.dirname(__file__), 'testdata')


def readlines(filename):
    with open(filename, 'rt') as f:
        lines = f.readlines()
        lines = [l.strip()         for l in lines]
        lines = [l                 for l in lines if not l.startswith('#')]
        lines = [l                 for l in lines if l != '']

        # numpy.genfromtxt is busted in python 3.
        # Pass it [str, str, ...], and it complains:
        #
        #   TypeError: must be str or None, not bytes
        #
        # Pass it [bytes, bytes, ...], and it works
        # fine.
        if six.PY3:
            lines = [l.encode('ascii') for l in lines]

    return lines


def test_invert():

    testfile = op.join(datadir, 'test_transform_test_invert.txt')
    testdata = np.loadtxt(testfile)

    nmatrices = testdata.shape[0] // 4

    for i in range(nmatrices):

        x      = testdata[i * 4:i * 4 + 4, 0:4]
        invx   = testdata[i * 4:i * 4 + 4, 4:8]
        result = transform.invert(x)

        assert np.all(np.isclose(invx, result))


def test_concat():

    testfile = op.join(datadir, 'test_transform_test_concat.txt')
    lines    = readlines(testfile)


    ntests = len(lines) // 4
    tests  = []

    for i in range(ntests):
        ilines = lines[i * 4:i * 4 + 4]
        data    = np.genfromtxt(ilines)
        ninputs = data.shape[1] // 4 - 1

        inputs  = []

        for j in range(ninputs):
            inputs.append(data[:, j * 4:j * 4 + 4])

        output = data[:, -4:]

        tests.append((inputs, output))

    for inputs, expected in tests:

        result = transform.concat(*inputs)

        assert np.all(np.isclose(result, expected))


def test_scaleOffsetXform():

    testfile = op.join(datadir, 'test_transform_test_scaleoffsetxform.txt')
    lines    = readlines(testfile)
    ntests   = len(lines) // 5

    for i in range(ntests):

        lineoff         = i * 5
        scales, offsets = lines[lineoff].decode('ascii').split(',')

        scales  = [float(s) for s in scales .split()]
        offsets = [float(o) for o in offsets.split()]

        expected = lines[lineoff + 1: lineoff + 5]
        expected = [[float(v) for v in l.split()] for l in expected]
        expected = np.array(expected)

        result = transform.scaleOffsetXform(scales, offsets)

        assert np.all(np.isclose(result, expected))


def test_compose_and_decompose():

    testfile = op.join(datadir, 'test_transform_test_compose.txt')
    lines    = readlines(testfile)
    ntests   = len(lines) // 4

    for i in range(ntests):

        xform                      = lines[i * 4: i * 4 + 4]
        xform                      = np.genfromtxt(xform)

        scales, offsets, rotations = transform.decompose(xform)
        result = transform.compose(scales, offsets, rotations)

        assert np.all(np.isclose(xform, result, atol=1e-5))

        # The decompose function does not support a
        # different rotation origin, but we test
        # explicitly passing the origin for
        # completeness
        scales, offsets, rotations = transform.decompose(xform)
        result = transform.compose(scales, offsets, rotations, [0, 0, 0])

        assert np.all(np.isclose(xform, result, atol=1e-5))


def test_axisBounds():
    testfile = op.join(datadir, 'test_transform_test_axisBounds.txt')
    lines    = readlines(testfile)
    ntests   = len(lines) // 6

    def readTest(testnum):
        tlines   = lines[testnum * 6: testnum * 6 + 6]
        params   = [p.strip() for p in tlines[0].decode('ascii').split(',')]
        shape    = [int(s) for s in params[0].split()]
        origin   = params[1]
        boundary = None if params[2] == 'None' else params[2]
        xform    = np.genfromtxt(tlines[1:5])
        expected = np.genfromtxt([tlines[5]])
        expected = (expected[:3], expected[3:])

        return shape, origin, boundary, xform, expected

    allAxes  = list(it.chain(
        range(0, 1, 2),
        it.permutations((0, 1, 2), 1),
        it.permutations((0, 1, 2), 2),
        it.permutations((0, 1, 2), 3)))

    for i in range(ntests):

        shape, origin, boundary, xform, expected = readTest(i)

        for axes in allAxes:
            result = transform.axisBounds(shape,
                                          xform,
                                          axes=axes,
                                          origin=origin,
                                          boundary=boundary)

            exp = expected[0][(axes,)], expected[1][(axes,)]

            assert np.all(np.isclose(exp, result))


    # Do some parameter checks on
    # the first test in the file
    # which has origin == centre
    for i in range(ntests):
        shape, origin, boundary, xform, expected = readTest(i)
        if origin == 'centre':
            break

    # US-spelling
    assert np.all(np.isclose(
        expected,
        transform.axisBounds(
            shape, xform, origin='center', boundary=boundary)))

    # Bad origin/boundary values
    with pytest.raises(ValueError):
        transform.axisBounds(shape, xform, origin='Blag', boundary=boundary)
    with pytest.raises(ValueError):
        transform.axisBounds(shape, xform, origin=origin, boundary='Blufu')


def test_transform():

    def is_orthogonal(xform):
        """Returns ``True`` if the given xform consists
        solely of translations and scales.
        """

        mask = np.array([[1, 0, 0, 1],
                         [0, 1, 0, 1],
                         [0, 0, 1, 1],
                         [0, 0, 0, 1]], dtype=np.bool)

        return np.all((xform != 0) == mask)

    coordfile   = op.join(datadir, 'test_transform_test_transform_coords.txt')
    testcoords  = np.loadtxt(coordfile)

    testpattern = op.join(datadir, 'test_transform_test_transform_??.txt')
    testfiles   = glob.glob(testpattern)

    allAxes  = list(it.chain(
        range(0, 1, 2),
        it.permutations((0, 1, 2), 1),
        it.permutations((0, 1, 2), 2),
        it.permutations((0, 1, 2), 3)))

    for i, testfile in enumerate(testfiles):

        lines    = readlines(testfile)
        xform    = np.genfromtxt(lines[:4])
        expected = np.genfromtxt(lines[ 4:])
        result   = transform.transform(testcoords, xform)

        assert np.all(np.isclose(expected, result))

        if not is_orthogonal(xform):
            continue

        for axes in allAxes:
            atestcoords = testcoords[:, axes]
            aexpected   = expected[  :, axes]
            aresult     = transform.transform(atestcoords, xform, axes=axes)

            assert np.all(np.isclose(aexpected, aresult))

    # Pass in some bad data, expect an error
    xform     = np.eye(4)
    badxform  = np.eye(3)
    badcoords = np.random.randint(1, 10, (10, 4))
    coords    = badcoords[:, :3]

    with pytest.raises(IndexError):
        transform.transform(coords, badxform)

    with pytest.raises(ValueError):
        transform.transform(badcoords, xform)

    with pytest.raises(ValueError):
        transform.transform(badcoords.reshape(5, 2, 4), xform)

    with pytest.raises(ValueError):
        transform.transform(badcoords.reshape(5, 2, 4), xform, axes=1)

    with pytest.raises(ValueError):
        transform.transform(badcoords[:, (1, 2, 3)], xform, axes=[1, 2])


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
