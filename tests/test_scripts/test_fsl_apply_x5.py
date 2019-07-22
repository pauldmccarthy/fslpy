#!/usr/bin/env python


import numpy as np

import fsl.scripts.fsl_apply_x5 as fsl_apply_x5
import fsl.data.image           as fslimage
import fsl.utils.image.resample as resample
import fsl.transform.x5         as x5
import fsl.transform.affine     as affine
import fsl.utils.tempdir        as tempdir

from ..test_transform.test_nonlinear import _affine_field


def _random_affine():
    return affine.compose(
        np.random.randint(2, 5, 3),
        np.random.randint(1, 10, 3),
        np.random.random(3))


def _random_image(aff):
    vx, vy, vz = np.random.randint(10, 50, 3)
    data       = (np.random.random((vx, vy, vz)) - 0.5) * 10
    return fslimage.Image(data, xform=aff)


def test_linear():
    with tempdir.tempdir():

        src2ref = _random_affine()
        src     = _random_image(np.eye(4))
        ref     = _random_image(src2ref)

        x5.writeLinearX5('xform.x5', src2ref, src, ref)

        src.save('src')
        ref.save('ref')

        fsl_apply_x5.main('src xform.x5 out'.split())

        result = fslimage.Image('out')
        expect = resample.resampleToReference(src, ref, matrix=src2ref)[0]

        assert result.sameSpace(ref)
        assert np.all(np.isclose(result.data, expect))


def test_nonlinear():
    with tempdir.tempdir():

        src2ref = _random_affine()
        ref2src = affine.invert(src2ref)
        src     = _random_image(np.eye(4))
        ref     = _random_image(src2ref)
        field   = _affine_field(src, ref, ref2src, 'world', 'world')

        x5.writeNonLinearX5('xform.x5', field)

        src.save('src')

        fsl_apply_x5.main('src xform.x5 out'.split())

        result = fslimage.Image('out')
        expect = resample.resampleToReference(src, ref, matrix=src2ref)[0]

        assert result.sameSpace(ref)

        # We might get truncation on the edges
        result = result.data[1:-1, 1:-1, 1:-1]
        expect = expect[     1:-1, 1:-1, 1:-1]

        assert np.all(np.isclose(result, expect))


def test_linear_altref():
    with tempdir.tempdir():

        src2ref = affine.scaleOffsetXform([1, 1, 1], [5,  5,  5])
        altv2w  = affine.scaleOffsetXform([1, 1, 1], [10, 10, 10])

        srcdata = np.random.randint(1, 65536, (10, 10, 10))
        src     = fslimage.Image(srcdata,  xform=np.eye(4))
        ref     = fslimage.Image(src.data, xform=src2ref)
        altref  = fslimage.Image(src.data, xform=altv2w)

        src   .save('src')
        ref   .save('ref')
        altref.save('altref')

        x5.writeLinearX5('xform.x5', src2ref, src, ref)

        fsl_apply_x5.main('src xform.x5 out -r altref'.split())

        result = fslimage.Image('out')
        expect = np.zeros(srcdata.shape)
        expect[:5, :5, :5] = srcdata[5:, 5:, 5:]

        assert result.sameSpace(altref)
        assert np.all(result.data == expect)


def test_nonlinear_altref():
    with tempdir.tempdir():

        src2ref = affine.scaleOffsetXform([1, 1, 1], [5,  5,  5])
        ref2src = affine.invert(src2ref)
        altv2w  = affine.scaleOffsetXform([1, 1, 1], [10, 10, 10])

        srcdata = np.random.randint(1, 65536, (10, 10, 10))
        src     = fslimage.Image(srcdata,  xform=np.eye(4))
        ref     = fslimage.Image(src.data, xform=src2ref)
        altref  = fslimage.Image(src.data, xform=altv2w)

        field   = _affine_field(src, ref, ref2src, 'world', 'world')

        src   .save('src')
        ref   .save('ref')
        altref.save('altref')

        x5.writeNonLinearX5('xform.x5', field)

        fsl_apply_x5.main('src xform.x5 out -r altref'.split())

        result = fslimage.Image('out')
        expect = np.zeros(srcdata.shape)
        expect[:5, :5, :5] = srcdata[5:, 5:, 5:]

        assert result.sameSpace(altref)
        assert np.all(result.data == expect)
