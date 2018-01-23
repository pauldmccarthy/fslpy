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

    gimg, verts, idxs = gifti.loadGiftiMesh(testfile)

    assert isinstance(gimg, nib.gifti.GiftiImage)
    assert tuple(verts.shape) == (642,  3)
    assert tuple(idxs.shape)  == (1280, 3)

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
