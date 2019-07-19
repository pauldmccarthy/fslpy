#!/usr/bin/env python
#
# test_x5.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path as op
import numpy as np

import pytest

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
    assert group.attrs['Type'] == 'affine'
    gotxform = np.array(group['Matrix'])
    assert np.all(np.isclose(gotxform, xform))


def _check_space(group, img):
    assert group.attrs['Type'] == 'image'
    assert np.all(np.isclose(group.attrs['Size'],   img.shape[ :3]))
    assert np.all(np.isclose(group.attrs['Scales'], img.pixdim[:3]))
    _check_affine(group['Mapping'], img.voxToWorldMat)


def _check_deformation(group, field):
    assert group.attrs['Type'] == 'deformation'
    assert group.attrs['SubType'] == field.deformationType
    xform = np.array(group['Matrix'])
    assert np.all(np.isclose(xform, field.data))
    _check_affine(group['Mapping'], field.voxToWorldMat)


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
            assert f.attrs['Type'] == 'linear'
            _check_affine(f['/Transform'], xform)
            _check_space( f['/A'],         src)
            _check_space( f['/B'],         ref)


def test_readWriteNonLinearX5():
    datadir = op.join(op.dirname(__file__), 'testdata', 'nonlinear')
    dffile  = op.join(datadir, 'displacementfield.nii.gz')
    srcfile = op.join(datadir, 'src.nii.gz')
    reffile = op.join(datadir, 'ref.nii.gz')

    src     = fslimage.Image(srcfile)
    ref     = fslimage.Image(reffile)
    dfield  = fnirt.readFnirt(dffile, src, ref)
    wdfield = nonlinear.convertDeformationSpace(dfield, 'world', 'world')

    with tempdir.tempdir():

        # field must be world->world
        with pytest.raises(x5.X5Error):
            x5.writeNonLinearX5('nonlinear.x5', dfield)

        x5.writeNonLinearX5('nonlinear.x5', wdfield)

        gotdfield = x5.readNonLinearX5('nonlinear.x5')

        assert gotdfield.src.sameSpace(src)
        assert gotdfield.ref.sameSpace(ref)
        assert gotdfield.srcSpace == wdfield.srcSpace
        assert gotdfield.refSpace == wdfield.refSpace
        assert gotdfield.deformationType == wdfield.deformationType
        assert np.all(np.isclose(gotdfield.data, wdfield.data))

        with h5py.File('nonlinear.x5', 'r') as f:
            assert f.attrs['Type'] == 'nonlinear'
            _check_metadata(f)
            _check_deformation(f['/Transform'], wdfield)
            _check_space(      f['/A'],         ref)
            _check_space(      f['/B'],         src)
