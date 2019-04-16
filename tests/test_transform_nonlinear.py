#!/usr/bin/env python


import numpy   as np
import nibabel as nib

import fsl.data.image                as fslimage
import fsl.utils.transform           as transform
import fsl.utils.transform.nonlinear as nonlinear


def _random_field():
    vx, vy, vz = np.random.randint(10, 50, 3)
    dx, dy, dz = np.random.randint( 1, 10, 3)

    field = (np.random.random((vx, vy, vz, 3)) - 0.5) * 10
    aff   = transform.compose(
        (dx, dy, dz),
        np.random.randint(1, 100, 3),
        np.random.random(3) * np.pi / 2)

    return nonlinear.DisplacementField(field, xform=aff)


def _field_coords(field):
    vx, vy, vz = field.shape[ :3]
    coords     = np.meshgrid(np.arange(vx),
                             np.arange(vy),
                             np.arange(vz), indexing='ij')
    coords = np.array(coords).transpose((1, 2, 3, 0))
    return transform.transform(
        coords.reshape(-1, 3),
        field.getAffine('voxel', 'fsl')).reshape(field.shape)


def test_detectDisplacementType():
    relfield = _random_field()
    coords   = _field_coords(relfield)
    absfield = nonlinear.DisplacementField(
        relfield.data + coords, xform=relfield.voxToWorldMat)

    assert nonlinear.detectDisplacementType(relfield) == 'relative'
    assert nonlinear.detectDisplacementType(absfield) == 'absolute'


def test_convertDisplacemenyType():
    relfield = nonlinear.DisplacementField(_random_field())
    coords   = _field_coords(relfield)
    absfield = fslimage.Image(
        relfield.data + coords, xform=relfield.voxToWorldMat)

    relfield = nonlinear.DisplacementField(relfield)
    absfield = nonlinear.DisplacementField(absfield)

    gotconvrel1 = nonlinear.convertDisplacementType(relfield)
    gotconvabs1 = nonlinear.convertDisplacementType(absfield)
    gotconvrel2 = nonlinear.convertDisplacementType(relfield, 'absolute')
    gotconvabs2 = nonlinear.convertDisplacementType(absfield, 'relative')

    assert np.all(np.isclose(gotconvrel1, absfield.data))
    assert np.all(np.isclose(gotconvabs1, relfield.data))
    assert np.all(np.isclose(gotconvrel2, absfield.data))
    assert np.all(np.isclose(gotconvabs2, relfield.data))
