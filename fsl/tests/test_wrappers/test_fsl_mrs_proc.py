#!/usr/bin/env python
#
# test_fsl_mrs_proc.py -
#
# Author: Vasilis Karlaftis <vasilis.karlaftis@ndcn.ox.ac.uk>
#

import pytest

import fsl.wrappers as fw
from fsl.tests.test_wrappers import testenv


pytestmark = pytest.mark.mrstest


def test_fsl_mrs_proc_coilcombine():
    with testenv('fsl_mrs_proc') as fsl_mrs_proc:
        # test simple call
        result = fw.fsl_mrs_proc.coilcombine('file', 'output')
        expected = f'{fsl_mrs_proc} coilcombine --file file --output output'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.fsl_mrs_proc.coilcombine('file', 'output', reference='reference', r=True)
        expected = f'{fsl_mrs_proc} coilcombine --file file --output output --reference reference --generateReports'
        assert result.stdout[0] == expected


def test_fsl_mrs_proc_average():
    with testenv('fsl_mrs_proc') as fsl_mrs_proc:
        # test simple call
        result = fw.fsl_mrs_proc.average('file', 'output')
        expected = f'{fsl_mrs_proc} average --file file --output output'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.fsl_mrs_proc.average('file', 'output', dim='DIM_DYN', filename='filename')
        expected = f'{fsl_mrs_proc} average --file file --output output --dim DIM_DYN --filename filename'
        assert result.stdout[0] == expected


def test_fsl_mrs_proc_align():
    with testenv('fsl_mrs_proc') as fsl_mrs_proc:
        # test simple call
        result = fw.fsl_mrs_proc.align('file', 'output')
        expected = f'{fsl_mrs_proc} align --file file --output output'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.fsl_mrs_proc.align('file', 'output', ppm=(1.8, 3.5), apod=50, filename='filename')
        expected = f'{fsl_mrs_proc} align --file file --output output --ppm 1.8 3.5 --apod 50 --filename filename'
        assert result.stdout[0] == expected


def test_fsl_mrs_proc_align_diff():
    with testenv('fsl_mrs_proc') as fsl_mrs_proc:
        # test simple call
        result = fw.fsl_mrs_proc.align_diff('file', 'output')
        expected = f'{fsl_mrs_proc} align-diff --file file --output output'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.fsl_mrs_proc.align_diff('file', 'output', ppm=[1.8, 3.5], dim='DIM_DYN',
                                            dim_diff='DIM_EDIT', diff_type='add',)
        expected = f'{fsl_mrs_proc} align-diff --file file --output output --ppm 1.8 3.5'\
                    ' --dim DIM_DYN --dim_diff DIM_EDIT --diff_type add'
        assert result.stdout[0] == expected


def test_fsl_mrs_proc_ecc():
    with testenv('fsl_mrs_proc') as fsl_mrs_proc:
        # test simple call
        result = fw.fsl_mrs_proc.ecc('file', 'reference', 'output')
        expected = f'{fsl_mrs_proc} ecc --file file --reference reference --output output'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.fsl_mrs_proc.ecc('file', 'reference', 'output', filename='filename')
        expected = f'{fsl_mrs_proc} ecc --file file --reference reference --output output --filename filename'
        assert result.stdout[0] == expected


def test_fsl_mrs_proc_remove():
    with testenv('fsl_mrs_proc') as fsl_mrs_proc:
        # test simple call
        result = fw.fsl_mrs_proc.remove('file', 'output')
        expected = f'{fsl_mrs_proc} remove --file file --output output'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.fsl_mrs_proc.remove('file', 'output', filename='filename', r=True)
        expected = f'{fsl_mrs_proc} remove --file file --output output --filename filename --generateReports'
        assert result.stdout[0] == expected


def test_fsl_mrs_proc_model():
    with testenv('fsl_mrs_proc') as fsl_mrs_proc:
        # test simple call
        result = fw.fsl_mrs_proc.model('file', 'output')
        expected = f'{fsl_mrs_proc} model --file file --output output'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.fsl_mrs_proc.model('file', 'output', ppm=(4.5, 4.8), components=7, allreports=True)
        expected = f'{fsl_mrs_proc} model --file file --output output --ppm 4.5 4.8 --components 7 --allreports'
        assert result.stdout[0] == expected


def test_fsl_mrs_proc_tshift():
    with testenv('fsl_mrs_proc') as fsl_mrs_proc:
        # test simple call
        result = fw.fsl_mrs_proc.tshift('file', 'output')
        expected = f'{fsl_mrs_proc} tshift --file file --output output'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.fsl_mrs_proc.tshift('file', 'output', tshiftStart=1.2, tshiftEnd=2.3, samples=10)
        expected = f'{fsl_mrs_proc} tshift --file file --output output --tshiftStart 1.2 --tshiftEnd 2.3 --samples 10'
        assert result.stdout[0] == expected


def test_fsl_mrs_proc_truncate():
    with testenv('fsl_mrs_proc') as fsl_mrs_proc:
        # test simple call
        result = fw.fsl_mrs_proc.truncate('file', 'output')
        expected = f'{fsl_mrs_proc} truncate --file file --output output'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.fsl_mrs_proc.truncate('file', 'output', points=-1, pos='first', generateReports=True)
        expected = f'{fsl_mrs_proc} truncate --file file --output output --points -1 --pos first --generateReports'
        assert result.stdout[0] == expected


def test_fsl_mrs_proc_apodize():
    with testenv('fsl_mrs_proc') as fsl_mrs_proc:
        # test simple call
        result = fw.fsl_mrs_proc.apodize('file', 'output')
        expected = f'{fsl_mrs_proc} apodize --file file --output output'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.fsl_mrs_proc.apodize('file', 'output', filter='exp', amount=[1, 2])
        expected = f'{fsl_mrs_proc} apodize --file file --output output --filter exp --amount 1 2'
        assert result.stdout[0] == expected


def test_fsl_mrs_proc_fshift():
    with testenv('fsl_mrs_proc') as fsl_mrs_proc:
        # test simple call
        result = fw.fsl_mrs_proc.fshift('file', 'output')
        expected = f'{fsl_mrs_proc} fshift --file file --output output'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.fsl_mrs_proc.fshift('file', 'output', shiftppm=4.65, shifthz=10.5,
                                        shiftRef=True, target=3.027, use_avg=True)
        expected = f'{fsl_mrs_proc} fshift --file file --output output --shiftppm 4.65'\
                    ' --shifthz 10.5 --shiftRef --target 3.027 --use_avg'
        assert result.stdout[0] == expected


def test_fsl_mrs_proc_unlike():
    with testenv('fsl_mrs_proc') as fsl_mrs_proc:
        # test simple call
        result = fw.fsl_mrs_proc.unlike('file', 'output')
        expected = f'{fsl_mrs_proc} unlike --file file --output output'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.fsl_mrs_proc.unlike('file', 'output', sd=1.96, iter=2, outputbad=True)
        expected = f'{fsl_mrs_proc} unlike --file file --output output --sd 1.96 --iter 2 --outputbad'
        assert result.stdout[0] == expected


def test_fsl_mrs_proc_phase():
    with testenv('fsl_mrs_proc') as fsl_mrs_proc:
        # test simple call
        result = fw.fsl_mrs_proc.phase('file', 'output')
        expected = f'{fsl_mrs_proc} phase --file file --output output'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.fsl_mrs_proc.phase('file', 'output', filename='filename', ppm=(4.6, 4.7), hlsvd=True)
        expected = f'{fsl_mrs_proc} phase --file file --output output --filename filename --ppm 4.6 4.7 --hlsvd'
        assert result.stdout[0] == expected



def test_fsl_mrs_proc_fixed_phase():
    with testenv('fsl_mrs_proc') as fsl_mrs_proc:
        # test simple call
        result = fw.fsl_mrs_proc.fixed_phase('file', 'output')
        expected = f'{fsl_mrs_proc} fixed_phase --file file --output output'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.fsl_mrs_proc.fixed_phase('file', 'output', p0=90, p1=0.001, p1_type='shift')
        expected = f'{fsl_mrs_proc} fixed_phase --file file --output output --p0 90 --p1 0.001 --p1_type shift'
        assert result.stdout[0] == expected


def test_fsl_mrs_proc_subtract():
    with testenv('fsl_mrs_proc') as fsl_mrs_proc:
        # test simple call
        result = fw.fsl_mrs_proc.subtract('file', 'output')
        expected = f'{fsl_mrs_proc} subtract --file file --output output'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.fsl_mrs_proc.subtract('file', 'output', reference='reference', dim='DIM_EDIT')
        expected = f'{fsl_mrs_proc} subtract --file file --output output --reference reference --dim DIM_EDIT'
        assert result.stdout[0] == expected


def test_fsl_mrs_proc_add():
    with testenv('fsl_mrs_proc') as fsl_mrs_proc:
        # test simple call
        result = fw.fsl_mrs_proc.add('file', 'output')
        expected = f'{fsl_mrs_proc} add --file file --output output'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.fsl_mrs_proc.add('file', 'output', reference='reference', dim='DIM_EDIT')
        expected = f'{fsl_mrs_proc} add --file file --output output --reference reference --dim DIM_EDIT'
        assert result.stdout[0] == expected


def test_fsl_mrs_proc_conj():
    with testenv('fsl_mrs_proc') as fsl_mrs_proc:
        # test simple call
        result = fw.fsl_mrs_proc.conj('file', 'output')
        expected = f'{fsl_mrs_proc} conj --file file --output output'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.fsl_mrs_proc.conj('file', 'output', filename='filename')
        expected = f'{fsl_mrs_proc} conj --file file --output output --filename filename'
        assert result.stdout[0] == expected


def test_fsl_mrs_proc_mrsi_align():
    with testenv('fsl_mrs_proc') as fsl_mrs_proc:
        # test simple call
        result = fw.fsl_mrs_proc.mrsi_align('file', 'output')
        expected = f'{fsl_mrs_proc} mrsi-align --file file --output output'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.fsl_mrs_proc.mrsi_align('file', 'output', target='target', mask='mask',
                                            zpad=1, save_params=True)
        expected = f'{fsl_mrs_proc} mrsi-align --file file --output output --target target'\
                    ' --mask mask --zpad 1 --save-params'
        assert result.stdout[0] == expected


def test_fsl_mrs_proc_mrsi_lipid():
    with testenv('fsl_mrs_proc') as fsl_mrs_proc:
        # test simple call
        result = fw.fsl_mrs_proc.mrsi_lipid('file', 'output')
        expected = f'{fsl_mrs_proc} mrsi-lipid --file file --output output'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.fsl_mrs_proc.mrsi_lipid('file', 'output', mask='mask', beta=1E-5)
        expected = f'{fsl_mrs_proc} mrsi-lipid --file file --output output --mask mask --beta 1e-05'
        assert result.stdout[0] == expected
