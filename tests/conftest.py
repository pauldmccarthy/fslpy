#!/usr/bin/env python
#
# conftest.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import pytest


def pytest_addoption(parser):
    parser.addoption('--niters',
                     type=int,
                     action='store',
                     default=150,
                     help='Number of test iterations for imagewrapper')
    
    parser.addoption('--testdir',
                     action='store',
                     help='FSLeyes test data directory')


    
@pytest.fixture
def testdir(request):
    """FSLeyes test data directory."""
    return request.config.getoption('--testdir')


@pytest.fixture
def niters(request):
    """Number of test iterations."""
    return request.config.getoption('--niters')
