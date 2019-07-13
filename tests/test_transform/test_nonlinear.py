#!/usr/bin/env python

import itertools as it
import os.path   as op

import numpy   as np

import fsl.data.image          as fslimage
import fsl.transform.affine    as affine
import fsl.transform.nonlinear as nonlinear
import fsl.transform.fnirt     as fnirt


datadir = op.join(op.dirname(__file__), 'testdata')


def _random_image():
    vx, vy, vz = np.random.randint(10, 50, 3)
    dx, dy, dz = np.random.randint( 1, 10, 3)
    data       = (np.random.random((vx, vy, vz)) - 0.5) * 10
    aff        = affine.compose(
        (dx, dy, dz),
        np.random.randint(1, 100, 3),
        np.random.random(3) * np.pi / 2)

    return fslimage.Image(data, xform=aff)


def _random_field():

    src        = _random_image()
    vx, vy, vz = np.random.randint(10, 50, 3)
    dx, dy, dz = np.random.randint( 1, 10, 3)

    field = (np.random.random((vx, vy, vz, 3)) - 0.5) * 10
    aff   = affine.compose(
        (dx, dy, dz),
        np.random.randint(1, 100, 3),
        np.random.random(3) * np.pi / 2)

    return nonlinear.DisplacementField(field, src=src, xform=aff)

def _random_affine_field():

    src = _random_image()
    ref = _random_image()

    # our test field just encodes an affine
    xform = affine.compose(
        np.random.randint(2, 5, 3),
        np.random.randint(1, 10, 3),
        np.random.random(3))

    rx, ry, rz = np.meshgrid(np.arange(ref.shape[0]),
                             np.arange(ref.shape[1]),
                             np.arange(ref.shape[2]), indexing='ij')

    rvoxels  = np.vstack((rx.flatten(), ry.flatten(), rz.flatten())).T
    rcoords  = affine.transform(rvoxels, ref.voxToScaledVoxMat)
    scoords  = affine.transform(rcoords, xform)

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
    return affine.transform(
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
        refcoords = affine.transform(refcoords, ref.voxToScaledVoxMat)
        srccoords = basefield.transform(refcoords)

        field   = nonlinear.convertDisplacementSpace(basefield, from_, to)
        premat  = ref.getAffine('fsl', from_)
        postmat = src.getAffine('fsl', to)

        input  = affine.transform(refcoords, premat)
        expect = affine.transform(srccoords, postmat)

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
    rcoords  = affine.transform(rvoxels, ref.voxToScaledVoxMat)
    scoords  = affine.transform(rcoords, xform)
    svoxels  = affine.transform(scoords, src.scaledVoxToVoxMat)

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
    rcoords  = affine.transform(rvoxels, ref.voxToScaledVoxMat)
    scoords  = affine.transform(rcoords, xform)
    svoxels  = affine.transform(scoords, src.scaledVoxToVoxMat)

    got = relfield.transform(rcoords)
    assert np.all(np.isnan(got[0, :]))
    assert np.all(np.isclose(got[1, :], scoords[1, :]))
    got = absfield.transform(rcoords)
    assert np.all(np.isnan(got[0, :]))
    assert np.all(np.isclose(got[1, :], scoords[1, :]))


def test_CoefficientField_displacements():

    nldir = op.join(datadir, 'nonlinear')
    src   = op.join(nldir, 'src.nii.gz')
    ref   = op.join(nldir, 'ref.nii.gz')
    cf    = op.join(nldir, 'coefficientfield.nii.gz')
    df    = op.join(nldir, 'displacementfield_no_premat.nii.gz')

    src = fslimage.Image(src)
    ref = fslimage.Image(ref)
    cf  = fnirt.readFnirt(cf, src, ref)
    df  = fnirt.readFnirt(df, src, ref)

    ix, iy, iz = ref.shape[:3]
    x,  y,  z  = np.meshgrid(np.arange(ix),
                             np.arange(iy),
                             np.arange(iz), indexing='ij')
    x          = x.flatten()
    y          = y.flatten()
    z          = z.flatten()
    xyz        = np.vstack((x, y, z)).T

    disps = cf.displacements(xyz)
    disps = disps.reshape(df.shape)

    tol = dict(atol=1e-5, rtol=1e-5)
    assert np.all(np.isclose(disps, df.data, **tol))


def test_CoefficientField_transform():
    nldir = op.join(datadir, 'nonlinear')
    src   = op.join(nldir, 'src.nii.gz')
    ref   = op.join(nldir, 'ref.nii.gz')
    cf    = op.join(nldir, 'coefficientfield.nii.gz')
    df    = op.join(nldir, 'displacementfield.nii.gz')
    dfnp  = op.join(nldir, 'displacementfield_no_premat.nii.gz')

    src  = fslimage.Image(src)
    ref  = fslimage.Image(ref)
    cf   = fnirt.readFnirt(cf,   src, ref)
    df   = fnirt.readFnirt(df,   src, ref)
    dfnp = fnirt.readFnirt(dfnp, src, ref)

    spaces = ['fsl', 'voxel', 'world']
    spaces = list(it.combinations_with_replacement(spaces, 2))
    spaces = spaces + [(r, s) for s, r in spaces]
    spaces = list(set(spaces))

    rx, ry, rz = np.meshgrid(np.arange(ref.shape[0]),
                             np.arange(ref.shape[1]),
                             np.arange(ref.shape[2]), indexing='ij')
    rvoxels  = np.vstack((rx.flatten(), ry.flatten(), rz.flatten())).T

    refcoords = {
        'voxel' : rvoxels,
        'fsl'   : affine.transform(rvoxels, ref.getAffine('voxel', 'fsl')),
        'world' : affine.transform(rvoxels, ref.getAffine('voxel', 'world'))
    }

    srccoords = refcoords['fsl'] + df.data.reshape(-1, 3)
    srccoords = {
        'voxel' : affine.transform(srccoords, src.getAffine('fsl', 'voxel')),
        'fsl'   : srccoords,
        'world' : affine.transform(srccoords, src.getAffine('fsl', 'world'))
    }

    srccoordsnp = refcoords['fsl'] + dfnp.data.reshape(-1, 3)
    srccoordsnp = {
        'voxel' : affine.transform(srccoordsnp, src.getAffine('fsl', 'voxel')),
        'fsl'   : srccoordsnp,
        'world' : affine.transform(srccoordsnp, src.getAffine('fsl', 'world'))
    }

    tol = dict(atol=1e-5, rtol=1e-5)
    for srcspace, refspace in spaces:
        got   = cf.transform(refcoords[refspace], refspace, srcspace)
        gotnp = cf.transform(refcoords[refspace], refspace, srcspace,
                             premat=False)
        assert np.all(np.isclose(got,   srccoords[  srcspace], **tol))
        assert np.all(np.isclose(gotnp, srccoordsnp[srcspace], **tol))


def test_coefficientFieldToDisplacementField():

    nldir = op.join(datadir, 'nonlinear')
    src   = op.join(nldir, 'src.nii.gz')
    ref   = op.join(nldir, 'ref.nii.gz')
    cf    = op.join(nldir, 'coefficientfield.nii.gz')
    df    = op.join(nldir, 'displacementfield.nii.gz')
    dfnp  = op.join(nldir, 'displacementfield_no_premat.nii.gz')

    src   = fslimage.Image(src)
    ref   = fslimage.Image(ref)
    cf    = fnirt.readFnirt(cf,   src, ref)
    rdf   = fnirt.readFnirt(df,   src, ref)
    rdfnp = fnirt.readFnirt(dfnp, src, ref)
    adf   = nonlinear.convertDisplacementType(rdf)
    adfnp = nonlinear.convertDisplacementType(rdfnp)

    rcnv   = nonlinear.coefficientFieldToDisplacementField(cf)
    acnv   = nonlinear.coefficientFieldToDisplacementField(cf,
                                                           dispType='absolute')
    acnvnp = nonlinear.coefficientFieldToDisplacementField(cf,
                                                           dispType='absolute',
                                                           premat=False)
    rcnvnp = nonlinear.coefficientFieldToDisplacementField(cf,
                                                           premat=False)

    tol = dict(atol=1e-5, rtol=1e-5)
    assert np.all(np.isclose(rcnv.data,   rdf  .data, **tol))
    assert np.all(np.isclose(acnv.data,   adf  .data, **tol))
    assert np.all(np.isclose(rcnvnp.data, rdfnp.data, **tol))
    assert np.all(np.isclose(acnvnp.data, adfnp.data, **tol))


def test_DisplacementFIeld_srcToRefMat():

    field1 = _random_field()
    xform  = affine.compose(
        np.random.randint( 1, 10, 3),
        np.random.randint(1, 100, 3),
        np.random.random(3) * np.pi / 2)

    field2 = nonlinear.DisplacementField(
        field1.data,
        xform=field1.voxToWorldMat,
        src=field1.src,
        ref=field1.ref,
        srcToRefMat=xform)

    x = np.random.randint(0, field1.shape[0], 100)
    y = np.random.randint(0, field1.shape[1], 100)
    z = np.random.randint(0, field1.shape[2], 100)

    coords = np.array([x, y, z]).T
    coords = affine.transform(
        coords, field1.ref.getAffine('voxel', 'fsl'))

    coordsf1 = field1.transform(coords)
    coordsf2 = field2.transform(coords)
    coordsf1 = affine.transform(coordsf1, affine.invert(xform))

    assert np.all(np.isclose(coordsf1, coordsf2))
