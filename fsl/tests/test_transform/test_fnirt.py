#!/usr/bin/env python
#
# test_fnirt.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os
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
import fsl.wrappers            as fslwrappers

from fsl.tests.test_transform.test_nonlinear import _random_affine_field


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

        # A 4D, 3-volume image with no intent
        # is read as a deformation field
        field = fnirt.readFnirt('field', src, ref)
        assert isinstance(field, nonlinear.DeformationField)

        field = fnirt.readFnirt(
            'field', src, ref,
            intent=constants.FSL_CUBIC_SPLINE_COEFFICIENTS)
        assert isinstance(field, nonlinear.CoefficientField)

        field = fnirt.readFnirt(
            'field', src, ref,
            intent=constants.FSL_FNIRT_DISPLACEMENT_FIELD)
        assert isinstance(field, nonlinear.DeformationField)


def test_readFnirt_intent_none():

    # FSL tools such as convertwarp save deformation fields with no
    # intent code. FSL reads any 4D, 3-volume image with an intent it
    # does not recognise as a deformation field, and decides whether
    # it is absolute or relative from the data unless told otherwise.
    src     = fslimage.Image(op.join(datadir, 'src'))
    ref     = fslimage.Image(op.join(datadir, 'ref'))
    rel     = fnirt.readFnirt(op.join(datadir, 'displacementfield'),
                              src, ref, defType='relative')
    absdata = nonlinear.convertDeformationType(rel, 'absolute')

    def save(data, fname):
        img = nib.Nifti1Image(data, None, rel.header)
        img.header['intent_code'] = constants.NIFTI_INTENT_NONE
        img.to_filename(fname)

    with tempdir.tempdir():
        save(rel.data, 'rel.nii.gz')
        save(absdata,  'abs.nii.gz')
        save(rel.data[..., 0], 'notafield.nii.gz')

        gotrel = fnirt.readFnirt('rel', src, ref)
        gotabs = fnirt.readFnirt('abs', src, ref)

        assert isinstance(gotrel, nonlinear.DeformationField)
        assert isinstance(gotabs, nonlinear.DeformationField)
        assert gotrel.deformationType == 'relative'
        assert gotabs.deformationType == 'absolute'
        assert np.all(np.isclose(gotrel.data, rel.data))
        assert np.all(np.isclose(gotabs.data, absdata, atol=1e-4))

        # The caller can override the guess
        got = fnirt.readFnirt('abs', src, ref, defType='relative')
        assert got.deformationType == 'relative'

        with pytest.raises(ValueError):
            fnirt.readFnirt('notafield', src, ref)


@pytest.mark.fsltest
@pytest.mark.skipif(os.environ.get('FSLDIR') is None,
                    reason='FSLDIR is not set')
def test_readFnirt_convertwarp_output():

    # readFnirt should open the output of convertwarp, which has
    # no intent code, whether it contains absolute or relative warps
    src  = fslimage.Image(op.join(datadir, 'src'))
    ref  = fslimage.Image(op.join(datadir, 'ref'))
    disp = op.join(datadir, 'displacementfield')
    rel  = fnirt.readFnirt(disp, src, ref, defType='relative')

    with tempdir.tempdir():
        fslwrappers.convertwarp('relout', ref, warp1=disp, relout=True)
        fslwrappers.convertwarp('absout', ref, warp1=disp, absout=True)

        assert nib.load('relout.nii.gz').header['intent_code'] == 0
        assert nib.load('absout.nii.gz').header['intent_code'] == 0

        relout = fnirt.readFnirt('relout', src, ref)
        absout = fnirt.readFnirt('absout', src, ref)

        assert relout.deformationType == 'relative'
        assert absout.deformationType == 'absolute'

        tol = dict(atol=1e-3)
        assert np.all(np.isclose(relout.data, rel.data, **tol))
        assert np.all(np.isclose(
            nonlinear.convertDeformationType(absout, 'relative'),
            rel.data, **tol))


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
