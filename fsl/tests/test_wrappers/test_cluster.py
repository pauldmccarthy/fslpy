#!/usr/bin/env python
#
# test_cluster.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import contextlib
import os
import os.path as op
import sys

import numpy as np

from fsl.wrappers.cluster import cluster, _cluster

from .  import testenv
from .. import mockFSLDIR


@contextlib.contextmanager
def reseed(seed):
    state = np.random.get_state()
    np.random.seed(seed)
    try:
        yield
    finally:
        np.random.set_state(state)


def test_cluster_wrapper():
    with testenv('fsl-cluster') as cluster_exe:
        result   = _cluster('input', 10, mm=True)
        expected = [cluster_exe, '-i', 'input', '-t', '10', '--mm']
        expected = ' '.join(expected)
        assert result.stdout[0] == expected


mock_titles  = 'ABCDEFGHIJ'
mock_cluster = f"""
#!{sys.executable}

import numpy as np

np.random.seed(12345)
data = np.random.randint(1, 10, (10, 10))

print('\t'.join('{mock_titles}'))
for row in data:
    print('\t'.join([str(val) for val in row]))
""".strip()


def test_cluster():
    with mockFSLDIR() as fsldir:
        cluster_exe = op.join(fsldir, 'bin', 'fsl-cluster')
        with open(cluster_exe, 'wt') as f:
            f.write(mock_cluster)
        os.chmod(cluster_exe, 0o755)

        data, titles, result1 = cluster('input', 3.5)
        result2               = cluster('input', 3.5, load=False)

    with reseed(12345):
        expected = np.random.randint(1, 10, (10, 10))

    assert np.all(np.isclose(data, expected))
    assert ''.join(titles) == mock_titles
    assert result1.stdout == result2.stdout
