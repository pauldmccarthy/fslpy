#!/usr/bin/env python
#
# test_transform.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op

import numpy as np

import fsl.utils.transform as transform


datadir = op.join(op.dirname(__file__), 'testdata')


def readlines(filename):
    with open(filename, 'rt') as f:
        lines = f.readlines()
        lines = [l.strip() for l in lines]
        lines = [l         for l in lines if not l.startswith('#')]
        lines = [l         for l in lines if l != '']
    return lines


def test_invert():

    testfile = op.join(datadir, 'test_transform_test_invert.txt')
    testdata = np.loadtxt(testfile)

    nmatrices = testdata.shape[0] / 4

    for i in range(nmatrices):

        x      = testdata[i * 4:i * 4 + 4, 0:4]
        invx   = testdata[i * 4:i * 4 + 4, 4:8]
        result = transform.invert(x)

        assert np.all(np.isclose(invx, result))


def test_concat():
    
    testfile = op.join(datadir, 'test_transform_test_concat.txt')
    lines    = readlines(testfile)


    ntests = len(lines) / 4
    tests  = []

    for i in range(ntests):
        ilines = lines[i * 4:i * 4 + 4]

        data    = np.genfromtxt(ilines)
        ninputs = data.shape[1] / 4 - 1

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
    ntests   = len(lines) / 5

    for i in range(ntests):
        
        lineoff         = i * 5
        scales, offsets = lines[lineoff].split(',')

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
    ntests   = len(lines) / 4

    for i in range(ntests):

        xform                      = lines[i * 4: i * 4 + 4]
        xform                      = np.genfromtxt(xform)
        
        scales, offsets, rotations = transform.decompose(xform)
        result = transform.compose(scales, offsets, rotations)

        assert np.all(np.isclose(xform, result))

        # The decompose function does not support a
        # different rotation origin, but we test
        # explicitly passing the origin for
        # completeness
        scales, offsets, rotations = transform.decompose(xform)
        result = transform.compose(scales, offsets, rotations, [0, 0, 0])

        assert np.all(np.isclose(xform, result))
