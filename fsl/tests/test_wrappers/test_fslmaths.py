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

def test_fslmaths2():
    with testenv('fslmaths') as fslmaths:
        result  = fw.fslmaths('input') \
            .thrp(20).thrP(50).uthrp(75).uthrP(90).seed(1234).restart('input2') \
            .save('temp').exp().log().sin().cos().tan().asin().acos().atan() \
            .recip().fillh26().index().grid(1, 2).edge().dog_edge(1, 2) \
            .tfce(1, 2, 3).tfceS(1, 2, 3, 4, 5, 6, 7).nan().nanm().rand() \
            .randn().ing('ingim').tensor_decomp().dilD(3).eroF(2).fmedian() \
            .fmean().s(5).subsamp2().subsamp2offc().run('output')
        expected = f'{fslmaths} input -thrp 20 -thrP 50 -uthrp 75 -uthrP 90 ' \
                   '-seed 1234 -restart input2 -save temp -exp -log -sin ' \
                   '-cos -tan -asin -acos -atan -recip -fillh26 -index '  \
                   '-grid 1 2 -edge -dog_edge 1 2 -tfce 1 2 3 -tfceS 1 2 3 4 ' \
                   '5 6 7 -nan -nanm -rand -randn -ing ingim -tensor_decomp ' \
                   '-dilD -dilD -dilD -eroF -eroF -fmedian -fmean -s 5 ' \
                   '-subsamp2 -subsamp2offc output'
        assert result.stdout[0] == expected


def test_fslmaths3():
    with testenv('fslmaths') as fslmaths:
        result  = fw.fslmaths('input') \
            .Tmean().Tstd().Tmin().Tmax().Tmaxn().Tmedian().Tperc(50).Tar1() \
            .pval().pval0().cpval().ztop().ptoz().rank().ranknorm() \
            .run('output')
        expected = f'{fslmaths} input -Tmean -Tstd -Tmin -Tmax -Tmaxn ' \
                   '-Tmedian -Tperc 50 -Tar1 -pval -pval0 -cpval -ztop ' \
                   '-ptoz -rank -ranknorm output'
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
