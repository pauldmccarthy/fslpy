#!/usr/bin/env python
#
# conftest.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import pytest

import os.path as op
import random
import numpy as np



def pytest_addoption(parser):
    parser.addoption('--niters',
                     type=int,
                     action='store',
                     default=50,
                     help='Number of test iterations for imagewrapper')

    parser.addoption('--testdir',
                     action='store',
                     help='FSLeyes test data directory')

    parser.addoption('--seed',
                     type=int,
                     help='Seed for random number generator')


@pytest.fixture
def niters(request):
    """Number of test iterations."""
    return request.config.getoption('--niters')


@pytest.fixture
def seed(request):

    seed = request.config.getoption('--seed')

    if seed is None:
        seed = np.random.randint(2 ** 30)

    np.random.seed(seed)
    random   .seed(seed)
    print('Seed for random number generator: {}'.format(seed))
    return seed
