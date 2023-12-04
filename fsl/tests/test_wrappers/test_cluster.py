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
import textwrap as tw

from unittest import mock

import numpy as np

from fsl.wrappers import wrapperutils as wutils
from fsl.wrappers.cluster_commands import (cluster,
                                           _cluster,
                                           smoothest,
                                           _smoothest)

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
#!/usr/bin/env python

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


def test_smoothest_wrapper():
    with testenv('smoothest') as smoothest_exe:
        result   = _smoothest(res='res', zstat='zstat', d=5, V=True)
        expected = f'{smoothest_exe} --res=res --zstat=zstat -d 5 -V'
        assert result.stdout[0] == expected

        # auto detect residuals vs zstat
        result   = _smoothest('res4d.nii.gz', d=5, V=True)
        expected = f'{smoothest_exe} -d 5 -V --res=res4d.nii.gz'
        assert result.stdout[0] == expected

        result   = _smoothest('zstat1.nii.gz', d=5, V=True)
        expected = f'{smoothest_exe} -d 5 -V --zstat=zstat1.nii.gz'
        assert result.stdout[0] == expected


def test_smoothest():

    result = tw.dedent("""
    FWHMx = 4.763 mm, FWHMy = 5.06668 mm, FWHMz = 4.71527 mm
    DLH 0.324569 voxels^-3
    VOLUME 244531 voxels
    RESELS 14.224 voxels per resel
    DLH 0.324569
    VOLUME 244531
    RESELS 14.224
    FWHMvoxel 2.3815 2.53334 2.35763
    FWHMmm 4.763 5.06668 4.71527
    """)

    result = wutils.FileOrThing.Results((result, ''))

    expect = {
        'DLH'       : 0.324569,
        'VOLUME'    : 244531,
        'RESELS'    : 14.224,
        'FWHMvoxel' : [2.3815, 2.53334, 2.35763],
        'FWHMmm'    : [4.763,  5.06668, 4.71527]
    }

    with mock.patch('fsl.wrappers.cluster_commands._smoothest',
                    return_value=result):

        result = smoothest('inimage')

        assert result.keys() == expect.keys()
        assert        np.isclose(result['DLH'],       expect['DLH'])
        assert        np.isclose(result['VOLUME'],    expect['VOLUME'])
        assert        np.isclose(result['RESELS'],    expect['RESELS'])
        assert np.all(np.isclose(result['FWHMvoxel'], expect['FWHMvoxel']))
        assert np.all(np.isclose(result['FWHMmm'],    expect['FWHMmm']))
