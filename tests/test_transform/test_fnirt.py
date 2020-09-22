#!/usr/bin/env python
#
# test_fnirt.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op
import itertools as it

import numpy as np
import nibabel as nib

import pytest

import fsl.data.image          as fslimage
import fsl.utils.tempdir       as tempdir
import fsl.data.constants      as constants
import fsl.transform.affine    as affine
import fsl.transform.nonlinear as nonlinear
import fsl.transform.fnirt     as fnirt

from .test_nonlinear import _random_affine_field


datadir = op.join(op.dirname(__file__), 'testdata', 'nonlinear')


def test_readFnirt():

    src  = op.join(datadir, 'src')
    ref  = op.join(datadir, 'ref')
    coef = op.join(datadir, 'coefficientfield')
    disp = op.join(datadir, 'displacementfield')

    src  = fslimage.Image(src)
    ref  = fslimage.Image(ref)
    coef = fnirt.readFnirt(coef, src, ref)
    disp = fnirt.readFnirt(disp, src, ref)

    with pytest.raises(ValueError):
        fnirt.readFnirt(src, src, ref)

    assert isinstance(coef, nonlinear.CoefficientField)
    assert isinstance(disp, nonlinear.DeformationField)

    assert coef.src.sameSpace(src)
    assert coef.ref.sameSpace(ref)
    assert disp.src.sameSpace(src)
    assert disp.ref.sameSpace(ref)
    assert coef.srcSpace == 'fsl'
    assert coef.refSpace == 'fsl'
    assert disp.srcSpace == 'fsl'
    assert disp.refSpace == 'fsl'


def test_readFnirt_defType_intent():
    src  = op.join(datadir, 'src.nii.gz')
    ref  = op.join(datadir, 'ref.nii.gz')
    coef = op.join(datadir, 'coefficientfield.nii.gz')
    disp = op.join(datadir, 'displacementfield.nii.gz')

    src  = fslimage.Image(src)
    ref  = fslimage.Image(ref)

    field = fnirt.readFnirt(disp, src, ref, defType='absolute')
    assert field.deformationType == 'absolute'
    field = fnirt.readFnirt(disp, src, ref, defType='relative')
    assert field.deformationType == 'relative'

    img = nib.load(coef)
    img.header['intent_code'] = 0
    with tempdir.tempdir():
        img.to_filename('field.nii.gz')

        with pytest.raises(ValueError):
            fnirt.readFnirt('field', src, ref)

        field = fnirt.readFnirt(
            'field', src, ref,
            intent=constants.FSL_CUBIC_SPLINE_COEFFICIENTS)
        assert isinstance(field, nonlinear.CoefficientField)

        field = fnirt.readFnirt(
            'field', src, ref,
            intent=constants.FSL_FNIRT_DISPLACEMENT_FIELD)
        assert isinstance(field, nonlinear.DeformationField)


def test_toFnirt():

    def check(got, exp):
        tol = dict(atol=1e-5, rtol=1e-5)
        assert np.all(np.isclose(got.data, exp.data, **tol))
        assert got.src.sameSpace(exp.src)
        assert got.ref.sameSpace(exp.ref)
        assert got.srcSpace == 'fsl'
        assert got.refSpace == 'fsl'

    basefield, xform = _random_affine_field()
    src = basefield.src
    ref = basefield.ref

    spaces = it.permutations(('voxel', 'fsl', 'world'), 2)

    for from_, to in spaces:
        field = nonlinear.convertDeformationSpace(basefield, from_, to)
        got = fnirt.toFnirt(field)
        check(got, basefield)

    src  = fslimage.Image(op.join(datadir, 'src'))
    ref  = fslimage.Image(op.join(datadir, 'ref'))
    coef = fnirt.readFnirt(op.join(datadir, 'coefficientfield'),  src, ref)
    got  = fnirt.toFnirt(coef)
    check(got, coef)


def test_fromFnirt():

    basefield, basexform = _random_affine_field()
    src = basefield.src
    ref = basefield.ref
    spaces = list(it.permutations(('voxel', 'fsl', 'world'), 2))

    for from_, to in spaces:

        got = fnirt.fromFnirt(basefield, from_, to)

        assert got.srcSpace == to
        assert got.refSpace == from_

        coords = [np.random.randint(0, basefield.shape[0], 5),
                  np.random.randint(0, basefield.shape[1], 5),
                  np.random.randint(0, basefield.shape[2], 5)]
        coords = np.array(coords).T

        coords = affine.transform(coords, ref.getAffine('voxel', from_))

        aff = affine.concat(src.getAffine('fsl', to),
                            basexform,
                            ref.getAffine(from_, 'fsl'))

        got = got.transform(coords)
        exp = affine.transform(coords, aff)

        enan = np.isnan(exp)
        gnan = np.isnan(got)

        assert np.all(np.isclose(enan, gnan))
        assert np.all(np.isclose(exp[~enan], got[~gnan]))

    # Converting from a FNIRT coefficient field
    src  = fslimage.Image(op.join(datadir, 'src'))
    ref  = fslimage.Image(op.join(datadir, 'ref'))
    coef = fnirt.readFnirt(op.join(datadir, 'coefficientfield'),  src, ref)
    disp = fnirt.readFnirt(op.join(datadir, 'displacementfield'), src, ref)

    for from_, to in spaces:

        cnv = fnirt.fromFnirt(coef, from_, to)
        exp = nonlinear.convertDeformationSpace(disp, from_, to)
        tol = dict(atol=1e-5, rtol=1e-5)
        assert np.all(np.isclose(cnv.data, exp.data, **tol))
