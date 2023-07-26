#!/usr/bin/env python
#
# test_fslmaths.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import             os
import os.path  as op
import textwrap as tw
import numpy    as np

from fsl.utils.tempdir import tempdir

import fsl.wrappers as fw

from .. import mockFSLDIR, make_random_image
from .  import testenv


def test_fslmaths():
    with testenv('fslmaths') as fslmaths:
        result   = fw.fslmaths('input') \
            .range() \
            .abs().bin().binv().recip().Tmean().Tstd().Tmin().Tmax() \
            .fillh().ero().dilM().dilF().add('addim').sub('subim') \
            .mul('mulim').div('divim').mas('masim').rem('remim')   \
            .thr('thrim').uthr('uthrim').inm('inmim').bptf(1, 10) \
            .smooth(sigma=6).kernel('3D').fmeanu().roi(10, 3, 20, 21, 1, 5) \
            .sqr().sqrt().log().dilD(2).max('im').min('im2') \
            .fmedian().kernel('3D').kernel('box', 3) \
            .run('output')

        expected = [fslmaths, 'input', '-range',
                    '-abs', '-bin', '-binv', '-recip', '-Tmean', '-Tstd',
                    '-Tmin', '-Tmax', '-fillh', '-ero', '-dilM', '-dilF',
                    '-add addim', '-sub subim', '-mul mulim', '-div divim',
                    '-mas masim', '-rem remim', '-thr thrim', '-uthr uthrim',
                    '-inm inmim', '-bptf 1 10', '-s 6', '-kernel 3D', '-fmeanu',
                    '-roi 10 3 20 21 1 5 0 -1', '-sqr', '-sqrt', '-log',
                    '-dilD', '-dilD', '-max', 'im', '-min', 'im2', '-fmedian',
                    '-kernel', '3D', '-kernel', 'box', '3', 'output']
        expected = ' '.join(expected)

        assert result.stdout[0] == expected


def test_fslmaths_load():
    with testenv('fslmaths') as fslmaths:
        result   = fw.fslmaths('input', 'char').ero().ero().bin()\
                       .run('output', 'float')
        expected = f'{fslmaths} -dt char input -ero -ero -bin ' \
                    'output -odt float'
        assert result.stdout[0] == expected


def test_fslmaths_load():
    with tempdir() as td, mockFSLDIR(bin=('fslmaths',)) as fsldir:
        expect = make_random_image(op.join(td, 'output.nii.gz'))

        with open(op.join(fsldir, 'bin', 'fslmaths'), 'wt') as f:
            f.write(tw.dedent("""
            #!/usr/bin/env python
            import sys
            import shutil
            shutil.copy('{}', sys.argv[2])
            """.format(op.join(td, 'output.nii.gz'))).strip())
            os.chmod(op.join(fsldir, 'bin', 'fslmaths'), 0o755)

        got = fw.fslmaths('input').run()
        assert np.all(expect.dataobj[:] == got.dataobj[:])
        got = fw.fslmaths('input').run(fw.LOAD)
        assert np.all(expect.dataobj[:] == got.dataobj[:])
