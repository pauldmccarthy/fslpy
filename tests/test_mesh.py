#!/usr/bin/env python
#
# test_mesh.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path as op
import            shutil
import            tempfile

import numpy   as np
import            mock
import            pytest

import fsl.utils.transform as transform
import fsl.data.mesh       as fslmesh


datadir = op.join(op.dirname(__file__), 'testdata')


# vertices of a cube
CUBE_VERTICES = np.array([
    [-1, -1, -1],
    [-1, -1,  1],
    [-1,  1, -1],
    [-1,  1,  1],
    [ 1, -1, -1],
    [ 1, -1,  1],
    [ 1,  1, -1],
    [ 1,  1,  1],
])

# triangles
# cw  == clockwise, when facing outwards
#        from the centre of the mesh
CUBE_TRIANGLES_CW = np.array([
    [0, 4, 6], [0, 6, 2],
    [1, 3, 5], [3, 7, 5],
    [0, 1, 4], [1, 5, 4],
    [2, 6, 7], [2, 7, 3],
    [0, 2, 1], [1, 2, 3],
    [4, 5, 7], [4, 7, 6],
])

# ccw == counter-clockwise
CUBE_TRIANGLES_CCW = np.array(CUBE_TRIANGLES_CW)
CUBE_TRIANGLES_CCW[:, [1, 2]] = CUBE_TRIANGLES_CCW[:, [2, 1]]


def test_create_mesh():

    # Test:
    #  - create from file
    #  - create from inmem data
    testbase = 'test_mesh.vtk'
    testfile = op.join(datadir, testbase)

    verts, lens, indices = fslmesh.loadVTKPolydataFile(testfile)

    mesh1 = fslmesh.TriangleMesh(testfile)
    mesh2 = fslmesh.TriangleMesh(verts, indices)

    assert mesh1.name       == testbase
    assert mesh2.name       == 'TriangleMesh'
    assert mesh1.dataSource == testfile
    assert mesh2.dataSource is None

    assert mesh1.vertices.shape == (642,  3)
    assert mesh2.vertices.shape == (642,  3)
    assert mesh1.indices.shape  == (1280, 3)
    assert mesh2.indices.shape  == (1280, 3)

    minbounds = np.array([ 59.50759888,  88.43039703,  72.10890198])
    maxbounds = np.array([ 77.72619629, 128.40600586,  94.82050323])

    mesh1Bounds = mesh1.getBounds()
    mesh2Bounds = mesh2.getBounds()

    assert np.all(np.isclose(mesh1Bounds[0], minbounds))
    assert np.all(np.isclose(mesh1Bounds[1], maxbounds))
    assert np.all(np.isclose(mesh2Bounds[0], minbounds))
    assert np.all(np.isclose(mesh2Bounds[1], maxbounds))


def test_mesh_loadVertexData():

    meshfile = op.join(datadir, 'test_mesh.vtk')
    datafile = op.join(datadir, 'test_mesh_data.txt')
    memdata  = np.random.randint(1, 100, 642)
    mesh     = fslmesh.TriangleMesh(meshfile)

    assert mesh.loadVertexData(datafile).shape == (642,)
    assert np.all(mesh.loadVertexData('inmemdata', memdata) == memdata)

    assert mesh.getVertexData(datafile).shape == (642,)
    assert np.all(mesh.getVertexData('inmemdata') == memdata)

    mesh.clearVertexData()

    assert mesh.getVertexData(datafile).shape == (642,)
    assert np.all(mesh.loadVertexData('inmemdata', memdata) == memdata)


def test_loadVTKPolydataFile():

    testfile = op.join(datadir, 'test_mesh.vtk')
    verts, lens, indices = fslmesh.loadVTKPolydataFile(testfile)

    assert verts.shape   == (642, 3)
    assert indices.shape == (3840, )
    assert lens.shape    == (1280, )
    assert np.all(lens == 3)


def test_getFIRSTPrefix():

    failures = [
        'blob.txt',
        'blob.vtk',
        'blob.nii.gz']

    passes = [
        ('blurgh-L_Thal_first.vtk', 'blurgh'),
        ('blurgh-L_Accu_first.vtk', 'blurgh'),
        ('blurgh_bufuu-R_Hipp_first.vtk', 'blurgh_bufuu'),
    ]

    for f in failures:
        with pytest.raises(ValueError):
            fslmesh.getFIRSTPrefix(f)

    for fname, expected in passes:
        assert fslmesh.getFIRSTPrefix(fname) == expected



def test_findReferenceImage():

    testdir  = tempfile.mkdtemp()
    vtkfiles = ['struc-L_Thal_first.vtk',
                'struc_first-L_Thal_first.vtk']

    assert fslmesh.findReferenceImage('nofile') is None

    try:

        for fname in vtkfiles:

            assert fslmesh.findReferenceImage(fname) is None

            prefix   = fslmesh.getFIRSTPrefix(fname)
            imgfname = op.join(testdir, '{}.nii.gz'.format(prefix))
            fname    = op.join(testdir, fname)

            with open(fname,    'wt') as f: f.write(fname)
            with open(imgfname, 'wt') as f: f.write(imgfname)

            assert fslmesh.findReferenceImage(fname) == imgfname

    finally:
        shutil.rmtree(testdir)


def test_normals():

    # vertices of a cube
    verts         = np.array(CUBE_VERTICES)
    triangles_cw  = np.array(CUBE_TRIANGLES_CW)
    triangles_ccw = np.array(CUBE_TRIANGLES_CCW)

    # face normals
    fnormals = np.array([
        [ 0,  0, -1], [ 0,  0, -1],
        [ 0,  0,  1], [ 0,  0,  1],
        [ 0, -1,  0], [ 0, -1,  0],
        [ 0,  1,  0], [ 0,  1,  0],
        [-1,  0,  0], [-1,  0,  0],
        [ 1,  0,  0], [ 1,  0,  0],
    ])

    # vertex normals
    vnormals = np.zeros((8, 3))
    for i in range(8):
        faces = np.where(triangles_cw == i)[0]
        vnormals[i] = fnormals[faces].sum(axis=0)
    vnormals = transform.normalise(vnormals)

    cw_nofix  = fslmesh.TriangleMesh(verts, triangles_cw)
    cw_fix    = fslmesh.TriangleMesh(verts, triangles_cw, fixWinding=True)
    ccw_nofix = fslmesh.TriangleMesh(verts, triangles_ccw)
    ccw_fix   = fslmesh.TriangleMesh(verts, triangles_ccw, fixWinding=True)

    # ccw triangles should give correct
    # normals without unwinding
    assert np.all(np.isclose(cw_nofix .normals,  -fnormals))
    assert np.all(np.isclose(cw_nofix .vnormals, -vnormals))
    assert np.all(np.isclose(cw_fix   .normals,   fnormals))
    assert np.all(np.isclose(cw_fix   .vnormals,  vnormals))
    assert np.all(np.isclose(ccw_nofix.normals,   fnormals))
    assert np.all(np.isclose(ccw_nofix.vnormals, vnormals))
    assert np.all(np.isclose(ccw_fix  .normals,   fnormals))
    assert np.all(np.isclose(ccw_fix  .vnormals,  vnormals))



def test_trimesh_no_trimesh():

    testbase = 'test_mesh.vtk'
    testfile = op.join(datadir, testbase)

    mods = ['trimesh', 'rtree']

    for mod in mods:
        with mock.patch.dict('sys.modules', **{mod : None}):
            mesh = fslmesh.TriangleMesh(testfile)
            assert mesh.trimesh() is None
            locs, tris = mesh.rayIntersection([[0, 0, 0]], [[0, 0, 1]])
            assert locs.size == 0
            assert tris.size == 0


def test_trimesh():

    import trimesh

    testbase = 'test_mesh.vtk'
    testfile = op.join(datadir, testbase)
    mesh = fslmesh.TriangleMesh(testfile)
    assert isinstance(mesh.trimesh(), trimesh.Trimesh)


def test_rayIntersection():

    verts     = np.array(CUBE_VERTICES)
    triangles = np.array(CUBE_TRIANGLES_CCW)
    mesh      = fslmesh.TriangleMesh(verts, triangles)

    for axis in range(3):
        rayOrigin       = [0, 0, 0]
        rayDir          = [0, 0, 0]
        rayOrigin[axis] = -2
        rayDir[   axis] =  1

        loc, tri = mesh.rayIntersection([rayOrigin], [rayDir])

        assert loc.shape == (1, 3)
        assert tri.shape == (1,)

        expected          = np.array([[0, 0, 0]])
        expected[0, axis] = -1

        assert np.all(np.isclose(loc, expected))

    loc, tri = mesh.rayIntersection([[-2, -2, -2]], [[-1, -1, -1]])

    assert loc.size == 0
    assert tri.size == 0


def test_nearestVertex():

    verts     = np.array(CUBE_VERTICES)
    triangles = np.array(CUBE_TRIANGLES_CCW)
    mesh      = fslmesh.TriangleMesh(verts, triangles)

    nverts, nidxs, ndists = mesh.nearestVertex(verts * 2)

    assert np.all(np.isclose(nverts, verts))
    assert np.all(np.isclose(nidxs,  np.arange(len(verts))))
    assert np.all(np.isclose(ndists, np.sqrt(3)))
