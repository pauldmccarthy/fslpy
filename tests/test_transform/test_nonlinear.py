#!/usr/bin/env python

import itertools as it

import numpy   as np
import nibabel as nib

import fsl.data.image          as fslimage
import fsl.transform           as transform
import fsl.transform.nonlinear as nonlinear


def _random_image():
    vx, vy, vz = np.random.randint(10, 50, 3)
    dx, dy, dz = np.random.randint( 1, 10, 3)
    data       = (np.random.random((vx, vy, vz)) - 0.5) * 10
    aff        = transform.compose(
        (dx, dy, dz),
        np.random.randint(1, 100, 3),
        np.random.random(3) * np.pi / 2)

    return fslimage.Image(data, xform=aff)


def _random_field():

    src        = _random_image()
    vx, vy, vz = np.random.randint(10, 50, 3)
    dx, dy, dz = np.random.randint( 1, 10, 3)

    field = (np.random.random((vx, vy, vz, 3)) - 0.5) * 10
    aff   = transform.compose(
        (dx, dy, dz),
        np.random.randint(1, 100, 3),
        np.random.random(3) * np.pi / 2)

    return nonlinear.DisplacementField(field, src=src, xform=aff)


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

def test_DisplacementField_transform():

    src = _random_image()
    ref = _random_image()

    # our test field just encodes an affine
    xform = transform.compose(
        np.random.randint(2, 5, 3),
        np.random.randint(1, 10, 3),
        np.random.random(3))

    rx, ry, rz = np.meshgrid(np.arange(ref.shape[0]),
                             np.arange(ref.shape[1]),
                             np.arange(ref.shape[2]), indexing='ij')

    rvoxels  = np.vstack((rx.flatten(), ry.flatten(), rz.flatten())).T
    rcoords  = transform.transform(rvoxels, ref.voxToScaledVoxMat)
    scoords  = transform.transform(rcoords, xform)
    svoxels  = transform.transform(scoords, src.scaledVoxToVoxMat)

    relfield    = np.zeros(list(ref.shape[:3]) + [3])
    relfield[:] = (scoords - rcoords).reshape(*it.chain(ref.shape, [3]))
    relfield    = nonlinear.DisplacementField(relfield, src, ref,
                                              dispType='relative')
    absfield    = np.zeros(list(ref.shape[:3]) + [3])
    absfield[:] = scoords.reshape(*it.chain(ref.shape, [3]))
    absfield    = nonlinear.DisplacementField(absfield, src, ref,
                                              dispType='absolute')

    got = relfield.transform(rcoords)
    assert np.all(np.isclose(got, scoords))
    got = absfield.transform(rcoords)
    assert np.all(np.isclose(got, scoords))

    got = relfield.transform(rvoxels, from_='voxel', to='voxel')
    assert np.all(np.isclose(got, svoxels))
    got = absfield.transform(rvoxels, from_='voxel', to='voxel')
    assert np.all(np.isclose(got, svoxels))

    # test out of bounds are returned as nan
    rvoxels = np.array([[-1, -1, -1],
                        [ 0,  0,  0]])
    rcoords  = transform.transform(rvoxels, ref.voxToScaledVoxMat)
    scoords  = transform.transform(rcoords, xform)
    svoxels  = transform.transform(scoords, src.scaledVoxToVoxMat)

    got = relfield.transform(rcoords)
    assert np.all(np.isnan(got[0, :]))
    assert np.all(np.isclose(got[1, :], scoords[1, :]))
    got = absfield.transform(rcoords)
    assert np.all(np.isnan(got[0, :]))
    assert np.all(np.isclose(got[1, :], scoords[1, :]))
