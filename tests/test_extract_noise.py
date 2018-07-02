#!/usr/bin/env python
#
# test_extract_noise.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import numpy as np

import pytest

import fsl.utils.tempdir         as tempdir
import fsl.scripts.extract_noise as extn


def test_genComponentIndexList():

    with tempdir.tempdir():

        # sequence of 1-indexed integers/file paths
        icomps  = [1, 5, 28, 12, 42, 54]
        fcomps1 = [1, 4, 6, 3, 7]
        fcomps2 = [12, 42, 31, 1, 4, 8]

        with open('comps1.txt', 'wt') as f:
            f.write(','.join([str(l) for l in fcomps1]))
        with open('comps2.txt', 'wt') as f:
            f.write(','.join([str(l) for l in fcomps2]))

        ncomps   = 60
        comps    = icomps + ['comps1.txt', 'comps2.txt']
        expcomps = list(sorted(set(icomps + fcomps1 + fcomps2)))
        expcomps = [c - 1 for c in expcomps]

        assert extn.genComponentIndexList(comps, ncomps) == expcomps

        with pytest.raises(ValueError):
            extn.genComponentIndexList(comps + [-1], 60)
        with pytest.raises(ValueError):
            extn.genComponentIndexList(comps, 40)


def test_loadConfoundFiles():
    with tempdir.tempdir():

        npts  = 50
        confs = [
            np.random.randint(1, 100, (50, 10)),
            np.random.randint(1, 100, (50, 1)),
            np.random.randint(1, 100, (50, 5))]

        badconfs = [
            np.random.randint(1, 100, (40, 10)),
            np.random.randint(1, 100, (60, 10))]

        expected            = np.empty((50, 16), dtype=np.float64)
        expected[:, :]      = np.nan
        expected[:, :10]    = confs[0]
        expected[:,  10:11] = confs[1]
        expected[:,  11:16] = confs[2]

        conffiles = []
        for i, c in enumerate(confs):
            fname = 'conf{}.txt'.format(i)
            conffiles.append(fname)
            np.savetxt(fname, c)

        result = extn.loadConfoundFiles(conffiles, npts)
        amask  = ~np.isnan(expected)

        assert np.all(~np.isnan(result) == amask)
        assert np.all(result[amask]     == expected[amask])
        assert np.all(result[amask]     == expected[amask])

        badconfs = [
            np.random.randint(1, 100, (40, 10)),
            np.random.randint(1, 100, (60, 10))]
        conffiles = []
        for i, c in enumerate(badconfs):
            fname = 'conf{}.txt'.format(i)
            conffiles.append(fname)
            np.savetxt(fname, c)

        with pytest.raises(ValueError):
            extn.loadConfoundFiles(conffiles, npts)
