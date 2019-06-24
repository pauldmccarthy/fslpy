#!/usr/bin/env python
#
# test_gifti.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import            shutil
import            glob
import os.path as op

import numpy   as np
import nibabel as nib
import pytest

import fsl.data.gifti as gifti

from . import tempdir


def test_GiftiMesh_create():

    testdir   = op.join(op.dirname(__file__), 'testdata')
    testfile  = op.join(testdir, 'example.surf.gii')

    surf      = gifti.GiftiMesh(testfile)
    minbounds = np.array([ 59.50759888,  88.43039703,  72.10890198])
    maxbounds = np.array([ 77.72619629, 128.40600586,  94.82050323])

    minb, maxb = surf.bounds

    assert surf.name                  == 'example'
    assert surf.dataSource            == testfile
    assert tuple(surf.vertices.shape) == (642,  3)
    assert tuple(surf.indices .shape) == (1280, 3)
    assert isinstance(surf.getMeta(testfile), nib.gifti.GiftiImage)

    assert np.all(np.isclose(minbounds, minb))
    assert np.all(np.isclose(maxbounds, maxb))


def test_GiftiMesh_create_loadAll():

    testdir  = op.join(op.dirname(__file__), 'testdata')
    testfile = op.join(testdir, 'example.surf.gii')

    with tempdir() as td:

        vertSets = [op.join(td, 'prefix.L.1.surf.gii'),
                    op.join(td, 'prefix.L.2.surf.gii'),
                    op.join(td, 'prefix.L.3.surf.gii')]

        for vs in vertSets:
            shutil.copy(testfile, vs)

        mesh = gifti.GiftiMesh(vertSets[0], loadAll=True)

        assert mesh.selectedVertices() == vertSets[0]

        mesh.vertices = vertSets[1]
        assert mesh.selectedVertices() == vertSets[1]

        mesh.vertices = vertSets[2]
        assert mesh.selectedVertices() == vertSets[2]


def test_loadGiftiMesh():

    testdir  = op.join(op.dirname(__file__), 'testdata')
    testfile = op.join(testdir, 'example.surf.gii')

    gimg, idxs, verts, _ = gifti.loadGiftiMesh(testfile)

    assert isinstance(gimg, nib.gifti.GiftiImage)
    assert len(verts)            == 1
    assert tuple(verts[0].shape) == (642,  3)
    assert tuple(idxs.shape)     == (1280, 3)

    badfiles = glob.glob(op.join(testdir, 'example_bad*surf.gii'))

    for bf in badfiles:
        with pytest.raises(Exception):
            gifti.loadGiftiSurface(bf)


def test_loadVertices():

    testdir  = op.join(op.dirname(__file__), 'testdata')
    testfile = op.join(testdir, 'example.surf.gii')

    with tempdir():

        mesh = gifti.GiftiMesh(testfile)

        shutil.copy(testfile, 'example2.surf.gii')


        verts  = mesh.vertices
        verts2 = verts * 2

        np.savetxt('verts.txt', verts2)

        assert np.all(np.isclose(mesh.loadVertices('example2.surf.gii'), verts))
        assert np.all(np.isclose(mesh.loadVertices('verts.txt')        , verts2))


def test_GiftiMesh_loadVertexData():

    testdir   = op.join(op.dirname(__file__), 'testdata')
    surffile  = op.join(testdir, 'example.surf.gii')

    shapefile = op.join(testdir, 'example.shape.gii')
    txtfile   = op.join(testdir, 'test_mesh_data.txt')
    memdata   = np.random.randint(1, 10, 642)

    # load from .gii file
    surf = gifti.GiftiMesh(surffile)
    assert surf.loadVertexData(shapefile).shape == (642, 1)

    # load from .txt file
    assert surf.loadVertexData(txtfile).shape == (642, 1)

    # add from memory
    assert np.all(np.isclose(surf.addVertexData('inmemdata', memdata), memdata.reshape(-1, 1)))

    # check cached
    assert surf.getVertexData(shapefile)  .shape == (642, 1)
    assert surf.getVertexData(txtfile)    .shape == (642, 1)
    assert surf.getVertexData('inmemdata').shape == (642, 1)


def test_loadGiftiVertexData():

    testdir = op.join(op.dirname(__file__), 'testdata')
    surffiles = glob.glob(op.join(testdir, 'example*surf.gii'))
    for sf in surffiles:
        with pytest.raises(Exception):
            gifti.loadGiftiVertexData(sf)

    ex3Dfile  = op.join(testdir, 'example.shape.gii')
    ex4Dfile  = op.join(testdir, 'example4D.shape.gii')
    ex4D2file = op.join(testdir, 'example4D_multiple_darrays.shape.gii')

    gimg, data = gifti.loadGiftiVertexData(ex3Dfile)
    assert isinstance(gimg, nib.gifti.GiftiImage)
    assert tuple(data.shape) == (642, 1)

    gimg, data = gifti.loadGiftiVertexData(ex4Dfile)
    assert isinstance(gimg, nib.gifti.GiftiImage)
    assert tuple(data.shape) == (642, 10)

    gimg, data = gifti.loadGiftiVertexData(ex4D2file)
    assert isinstance(gimg, nib.gifti.GiftiImage)
    assert tuple(data.shape) == (642, 10)


def test_relatedFiles():

    listing = [
        'subject.L.ArealDistortion_FS.32k_fs_LR.shape.gii',
        'subject.L.ArealDistortion_MSMSulc.32k_fs_LR.shape.gii',
        'subject.L.BA.32k_fs_LR.label.gii',
        'subject.L.MyelinMap.32k_fs_LR.func.gii',
        'subject.L.MyelinMap_BC.32k_fs_LR.func.gii',
        'subject.L.SmoothedMyelinMap.32k_fs_LR.func.gii',
        'subject.L.SmoothedMyelinMap_BC.32k_fs_LR.func.gii',
        'subject.L.aparc.32k_fs_LR.label.gii',
        'subject.L.aparc.a2009s.32k_fs_LR.label.gii',
        'subject.L.atlasroi.32k_fs_LR.shape.gii',
        'subject.L.corrThickness.32k_fs_LR.shape.gii',
        'subject.L.curvature.32k_fs_LR.shape.gii',
        'subject.L.flat.32k_fs_LR.surf.gii',
        'subject.L.inflated.32k_fs_LR.surf.gii',
        'subject.L.midthickness.32k_fs_LR.surf.gii',
        'subject.L.pial.32k_fs_LR.surf.gii',
        'subject.L.sphere.32k_fs_LR.surf.gii',
        'subject.L.sulc.32k_fs_LR.shape.gii',
        'subject.L.thickness.32k_fs_LR.shape.gii',
        'subject.L.very_inflated.32k_fs_LR.surf.gii',
        'subject.L.white.32k_fs_LR.surf.gii',
        'subject.R.ArealDistortion_FS.32k_fs_LR.shape.gii',
        'subject.R.ArealDistortion_MSMSulc.32k_fs_LR.shape.gii',
        'subject.R.BA.32k_fs_LR.label.gii',
        'subject.R.MyelinMap.32k_fs_LR.func.gii',
        'subject.R.MyelinMap_BC.32k_fs_LR.func.gii',
        'subject.R.SmoothedMyelinMap.32k_fs_LR.func.gii',
        'subject.R.SmoothedMyelinMap_BC.32k_fs_LR.func.gii',
        'subject.R.aparc.32k_fs_LR.label.gii',
        'subject.R.aparc.a2009s.32k_fs_LR.label.gii',
        'subject.R.atlasroi.32k_fs_LR.shape.gii',
        'subject.R.corrThickness.32k_fs_LR.shape.gii',
        'subject.R.curvature.32k_fs_LR.shape.gii',
        'subject.R.flat.32k_fs_LR.surf.gii',
        'subject.R.inflated.32k_fs_LR.surf.gii',
        'subject.R.midthickness.32k_fs_LR.surf.gii',
        'subject.R.pial.32k_fs_LR.surf.gii',
        'subject.R.sphere.32k_fs_LR.surf.gii',
        'subject.R.sulc.32k_fs_LR.shape.gii',
        'subject.R.thickness.32k_fs_LR.shape.gii',
        'subject.R.very_inflated.32k_fs_LR.surf.gii',
        'subject.R.white.32k_fs_LR.surf.gii',
        'badly-formed-filename.surf.gii'
    ]

    lsurfaces = [l for l in listing if (l.startswith('subject.L') and
                                        l.endswith('surf.gii'))]
    lrelated  = [l for l in listing if (l.startswith('subject.L') and
                                        not l.endswith('surf.gii'))]

    rsurfaces = [l for l in listing if (l.startswith('subject.R') and
                                        l.endswith('surf.gii'))]
    rrelated  = [l for l in listing if (l.startswith('subject.R') and
                                        not l.endswith('surf.gii'))]

    with tempdir() as td:

        for l in listing:
            with open(op.join(td, l), 'wt') as f:
                f.write(l)

        badname = op.join(op.join(td, 'badly-formed-filename'))

        assert len(gifti.relatedFiles(badname))       == 0
        assert len(gifti.relatedFiles('nonexistent')) == 0

        llisting  = [op.join(td, f) for f in listing]
        lsurfaces = [op.join(td, f) for f in lsurfaces]
        rsurfaces = [op.join(td, f) for f in rsurfaces]
        lrelated  = [op.join(td, f) for f in lrelated]
        rrelated  = [op.join(td, f) for f in rrelated]

        for s in lsurfaces:
            result = gifti.relatedFiles(s)
            assert sorted(lrelated) == sorted(result)
        for s in rsurfaces:
            result = gifti.relatedFiles(s)
            assert sorted(rrelated) == sorted(result)

        exp = lsurfaces + lrelated
        exp = [f for f in exp if f != lsurfaces[0]]
        result = gifti.relatedFiles(lsurfaces[0],
                                    ftypes=gifti.ALLOWED_EXTENSIONS)
        assert sorted(exp) == sorted(result)

TEST_VERTS = np.array([
    [0, 0, 0],
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 1]])
TEST_IDXS = np.array([
    [0, 1, 2],
    [0, 3, 1],
    [0, 2, 3],
    [1, 3, 2]])

TEST_VERT_ARRAY = nib.gifti.GiftiDataArray(
    TEST_VERTS, intent='NIFTI_INTENT_POINTSET')
TEST_IDX_ARRAY  = nib.gifti.GiftiDataArray(
    TEST_IDXS, intent='NIFTI_INTENT_TRIANGLE')

def test_GiftiMesh_surface_and_data():

    data1   = np.random.randint(0, 10, len(TEST_VERTS))
    data2   = np.random.randint(0, 10, len(TEST_VERTS))
    expdata = np.vstack([data1, data2]).T
    verts   = TEST_VERT_ARRAY
    tris    = TEST_IDX_ARRAY
    data1   = nib.gifti.GiftiDataArray(data1, intent='NIFTI_INTENT_SHAPE')
    data2   = nib.gifti.GiftiDataArray(data2, intent='NIFTI_INTENT_SHAPE')
    gimg    = nib.gifti.GiftiImage(darrays=[verts, tris, data1, data2])

    with tempdir():
        fname = op.abspath('test.gii')
        gimg.to_filename(fname)
        surf = gifti.GiftiMesh(fname)

        assert np.all(surf.vertices  == TEST_VERTS)
        assert np.all(surf.indices   == TEST_IDXS)
        assert surf.vertexDataSets() == [fname]
        assert np.all(surf.getVertexData(fname) == expdata)



def test_GiftiMesh_multiple_vertices():

    tris   = TEST_IDX_ARRAY
    verts1 = TEST_VERT_ARRAY
    verts2 = nib.gifti.GiftiDataArray(
        TEST_VERTS * 5, intent='NIFTI_INTENT_POINTSET')
    verts3 = nib.gifti.GiftiDataArray(
        TEST_VERTS * 10, intent='NIFTI_INTENT_POINTSET')

    gimg  = nib.gifti.GiftiImage(darrays=[verts1, verts2, tris])
    gimg2 = nib.gifti.GiftiImage(darrays=[verts3, tris])

    with tempdir():
        fname  = op.abspath('test.gii')
        fname2 = op.abspath('test2.gii')
        gimg .to_filename(fname)
        gimg2.to_filename(fname2)

        surf  = gifti.GiftiMesh(fname)

        expvsets = [fname, '{}_1'.format(fname)]

        expbounds1 = np.min(verts1.data, axis=0), np.max(verts1.data, axis=0)
        expbounds2 = np.min(verts2.data, axis=0), np.max(verts2.data, axis=0)
        expbounds3 = np.min(verts3.data, axis=0), np.max(verts3.data, axis=0)

        assert np.all(surf.vertices == TEST_VERTS)
        assert np.all(surf.indices  == TEST_IDXS)
        assert  surf.vertexSets()   == expvsets
        assert np.all(np.isclose(surf.bounds, expbounds1))

        surf.vertices = expvsets[1]
        assert np.all(surf.vertices == TEST_VERTS * 5)
        assert np.all(np.isclose(surf.bounds, expbounds2))

        surf.loadVertices(fname2, select=True)
        assert np.all(surf.vertices == TEST_VERTS * 10)
        assert np.all(np.isclose(surf.bounds, expbounds3))


def test_GiftiMesh_needsFixing():
    from . import test_mesh

    verts      = test_mesh.CUBE_VERTICES
    idxs       = test_mesh.CUBE_TRIANGLES_CW
    idxs_fixed = test_mesh.CUBE_TRIANGLES_CCW

    verts = nib.gifti.GiftiDataArray(verts, intent='NIFTI_INTENT_POINTSET')
    idxs  = nib.gifti.GiftiDataArray(idxs,  intent='NIFTI_INTENT_TRIANGLE')
    gimg  = nib.gifti.GiftiImage(darrays=[verts, idxs])

    with tempdir():
        fname = op.abspath('test.gii')
        gimg.to_filename(fname)

        surf = gifti.GiftiMesh(fname, fixWinding=True)

        assert np.all(np.isclose(surf.indices, idxs_fixed))
