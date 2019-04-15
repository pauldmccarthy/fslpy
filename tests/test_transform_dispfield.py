#!/usr/bin/env python


import numpy   as np
import nibabel as nib

import fsl.data.image                as fslimage
import fsl.utils.transform           as transform
import fsl.utils.transform.dispfield as dispfield


def _random_field():
    vx, vy, vz = np.random.randint(10, 50, 3)
    dx, dy, dz = np.random.randint( 1, 10, 3)

    field = (np.random.random((vx, vy, vz, 3)) - 0.5) * 10
    aff   = transform.compose(
        (dx, dy, dz),
        np.random.randint(1, 100, 3),
        np.random.random(3) * np.pi / 2)

    return dispfield.DisplacementField(field, xform=aff)


def _field_coords(field):
    vx, vy, vz = field.shape[ :3]
    coords     = np.meshgrid(np.arange(vx),
                             np.arange(vy),
                             np.arange(vz), indexing='ij')
    coords = np.array(coords).transpose((1, 2, 3, 0))
    return transform.transform(
        coords.reshape(-1, 3),
        field.getAffine('voxel', 'fsl')).reshape(field.shape)


def test_detectType():
    relfield = _random_field()
    coords   = _field_coords(relfield)
    absfield = dispfield.DisplacementField(
        relfield.data + coords, xform=relfield.voxToWorldMat)

    assert dispfield.detectType(relfield) == 'relative'
    assert dispfield.detectType(absfield) == 'absolute'


def test_convertType():
    relfield = dispfield.DisplacementField(_random_field())
    coords   = _field_coords(relfield)
    absfield = fslimage.Image(
        relfield.data + coords, xform=relfield.voxToWorldMat)

    relfield = dispfield.DisplacementField(relfield)
    absfield = dispfield.DisplacementField(absfield)

    gotconvrel1 = dispfield.convertType(relfield)
    gotconvabs1 = dispfield.convertType(absfield)
    gotconvrel2 = dispfield.convertType(relfield, 'absolute')
    gotconvabs2 = dispfield.convertType(absfield, 'relative')

    assert np.all(np.isclose(gotconvrel1, absfield.data))
    assert np.all(np.isclose(gotconvabs1, relfield.data))
    assert np.all(np.isclose(gotconvrel2, absfield.data))
    assert np.all(np.isclose(gotconvabs2, relfield.data))
