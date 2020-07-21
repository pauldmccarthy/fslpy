#!/usr/bin/env python
#
# test_vest2text.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import numpy as np

import fsl.data.vest         as fslvest
import fsl.scripts.Text2Vest as Text2Vest
import fsl.scripts.Vest2Text as Vest2Text

from tests import tempdir


def test_usage():
    assert Vest2Text.main([]) == 0
    assert Text2Vest.main([]) == 0


def test_Vest2Text():
    with tempdir():
        data = np.random.random((20, 10))
        vest = fslvest.generateVest(data)

        with open('data.vest', 'wt') as f:
            f.write(vest)

        assert Vest2Text.main(['data.vest', 'data.txt']) == 0

        got = np.loadtxt('data.txt')

        assert np.all(np.isclose(data, got))


def test_Text2Vest():
    with tempdir():
        data = np.random.random((20, 10))

        np.savetxt('data.txt', data)

        assert Text2Vest.main(['data.txt', 'data.vest']) == 0

        got = fslvest.loadVestFile('data.vest', ignoreHeader=False)

        assert np.all(np.isclose(data, got))
