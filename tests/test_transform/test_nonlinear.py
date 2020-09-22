#!/usr/bin/env python

import itertools as it
import os.path   as op

import numpy   as np

import fsl.data.image           as fslimage
import fsl.utils.image.resample as resample
import fsl.utils.image.roi      as roi
import fsl.transform.affine     as affine
import fsl.transform.nonlinear  as nonlinear
import fsl.transform.fnirt      as fnirt


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

    return nonlinear.DeformationField(field, src=src, xform=aff)


def _affine_field(src, ref, xform, srcSpace, refSpace, shape=None, fv2w=None):

    if shape is None: shape = ref.shape[:3]
    if fv2w  is None: fv2w  = ref.getAffine('voxel', 'world')

    rx, ry, rz = np.meshgrid(np.arange(shape[0]),
                             np.arange(shape[1]),
                             np.arange(shape[2]), indexing='ij')

    rvoxels  = np.vstack((rx.flatten(), ry.flatten(), rz.flatten())).T
    f2r      = affine.concat(ref.getAffine('world', refSpace), fv2w)
    rcoords  = affine.transform(rvoxels, f2r)
    scoords  = affine.transform(rcoords, xform)

    field    = np.zeros(list(shape[:3]) + [3])
    field[:] = (scoords - rcoords).reshape(*it.chain(shape, [3]))
    field    = nonlinear.DeformationField(field, src, ref,
                                          srcSpace=srcSpace,
                                          refSpace=refSpace,
                                          xform=fv2w,
                                          header=ref.header,
                                          defType='relative')
    return field


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
    field    = nonlinear.DeformationField(field, src, ref,
                                          header=ref.header,
                                          defType='relative')
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


def test_detectDeformationType():
    relfield = _random_field()
    coords   = _field_coords(relfield)
    absfield = nonlinear.DeformationField(
        relfield.data + coords,
        src=relfield.src,
        xform=relfield.voxToWorldMat)

    assert nonlinear.detectDeformationType(relfield) == 'relative'
    assert nonlinear.detectDeformationType(absfield) == 'absolute'


def test_convertDeformationType():

    relfield = _random_field()
    coords   = _field_coords(relfield)
    absfield = nonlinear.DeformationField(
        relfield.data + coords,
        src=relfield.src,
        xform=relfield.voxToWorldMat)

    gotconvrel1 = nonlinear.convertDeformationType(relfield)
    gotconvabs1 = nonlinear.convertDeformationType(absfield)
    gotconvrel2 = nonlinear.convertDeformationType(relfield, 'absolute')
    gotconvabs2 = nonlinear.convertDeformationType(absfield, 'relative')

    tol = dict(atol=1e-3, rtol=1e-3)

    assert np.all(np.isclose(gotconvrel1, absfield.data, **tol))
    assert np.all(np.isclose(gotconvabs1, relfield.data, **tol))
    assert np.all(np.isclose(gotconvrel2, absfield.data, **tol))
    assert np.all(np.isclose(gotconvabs2, relfield.data, **tol))


def test_convertDeformationSpace():

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

        field   = nonlinear.convertDeformationSpace(basefield, from_, to)
        premat  = ref.getAffine('fsl', from_)
        postmat = src.getAffine('fsl', to)

        input  = affine.transform(refcoords, premat)
        expect = affine.transform(srccoords, postmat)

        got  = field.transform(input)
        enan = np.isnan(expect)
        gnan = np.isnan(got)

        assert np.all(np.isclose(enan, gnan))
        assert np.all(np.isclose(expect[~enan], got[~gnan]))


def test_DeformationField_transform():

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
    absfield    = nonlinear.DeformationField(absfield, src, ref,
                                             header=ref.header,
                                             defType='absolute')

    got = relfield.transform(rcoords)
    assert np.all(np.isclose(got, scoords))
    got = absfield.transform(rcoords)
    assert np.all(np.isclose(got, scoords))

    # test single set of coords
    got = absfield.transform(rcoords[0])
    assert np.all(np.isclose(got, scoords[0]))

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


def test_coefficientField_transform_altref():

    # test coordinates (manually determined).
    # original ref image is 2mm isotropic,
    # resampled is 1mm. Each tuple contains:
    #
    # (src, ref2mm, ref1mm)
    coords = [
        ((18.414, 26.579, 25.599), (11, 19, 11), (22, 38, 22)),
        ((14.727, 22.480, 20.340), ( 8, 17,  8), (16, 34, 16)),
        ((19.932, 75.616, 27.747), (11, 45,  5), (22, 90, 10))
    ]

    nldir  = op.join(datadir, 'nonlinear')
    src    = op.join(nldir, 'src.nii.gz')
    ref    = op.join(nldir, 'ref.nii.gz')
    cf     = op.join(nldir, 'coefficientfield.nii.gz')

    src      = fslimage.Image(src)
    ref2mm   = fslimage.Image(ref)
    ref1mm   = ref2mm.adjust((1, 1, 1))
    cfref2mm = fnirt.readFnirt(cf, src, ref2mm)
    cfref1mm = fnirt.readFnirt(cf, src, ref1mm)

    for srcc, ref2mmc, ref1mmc in coords:
        ref2mmc = cfref2mm.transform(ref2mmc, 'voxel', 'voxel')
        ref1mmc = cfref1mm.transform(ref1mmc, 'voxel', 'voxel')

        assert np.all(np.isclose(ref2mmc, srcc, 1e-4))
        assert np.all(np.isclose(ref1mmc, srcc, 1e-4))


def test_coefficientFieldToDeformationField():

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
    adf   = nonlinear.convertDeformationType(rdf)
    adfnp = nonlinear.convertDeformationType(rdfnp)

    rcnv   = nonlinear.coefficientFieldToDeformationField(cf)
    acnv   = nonlinear.coefficientFieldToDeformationField(cf,
                                                          defType='absolute')
    acnvnp = nonlinear.coefficientFieldToDeformationField(cf,
                                                          defType='absolute',
                                                          premat=False)
    rcnvnp = nonlinear.coefficientFieldToDeformationField(cf,
                                                          premat=False)

    tol = dict(atol=1e-5, rtol=1e-5)
    assert np.all(np.isclose(rcnv.data,   rdf  .data, **tol))
    assert np.all(np.isclose(acnv.data,   adf  .data, **tol))
    assert np.all(np.isclose(rcnvnp.data, rdfnp.data, **tol))
    assert np.all(np.isclose(acnvnp.data, adfnp.data, **tol))


def test_applyDeformation():

    src2ref = affine.compose(
        np.random.randint(2, 5, 3),
        np.random.randint(1, 10, 3),
        np.random.random(3))
    ref2src = affine.invert(src2ref)

    srcdata = np.random.randint(1, 65536, (10, 10, 10))
    refdata = np.random.randint(1, 65536, (10, 10, 10))

    src   = fslimage.Image(srcdata)
    ref   = fslimage.Image(refdata, xform=src2ref)
    field = _affine_field(src, ref, ref2src, 'world', 'world')

    expect, xf = resample.resampleToReference(
        src, ref, matrix=src2ref, order=1, mode='nearest')
    result = nonlinear.applyDeformation(
        src, field, order=1, mode='nearest')

    assert np.all(np.isclose(expect, result))


def test_applyDeformation_altsrc():

    src2ref = affine.compose(
        np.random.randint(2, 5, 3),
        np.random.randint(1, 10, 3),
        [0, 0, 0])
    ref2src = affine.invert(src2ref)

    srcdata = np.random.randint(1, 65536, (10, 10, 10))
    refdata = np.random.randint(1, 65536, (10, 10, 10))

    src   = fslimage.Image(srcdata)
    ref   = fslimage.Image(refdata, xform=src2ref)
    field = _affine_field(src, ref, ref2src, 'world', 'world')

    # First try a down-sampled version
    # of the original source image
    altsrc, xf = resample.resample(src, (5, 5, 5), origin='corner')
    altsrc     = fslimage.Image(altsrc, xform=xf, header=src.header)
    expect, xf = resample.resampleToReference(
        altsrc, ref, matrix=src2ref, order=1, mode='nearest')
    result = nonlinear.applyDeformation(
        altsrc, field, order=1, mode='nearest')
    assert np.all(np.isclose(expect, result))

    # Now try a down-sampled ROI
    # of the original source image
    altsrc     = roi.roi(src, [(2, 9), (2, 9), (2, 9)])
    altsrc, xf = resample.resample(altsrc, (4, 4, 4))
    altsrc     = fslimage.Image(altsrc, xform=xf, header=src.header)
    expect, xf = resample.resampleToReference(
        altsrc, ref, matrix=src2ref, order=1, mode='nearest')
    result = nonlinear.applyDeformation(
        altsrc, field, order=1, mode='nearest')
    assert np.all(np.isclose(expect, result))

    # down-sampled and offset ROI
    # of the original source image
    altsrc     = roi.roi(src, [(-5, 8), (-5, 8), (-5, 8)])
    altsrc, xf = resample.resample(altsrc, (6, 6, 6))
    altsrc     = fslimage.Image(altsrc, xform=xf, header=src.header)
    expect, xf = resample.resampleToReference(
        altsrc, ref, matrix=src2ref, order=1, mode='nearest')
    result = nonlinear.applyDeformation(
        altsrc, field, order=1, mode='nearest')
    assert np.all(np.isclose(expect, result))


def test_applyDeformation_premat():

    src2ref = affine.compose(
        np.random.randint(2, 5, 3),
        np.random.randint(1, 10, 3),
        [0, 0, 0])
    ref2src = affine.invert(src2ref)

    srcdata = np.random.randint(1, 65536, (10, 10, 10))
    refdata = np.random.randint(1, 65536, (10, 10, 10))

    src   = fslimage.Image(srcdata)
    ref   = fslimage.Image(refdata, xform=src2ref)
    field = _affine_field(src, ref, ref2src, 'world', 'world')

    # First try a down-sampled version
    # of the original source image
    altsrc, xf = resample.resample(src, (5, 5, 5), origin='corner')
    altsrc     = fslimage.Image(altsrc, xform=xf, header=src.header)
    expect, xf = resample.resampleToReference(
        altsrc, ref, matrix=src2ref, order=1, mode='nearest')
    premat = affine.concat(src   .getAffine('world', 'voxel'),
                           altsrc.getAffine('voxel', 'world'))
    result = nonlinear.applyDeformation(
        altsrc, field, order=1, mode='nearest', premat=premat)
    assert np.all(np.isclose(expect, result))

    # Now try a down-sampled ROI
    # of the original source image
    altsrc     = roi.roi(src, [(2, 9), (2, 9), (2, 9)])
    altsrc, xf = resample.resample(altsrc, (4, 4, 4))
    altsrc     = fslimage.Image(altsrc, xform=xf, header=src.header)
    expect, xf = resample.resampleToReference(
        altsrc, ref, matrix=src2ref, order=1, mode='nearest')
    premat = affine.concat(src   .getAffine('world', 'voxel'),
                           altsrc.getAffine('voxel', 'world'))
    result = nonlinear.applyDeformation(
        altsrc, field, order=1, mode='nearest', premat=premat)
    assert np.all(np.isclose(expect, result))

    # down-sampled and offset ROI
    # of the original source image
    altsrc     = roi.roi(src, [(-5, 8), (-5, 8), (-5, 8)])
    altsrc, xf = resample.resample(altsrc, (6, 6, 6))
    altsrc     = fslimage.Image(altsrc, xform=xf, header=src.header)
    expect, xf = resample.resampleToReference(
        altsrc, ref, matrix=src2ref, order=1, mode='nearest')
    premat = affine.concat(src   .getAffine('world', 'voxel'),
                           altsrc.getAffine('voxel', 'world'))
    result = nonlinear.applyDeformation(
        altsrc, field, order=1, mode='nearest', premat=premat)
    assert np.all(np.isclose(expect, result))


def test_applyDeformation_altref():
    src2ref = affine.compose(
        np.random.randint(2, 5, 3),
        np.random.randint(1, 10, 3),
        np.random.random(3))
    ref2src = affine.invert(src2ref)

    srcdata = np.random.randint(1, 65536, (10, 10, 10))
    refdata = np.random.randint(1, 65536, (10, 10, 10))

    src   = fslimage.Image(srcdata)
    ref   = fslimage.Image(refdata, xform=src2ref)
    field = _affine_field(src, ref, ref2src, 'world', 'world')

    altrefxform = affine.concat(
        src2ref,
        affine.scaleOffsetXform([1, 1, 1], [5, 0, 0]))

    altref = fslimage.Image(refdata, xform=altrefxform)

    expect, xf = resample.resampleToReference(
        src, altref, matrix=src2ref, order=1, mode='constant', cval=0)
    result = nonlinear.applyDeformation(
        src, field, ref=altref, order=1, mode='constant', cval=0)

    # boundary voxels can get truncated
    # (4 is the altref-ref overlap boundary)
    expect[4, :, :] = 0
    result[4, :, :] = 0
    expect = expect[1:-1, 1:-1, 1:-1]
    result = result[1:-1, 1:-1, 1:-1]

    assert np.all(np.isclose(expect, result))


# test when reference/field
# are not voxel-aligned
def test_applyDeformation_worldAligned():
    refv2w   = affine.scaleOffsetXform([1, 1, 1], [10,   10,   10])
    fieldv2w = affine.scaleOffsetXform([2, 2, 2], [10.5, 10.5, 10.5])
    src2ref  = refv2w
    ref2src  = affine.invert(src2ref)

    srcdata = np.random.randint(1, 65536, (10, 10, 10))

    src   = fslimage.Image(srcdata)
    ref   = fslimage.Image(srcdata, xform=src2ref)
    field = _affine_field(src, ref, ref2src, 'world', 'world',
                          shape=(5, 5, 5), fv2w=fieldv2w)

    field = nonlinear.DeformationField(
        nonlinear.convertDeformationType(field, 'absolute'),
        header=field.header,
        src=src,
        ref=ref,
        srcSpace='world',
        refSpace='world',
        defType='absolute')

    expect, xf = resample.resampleToReference(
        src, ref, matrix=src2ref, order=1, mode='constant', cval=0)
    result = nonlinear.applyDeformation(
        src, field, order=1, mode='constant', cval=0)

    expect = expect[1:-1, 1:-1, 1:-1]
    result = result[1:-1, 1:-1, 1:-1]

    assert np.all(np.isclose(expect, result))
