#!/usr/bin/env python


import numpy as np

import pytest

import fsl.scripts.fsl_apply_x5 as fsl_apply_x5
import fsl.data.image           as fslimage
import fsl.utils.image.resample as resample
import fsl.utils.image.roi      as roi
import fsl.transform.x5         as x5
import fsl.transform.affine     as affine
import fsl.utils.tempdir        as tempdir

from ..test_transform.test_nonlinear import _affine_field


def _random_affine():
    return affine.compose(
        np.random.randint(2, 5, 3),
        np.random.randint(1, 10, 3),
        np.random.random(3))


def _random_image(aff, shape=None):

    if shape is None:
        shape = np.random.randint(10, 50, 3)

    data = (np.random.random(shape) - 0.5) * 10

    return fslimage.Image(data, xform=aff)


def test_help():
    def run(args):
        with pytest.raises(SystemExit) as e:
            fsl_apply_x5.main(args)
        assert e.value.code == 0

    run([])
    run(['-h'])



def test_linear(seed):
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


def test_nonlinear(seed):
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
        expect = resample.resampleToReference(src, ref, matrix=src2ref, smooth=False)[0]

        assert result.sameSpace(ref)

        # We might get truncation on the edges
        result = result.data[1:-1, 1:-1, 1:-1]
        expect = expect[     1:-1, 1:-1, 1:-1]

        tol = dict(atol=1e-3, rtol=1e-3)
        assert np.all(np.isclose(result, expect, **tol))


def test_linear_altref(seed):
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


def test_nonlinear_altref(seed):
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


def test_linear_altsrc(seed):
    with tempdir.tempdir():

        src2ref = _random_affine()
        src     = _random_image(np.eye(4), (20, 20, 20))
        ref     = _random_image(src2ref)

        x5.writeLinearX5('xform.x5', src2ref, src, ref)

        src.save('src')
        ref.save('ref')

        srclo, xf = resample.resample(src, (10, 10, 10))
        srclo = fslimage.Image(srclo, xform=xf)
        srchi, xf = resample.resample(src, (40, 40, 40))
        srchi = fslimage.Image(srchi, xform=xf)

        srcoff = roi.roi(src, [(-10, 10), (-10, 10), (-10, 10)])

        srclo .save('srclo')
        srchi .save('srchi')
        srcoff.save('srcoff')

        fsl_apply_x5.main('src    xform.x5 out'   .split())
        fsl_apply_x5.main('srclo  xform.x5 outlo' .split())
        fsl_apply_x5.main('srchi  xform.x5 outhi' .split())
        fsl_apply_x5.main('srcoff xform.x5 outoff'.split())

        out    = fslimage.Image('out')
        outlo  = fslimage.Image('outlo')
        outhi  = fslimage.Image('outhi')
        outoff = fslimage.Image('outoff')

        exp    = resample.resampleToReference(src,    ref, matrix=src2ref)[0]
        explo  = resample.resampleToReference(srclo,  ref, matrix=src2ref)[0]
        exphi  = resample.resampleToReference(srchi,  ref, matrix=src2ref)[0]
        expoff = resample.resampleToReference(srcoff, ref, matrix=src2ref)[0]

        assert out   .sameSpace(ref)
        assert outlo .sameSpace(ref)
        assert outhi .sameSpace(ref)
        assert outoff.sameSpace(ref)

        assert np.all(np.isclose(out   .data, exp))
        assert np.all(np.isclose(outlo .data, explo))
        assert np.all(np.isclose(outhi .data, exphi))
        assert np.all(np.isclose(outoff.data, expoff))


def test_nonlinear_altsrc(seed):
    with tempdir.tempdir():

        src2ref = _random_affine()
        ref2src = affine.invert(src2ref)
        src     = _random_image(np.eye(4), (20, 20, 20))
        ref     = _random_image(src2ref,   (20, 20, 20))

        field   = _affine_field(src, ref, ref2src, 'world', 'world')

        x5.writeNonLinearX5('xform.x5', field)

        src.save('src')
        ref.save('ref')

        # use origin=corner so that the
        # resampled variants are exactly
        # aligned in the world coordinate
        # system
        srclo, xf = resample.resample(src, (10, 10, 10), origin='corner', smooth=False)
        srclo = fslimage.Image(srclo, xform=xf)
        srchi, xf = resample.resample(src, (40, 40, 40), origin='corner', smooth=False)
        srchi = fslimage.Image(srchi, xform=xf)

        srcoff = roi.roi(src, [(-10, 10), (-10, 10), (-10, 10)])

        srclo .save('srclo')
        srchi .save('srchi')
        srcoff.save('srcoff')

        fsl_apply_x5.main('src    xform.x5 out'   .split())
        fsl_apply_x5.main('srclo  xform.x5 outlo' .split())
        fsl_apply_x5.main('srchi  xform.x5 outhi' .split())
        fsl_apply_x5.main('srcoff xform.x5 outoff'.split())

        out    = fslimage.Image('out')
        outlo  = fslimage.Image('outlo')
        outhi  = fslimage.Image('outhi')
        outoff = fslimage.Image('outoff')

        exp,    x1 = resample.resampleToReference(src,    ref, matrix=src2ref, mode='constant', smooth=False)
        explo,  x2 = resample.resampleToReference(srclo,  ref, matrix=src2ref, mode='constant', smooth=False)
        exphi,  x3 = resample.resampleToReference(srchi,  ref, matrix=src2ref, mode='constant', smooth=False)
        expoff, x4 = resample.resampleToReference(srcoff, ref, matrix=src2ref, mode='constant', smooth=False)

        assert out   .sameSpace(ref)
        assert outlo .sameSpace(ref)
        assert outhi .sameSpace(ref)
        assert outoff.sameSpace(ref)

        # We get boundary cropping,
        # so ignore edge slices
        out    = out   .data[1:-1, 1:-1, 1:-1]
        outlo  = outlo .data[1:-1, 1:-1, 1:-1]
        outhi  = outhi .data[1:-1, 1:-1, 1:-1]
        outoff = outoff.data[ :9,   :9,   :9]
        exp    = exp[        1:-1, 1:-1, 1:-1]
        explo  = explo[      1:-1, 1:-1, 1:-1]
        exphi  = exphi[      1:-1, 1:-1, 1:-1]
        expoff = expoff[      :9,   :9,   :9]

        tol = dict(atol=1e-3, rtol=1e-3)

        assert np.all(np.isclose(out,    exp,   **tol))
        assert np.all(np.isclose(outlo,  explo, **tol))
        assert np.all(np.isclose(outhi,  exphi, **tol))
        assert np.all(np.isclose(outoff, expoff, **tol))
