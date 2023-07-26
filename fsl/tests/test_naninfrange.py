#!/usr/bin/env python
#
# test_naninfrange.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import numpy as np

import fsl.utils.naninfrange as naninfrange


def test_naninfrange():
    # numinf, numnan, expectedResult
    tests = [( 0,     0,    (0,      100)),
             ( 0,     1,    (0,      100)),
             ( 1,     0,    (0,      100)),
             ( 1,     1,    (0,      100)),
             ( 5,     5,    (0,      100)),
             ( 0,    'all', (np.nan, np.nan)),
             ('all',  0,    (np.nan, np.nan))]

    # Test non floating point data as wll
    data = np.linspace(0, 100, 100, dtype=np.uint32)
    assert naninfrange.naninfrange(data) == (0, 100)

    for numinf, numnan, expected in tests:

        data   = np.linspace(0, 100, 100)

        if   numinf == 'all': data[:] = np.inf
        elif numnan == 'all': data[:] = np.nan

        nanoff = 1
        if numinf != 'all':
            for i in range(1, numinf + 1):
                data[i] = np.inf
            nanoff += numinf

        if numnan != 'all':
            for i in range(nanoff, numnan + nanoff):
                data[i] = np.nan

        result = naninfrange.naninfrange(data)

        if   np.isfinite(expected[0]): assert result[0] == expected[0]
        elif np.isnan(   expected[0]): assert np.isnan(result[0])
        elif np.isinf(   expected[0]): assert np.isinf(result[0])
        if   np.isfinite(expected[1]): assert result[1] == expected[1]
        elif np.isnan(   expected[1]): assert np.isnan(result[1])
        elif np.isinf(   expected[1]): assert np.isinf(result[1])


def test_naninfrange_structured_ordered_contiguous():

    data = np.random.random((4, 5, 6))

    cdata = data.copy(order='C')
    fdata = data.copy(order='F')

    sdtype = np.dtype([('R', 'float64'), ('G', 'float64'), ('B', 'float64')])
    sdata = np.zeros(data.shape, dtype=sdtype)
    sdata['R'] = data
    sdata['G'] = data
    sdata['B'] = data

    csdata = sdata.copy(order='C')
    fsdata = sdata.copy(order='F')

    tests = [
        cdata,
        cdata.transpose(1, 0, 2),
        cdata[2:4, 1:3, 0:4],
        fdata,
        fdata.transpose(1, 0, 2),
        fdata[2:4, 1:3, 0:4],
        csdata,
        csdata.transpose(1, 0, 2),
        csdata[2:4, 1:3, 0:4],
        fsdata,
        fsdata.transpose(1, 0, 2),
        fsdata[2:4, 1:3, 0:4]
    ]

    for t in tests:
        if len(t.dtype) > 0:
            expmin = np.min([t[n].min() for n in t.dtype.names])
            expmax = np.max([t[n].max() for n in t.dtype.names])
        else:
            expmin, expmax = np.min(t), np.max(t)
        result = naninfrange.naninfrange(t)
        assert np.all(np.isclose(result, (expmin, expmax)))
