#!/usr/bin/env python
#
# test_fsl_mrs.py -
#
# Author: Vasilis Karlaftis <vasilis.karlaftis@ndcn.ox.ac.uk>
#

import pytest

import fsl.wrappers as fw
from fsl.tests.test_wrappers import testenv


pytestmark = pytest.mark.mrstest


def test_fsl_mrs():
    with testenv('fsl_mrs') as fsl_mrs:
        # test simple call
        result = fw.fsl_mrs('data', 'basis', 'output')
        expected = f'{fsl_mrs} --data data --output output --basis basis'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.fsl_mrs('data', 'basis', 'output', h2o='h2o', tissue_frac='segmentation.json', overwrite=True, config='fit_config.txt')
        expected = f'{fsl_mrs} --data data --output output --basis basis --h2o h2o --tissue_frac segmentation.json --overwrite --config fit_config.txt'
        assert result.stdout[0] == expected


def test_fsl_mrsi():
    with testenv('fsl_mrsi') as fsl_mrsi:
        # test simple call
        result = fw.fsl_mrsi('data', 'basis', 'output')
        expected = f'{fsl_mrsi} --data data --output output --basis basis'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.fsl_mrsi('data', 'basis', 'output', h2o='h2o', tissue_frac='segmentation.json', overwrite=True, config='fit_config.txt')
        expected = f'{fsl_mrsi} --data data --output output --basis basis --h2o h2o --tissue_frac segmentation.json --overwrite --config fit_config.txt'
        assert result.stdout[0] == expected


def test_fsl_mrs_preproc():
    with testenv('fsl_mrs_preproc') as fsl_mrs_preproc:
        # test simple call
        result = fw.fsl_mrs_preproc('data', 'reference', 'output')
        expected = f'{fsl_mrs_preproc} --data data --reference reference --output output'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.fsl_mrs_preproc('data', 'reference', 'output', quant='quant', truncate_fid='1', remove_water=True, report=True, overwrite=True)
        expected = f'{fsl_mrs_preproc} --data data --reference reference --output output --quant quant --truncate-fid 1 --remove-water --report --overwrite'
        assert result.stdout[0] == expected


def test_fsl_mrs_preproc_edit():
    with testenv('fsl_mrs_preproc_edit') as fsl_mrs_preproc_edit:
        # test simple call
        result = fw.fsl_mrs_preproc_edit('data', 'reference', 'output')
        expected = f'{fsl_mrs_preproc_edit} --data data --reference reference --output output'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.fsl_mrs_preproc_edit('data', 'reference', 'output', quant='quant', truncate_fid='1', remove_water=True, report=True, overwrite=True)
        expected = f'{fsl_mrs_preproc_edit} --data data --reference reference --output output --quant quant --truncate-fid 1 --remove-water --report --overwrite'
        assert result.stdout[0] == expected


def test_svs_segment():
    with testenv('svs_segment') as svs_segment:
        # test simple call
        result = fw.svs_segment('svs')
        expected = f'{svs_segment} svs'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.svs_segment('svs', anat='anat', output='output')
        expected = f'{svs_segment} svs --anat anat --output output'
        assert result.stdout[0] == expected

        # same call but with single dashed arguments
        result = fw.svs_segment('svs', a='anat', o='output')
        expected = f'{svs_segment} svs --anat anat --output output'
        assert result.stdout[0] == expected


def test_mrsi_segment():
    with testenv('mrsi_segment') as mrsi_segment:
        # test simple call
        result = fw.mrsi_segment('mrsi')
        expected = f'{mrsi_segment} mrsi'
        assert result.stdout[0] == expected

        # test more complex and common call
        result = fw.mrsi_segment('mrsi', anat='anat', output='output')
        expected = f'{mrsi_segment} mrsi --anat anat --output output'
        assert result.stdout[0] == expected

        # same call but with single dashed arguments
        result = fw.mrsi_segment('mrsi', a='anat', o='output')
        expected = f'{mrsi_segment} mrsi --anat anat --output output'
        assert result.stdout[0] == expected
