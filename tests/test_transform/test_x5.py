#!/usr/bin/env python
#
# test_x5.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path as op
import numpy as np

import h5py

import fsl.data.image          as fslimage
import fsl.utils.tempdir       as tempdir
import fsl.transform.affine    as affine
import fsl.transform.fnirt     as fnirt
import fsl.transform.nonlinear as nonlinear
import fsl.transform.x5        as x5

from .. import make_random_image


def _check_metadata(group):
    assert group.attrs['Format']  == x5.X5_FORMAT
    assert group.attrs['Version'] == x5.X5_VERSION


def _check_affine(group, xform):
    assert group.attrs['Type'] == 'linear'
    gotxform = np.array(group['Transform'])
    assert np.all(np.isclose(gotxform, xform))


def _check_space(group, img):
    assert group.attrs['Type'] == 'image'
    assert np.all(np.isclose(group.attrs['Size'],   img.shape[ :3]))
    assert np.all(np.isclose(group.attrs['Scales'], img.pixdim[:3]))
    _check_affine(group['Mapping'], img.voxToWorldMat)


def _check_nonlinear_common(group, field):
    assert group.attrs['Type'] == 'nonlinear'

    if isinstance(field, nonlinear.DisplacementField):
        assert group.attrs['SubType']        == 'displacement'
        assert group.attrs['Representation'] == field.displacementType

    elif isinstance(field, nonlinear.CoefficientField):
        assert group.attrs['SubType'] == 'coefficient'
        if field.fieldType == 'cubic':
            assert group.attrs['Representation'] == 'cubic bspline'
        elif field.fieldType == 'quadratic':
            assert group.attrs['Representation'] == 'quadratic bspline'

    _check_space(group['From'], field.src)
    _check_space(group['To'],   field.ref)

    pre  = field.ref.getAffine('world', 'fsl')
    post = field.src.getAffine('fsl', 'world')

    _check_affine(group['Pre'],  pre)
    _check_affine(group['Post'], post)


def test_readWriteLinearX5():
    with tempdir.tempdir():
        make_random_image('src.nii')
        make_random_image('ref.nii')
        xform = affine.compose(
            np.random.randint(1, 5, 3),
            np.random.randint(-10, 10, 3),
            -np.pi / 4 + np.random.random(3) * np.pi / 2)

        src = fslimage.Image('src.nii')
        ref = fslimage.Image('ref.nii')

        x5.writeLinearX5('linear.x5', xform, src, ref)

        gotxform, gotsrc, gotref = x5.readLinearX5('linear.x5')
        assert np.all(np.isclose(gotxform, xform))
        assert gotsrc.sameSpace(src)
        assert gotref.sameSpace(ref)

        with h5py.File('linear.x5', 'r') as f:
            _check_metadata(f)
            _check_affine(f['/'],     xform)
            _check_space( f['/From'], src)
            _check_space( f['/To'],   ref)


def test_readWriteNonLinearX5_DisplacementField():
    datadir = op.join(op.dirname(__file__), 'testdata', 'nonlinear')
    dffile  = op.join(datadir, 'displacementfield.nii.gz')
    srcfile = op.join(datadir, 'src.nii.gz')
    reffile = op.join(datadir, 'ref.nii.gz')

    src = fslimage.Image(srcfile)
    ref = fslimage.Image(reffile)

    dfield = fnirt.readFnirt(dffile, src, ref)

    with tempdir.tempdir():
        x5.writeNonLinearX5('nonlinear.x5', dfield)

        gotdfield = x5.readNonLinearX5('nonlinear.x5')

        assert gotdfield.src.sameSpace(src)
        assert gotdfield.ref.sameSpace(ref)
        assert gotdfield.srcSpace == dfield.srcSpace
        assert gotdfield.refSpace == dfield.refSpace
        assert gotdfield.displacementType == dfield.displacementType
        assert np.all(np.isclose(gotdfield.data, dfield.data))

        with h5py.File('nonlinear.x5', 'r') as f:
            _check_metadata(f)
            _check_nonlinear_common(f['/'], dfield)

            xform = np.array(f['/Transform'])
            assert np.all(np.isclose(xform, dfield.data))



def test_readWriteNonLinearX5_CoefficientField():
    datadir = op.join(op.dirname(__file__), 'testdata', 'nonlinear')
    cffile  = op.join(datadir, 'coefficientfield.nii.gz')
    srcfile = op.join(datadir, 'src.nii.gz')
    reffile = op.join(datadir, 'ref.nii.gz')

    src = fslimage.Image(srcfile)
    ref = fslimage.Image(reffile)

    cfield = fnirt.readFnirt(cffile, src, ref)

    with tempdir.tempdir():
        x5.writeNonLinearX5('nonlinear.x5', cfield)

        gotcfield = x5.readNonLinearX5('nonlinear.x5')

        assert gotcfield.src.sameSpace(src)
        assert gotcfield.ref.sameSpace(ref)
        assert gotcfield.srcSpace    == cfield.srcSpace
        assert gotcfield.refSpace    == cfield.refSpace
        assert gotcfield.knotSpacing == cfield.knotSpacing

        assert np.all(np.isclose(gotcfield.fieldToRefMat, cfield.fieldToRefMat))
        assert np.all(np.isclose(gotcfield.srcToRefMat,   cfield.srcToRefMat))
        assert np.all(np.isclose(gotcfield.data,          cfield.data))

        with h5py.File('nonlinear.x5', 'r') as f:
            _check_metadata(f)
            _check_nonlinear_common(f['/'], cfield)

            _check_affine(f['/InitialAlignment'], cfield.srcToRefMat)
            _check_affine(f['/Parameters/ReferenceToField'], cfield.refToFieldMat)
            assert np.all(np.isclose(f['/Parameters'].attrs['Spacing'], cfield.knotSpacing))
