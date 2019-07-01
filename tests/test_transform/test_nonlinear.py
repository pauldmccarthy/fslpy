#!/usr/bin/env python

import itertools as it
import os.path   as op

import numpy   as np
import nibabel as nib

import fsl.data.image          as fslimage
import fsl.transform           as transform
import fsl.transform.nonlinear as nonlinear
import fsl.transform.fnirt     as fnirt


datadir = op.join(op.dirname(__file__), 'testdata')


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

def _random_affine_field():

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

    field    = np.zeros(list(ref.shape[:3]) + [3])
    field[:] = (scoords - rcoords).reshape(*it.chain(ref.shape, [3]))
    field    = nonlinear.DisplacementField(field, src, ref,
                                           header=ref.header,
                                           dispType='relative')
    return field, xform


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
        relfield.data + coords,
        src=relfield.src,
        xform=relfield.voxToWorldMat)

    assert nonlinear.detectDisplacementType(relfield) == 'relative'
    assert nonlinear.detectDisplacementType(absfield) == 'absolute'


def test_convertDisplacementType():

    relfield = _random_field()
    coords   = _field_coords(relfield)
    absfield = nonlinear.DisplacementField(
        relfield.data + coords,
        src=relfield.src,
        xform=relfield.voxToWorldMat)

    gotconvrel1 = nonlinear.convertDisplacementType(relfield)
    gotconvabs1 = nonlinear.convertDisplacementType(absfield)
    gotconvrel2 = nonlinear.convertDisplacementType(relfield, 'absolute')
    gotconvabs2 = nonlinear.convertDisplacementType(absfield, 'relative')

    tol = dict(atol=1e-5, rtol=1e-5)

    assert np.all(np.isclose(gotconvrel1, absfield.data, **tol))
    assert np.all(np.isclose(gotconvabs1, relfield.data, **tol))
    assert np.all(np.isclose(gotconvrel2, absfield.data, **tol))
    assert np.all(np.isclose(gotconvabs2, relfield.data, **tol))


def test_convertDisplacementSpace():

    basefield, xform = _random_affine_field()
    src              = basefield.src
    ref              = basefield.ref

    # generate reference fsl->fsl coordinate mappings

    # For each combination of srcspace->tospace
    # Generate random coordinates, check that
    # displacements are correct
    spaces = ['fsl', 'voxel', 'world']
    spaces = list(it.combinations_with_replacement(spaces, 2))
    spaces = spaces + [(r, s) for s, r in spaces]
    spaces = list(set(spaces))

    for from_, to in spaces:

        refcoords = [np.random.randint(0, basefield.shape[0], 5),
                     np.random.randint(0, basefield.shape[1], 5),
                     np.random.randint(0, basefield.shape[2], 5)]
        refcoords = np.array(refcoords, dtype=np.int).T
        refcoords = transform.transform(refcoords, ref.voxToScaledVoxMat)
        srccoords = basefield.transform(refcoords)

        field   = nonlinear.convertDisplacementSpace(basefield, from_, to)
        premat  = ref.getAffine('fsl', from_)
        postmat = src.getAffine('fsl', to)

        input  = transform.transform(refcoords, premat)
        expect = transform.transform(srccoords, postmat)

        got  = field.transform(input)
        enan = np.isnan(expect)
        gnan = np.isnan(got)

        assert np.all(np.isclose(enan, gnan))
        assert np.all(np.isclose(expect[~enan], got[~gnan]))


def test_DisplacementField_transform():

    relfield, xform = _random_affine_field()
    src             = relfield.src
    ref             = relfield.ref

    rx, ry, rz = np.meshgrid(np.arange(ref.shape[0]),
                             np.arange(ref.shape[1]),
                             np.arange(ref.shape[2]), indexing='ij')
    rvoxels  = np.vstack((rx.flatten(), ry.flatten(), rz.flatten())).T
    rcoords  = transform.transform(rvoxels, ref.voxToScaledVoxMat)
    scoords  = transform.transform(rcoords, xform)
    svoxels  = transform.transform(scoords, src.scaledVoxToVoxMat)

    absfield    = np.zeros(list(ref.shape[:3]) + [3])
    absfield[:] = scoords.reshape(*it.chain(ref.shape, [3]))
    absfield    = nonlinear.DisplacementField(absfield, src, ref,
                                              header=ref.header,
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

def test_coefficientFieldToDisplacementField():

    nldir = op.join(datadir, 'nonlinear')
    src   = op.join(nldir, 'src.nii.gz')
    ref   = op.join(nldir, 'ref.nii.gz')
    cf    = op.join(nldir, 'coefficientfield.nii.gz')
    df    = op.join(nldir, 'displacementfield.nii.gz')

    src   = fslimage.Image(src)
    ref   = fslimage.Image(ref)
    cf    = fnirt.readFnirt(cf, src, ref)
    rdf   = fnirt.readFnirt(df, src, ref)
    adf   = nonlinear.convertDisplacementType(rdf)

    tol = dict(atol=1e-5, rtol=1e-5)

    rcnv = nonlinear.coefficientFieldToDisplacementField(cf)
    acnv = nonlinear.coefficientFieldToDisplacementField(cf, dispType='absolute')

    assert np.all(np.isclose(rcnv.data, rdf.data, **tol))
    assert np.all(np.isclose(acnv.data, adf.data, **tol))
