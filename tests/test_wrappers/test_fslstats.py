#!/usr/bin/env python


import os
import os.path as op
import textwrap as tw
import sys
import contextlib

import pytest

import numpy as np

import fsl.utils.run as run
import fsl.utils.tempdir as tempdir
import fsl.wrappers  as fw

from .. import mockFSLDIR as mockFSLDIR_base, make_random_image


mock_fslstats = """
#!/usr/bin/env python3

shape = {outshape}

import sys
import numpy as np

data = np.random.randint(1, 10, shape)

if len(shape) == 1:
    data = data.reshape(1, -1)

np.savetxt(sys.stdout, data, fmt='%i')
""".strip()


@contextlib.contextmanager
def mockFSLDIR(shape=None, fslstats=None):
    with mockFSLDIR_base() as fd:
        fname  = op.join(fd, 'bin', 'fslstats')

        if shape is not None:
            script = mock_fslstats.format(outshape=shape)
        else:
            script = fslstats
        with open(fname, 'wt') as f:
            f.write(script)
        os.chmod(fname, 0o755)
        yield fd


def test_fslstats_cmdline():
    with tempdir.tempdir(), run.dryrun(), mockFSLDIR(1) as fsldir:

        make_random_image('image')
        cmd = op.join(fsldir, 'bin', 'fslstats')

        result   = fw.fslstats('image').m.r.mask('mask').k('mask').r.run(True)
        expected = cmd + ' image -m -r -k mask -k mask -r'
        assert result[0] == expected

        result   = fw.fslstats('image', t=True, K='mask').m.R.u(123).s.volume.run(True)
        expected = cmd + ' -t -K mask image -m -R -u 123 -s -v'
        assert result[0] == expected

        result   = fw.fslstats('image', K='mask').n.V.p(1).run(True)
        expected = cmd + ' -K mask image -n -V -p 1'
        assert result[0] == expected

        result   = fw.fslstats('image', t=True).H(10, 1, 99).d('diff').run(True)
        expected = cmd + ' -t image -H 10 1 99 -d diff'
        assert result[0] == expected

        # unknown option
        with pytest.raises(AttributeError):
            fw.fslstats('image').Q


def test_fslstats_result():
    with tempdir.tempdir():

        with mockFSLDIR('(1,)') as fsldir:
            result = fw.fslstats('image').run()
            assert np.isscalar(result)

        with mockFSLDIR('(2,)') as fsldir:
            result = fw.fslstats('image').run()
            assert result.shape == (2,)

        # 3 mask lbls, 2 values
        with mockFSLDIR('(3, 2)') as fsldir:
            result = fw.fslstats('image', K='mask').run()
            assert result.shape == (3, 2)

        # 5 vols, 2 values
        with mockFSLDIR('(5, 2)') as fsldir:
            result = fw.fslstats('image', t=True).run()
            assert result.shape == (5, 2)

        # 5 vols, 3 mask lbls, 2 values
        with mockFSLDIR('(15, 2)') as fsldir:
            make_random_image('image', (10, 10, 10, 5))
            result = fw.fslstats('image', K='mask', t=True).run()
            assert result.shape == (5, 3, 2)

        # -t/-K with a 3D image
        with mockFSLDIR('(4,)') as fsldir:
            make_random_image('image', (10, 10, 10))
            result = fw.fslstats('image', K='mask', t=True).run()
            assert result.shape == (4,)

            result = fw.fslstats('image', t=True).run()
            assert result.shape == (4,)

            result = fw.fslstats('image', K='mask').run()
            assert result.shape == (4,)


def test_fslstats_index_mask_missing_labels():
    script = tw.dedent("""
    #!/usr/bin/env bash

    echo "1"
    echo "missing label: 2"
    echo "3"
    echo "missing label: 4"
    echo "5"
    """).strip()
    with tempdir.tempdir():
        with mockFSLDIR(fslstats=script) as fsldir:
            result = fw.fslstats('image', K='mask').p(50).run()
            expect = np.array([1, np.nan, 3, np.nan, 5])
            namask = np.isnan(expect)
            assert np.all(result[~namask]  == expect[~namask])
            assert np.all(np.isnan(expect) == np.isnan(result))
