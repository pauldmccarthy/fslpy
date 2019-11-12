#!/usr/bin/env python
#
# test_mesh.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path  as     op
import numpy    as     np
from   unittest import mock
import                 pytest

import fsl.transform.affine as affine
import fsl.data.mesh        as fslmesh

from . import tempdir


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

CUBE_CCW_FACE_NORMALS = np.array([
    [ 0,  0, -1], [ 0,  0, -1],
    [ 0,  0,  1], [ 0,  0,  1],
    [ 0, -1,  0], [ 0, -1,  0],
    [ 0,  1,  0], [ 0,  1,  0],
    [-1,  0,  0], [-1,  0,  0],
    [ 1,  0,  0], [ 1,  0,  0],
])

CUBE_CCW_VERTEX_NORMALS = np.zeros((8, 3))
for i in range(8):
    faces = np.where(CUBE_TRIANGLES_CCW == i)[0]
    CUBE_CCW_VERTEX_NORMALS[i] = CUBE_CCW_FACE_NORMALS[faces].sum(axis=0)
CUBE_CCW_VERTEX_NORMALS = affine.normalise(CUBE_CCW_VERTEX_NORMALS)


def test_mesh_create():

    verts = np.array(CUBE_VERTICES)
    tris  = np.array(CUBE_TRIANGLES_CCW)

    mesh = fslmesh.Mesh(tris, vertices=verts)

    print(str(mesh))

    assert mesh.name       == 'mesh'
    assert mesh.dataSource is None
    assert mesh.nvertices  == 8
    assert np.all(np.isclose(mesh.vertices, verts))
    assert np.all(np.isclose(mesh.indices,  tris))

    blo, bhi = mesh.bounds

    assert np.all(np.isclose(blo, verts.min(axis=0)))
    assert np.all(np.isclose(bhi, verts.max(axis=0)))


def test_mesh_addVertices():

    tris   = np.array(CUBE_TRIANGLES_CCW)
    verts  = np.array(CUBE_VERTICES)
    verts2 = np.array(CUBE_VERTICES) * 2
    verts3 = np.array(CUBE_VERTICES) * 3

    mesh = fslmesh.Mesh(tris, vertices=verts)

    assert mesh.selectedVertices() == 'default'
    assert mesh.vertexSets() == ['default']
    assert np.all(np.isclose(mesh.vertices, verts))

    assert np.all(np.isclose(mesh.addVertices(verts2, 'twotimes'), verts2))

    assert mesh.selectedVertices() == 'twotimes'
    assert mesh.vertexSets() == ['default', 'twotimes']
    assert np.all(np.isclose(mesh.vertices, verts2))

    assert np.all(np.isclose(mesh.addVertices(verts3, 'threetimes', select=False), verts3))

    assert mesh.selectedVertices() == 'twotimes'
    assert mesh.vertexSets() == ['default', 'twotimes', 'threetimes']
    assert np.all(np.isclose(mesh.vertices, verts2))

    mesh.vertices = 'threetimes'

    assert mesh.selectedVertices() == 'threetimes'
    assert np.all(np.isclose(mesh.vertices, verts3))

    with pytest.raises(ValueError):
        mesh.addVertices(verts[:-1, :], 'badverts')


def test_loadVertices():

    tris  = np.array(CUBE_TRIANGLES_CCW)
    verts = np.array(CUBE_VERTICES)

    mesh = fslmesh.Mesh(tris, vertices=verts)

    with tempdir():

        verts2 = verts * 2

        np.savetxt('verts2.txt', verts2)

        assert np.all(np.isclose(mesh.loadVertices('verts2.txt'), verts2))

        assert mesh.selectedVertices() == op.abspath('verts2.txt')

        np.savetxt('badverts.txt', verts2[:-1, :])

        with pytest.raises(ValueError):
            mesh.loadVertices('badverts.txt')


def test_mesh_addVertexData():

    mesh = fslmesh.Mesh(np.array(CUBE_TRIANGLES_CCW),
                        vertices=np.array(CUBE_VERTICES))

    nverts = CUBE_VERTICES.shape[0]

    data3D   = np.random.randint(1, 100,  nverts)
    data3_1D = np.random.randint(1, 100, (nverts, 1))
    data4D   = np.random.randint(1, 100, (nverts, 20))
    dataBad  = np.random.randint(1, 100, (nverts - 1, 20))

    assert np.all(np.isclose(mesh.addVertexData('3d',   data3D),   data3D.reshape(-1, 1)))
    assert list(mesh.vertexDataSets()) == ['3d']

    assert np.all(np.isclose(mesh.addVertexData('3_1d', data3_1D), data3_1D))
    assert list(mesh.vertexDataSets()) == ['3d', '3_1d']

    assert np.all(np.isclose(mesh.addVertexData('4d',   data4D),   data4D))
    assert list(mesh.vertexDataSets()) == ['3d', '3_1d', '4d']

    assert mesh.getVertexData('3d')  .shape == (nverts, 1)
    assert mesh.getVertexData('3_1d').shape == (nverts, 1)
    assert mesh.getVertexData('4d')  .shape == (nverts, 20)

    assert np.all(np.isclose(data3D.reshape(-1, 1), mesh.getVertexData('3d')))
    assert np.all(np.isclose(data3_1D,              mesh.getVertexData('3_1d')))
    assert np.all(np.isclose(data4D,                mesh.getVertexData('4d')))

    mesh.clearVertexData()

    with pytest.raises(KeyError):   mesh.getVertexData('3d')
    with pytest.raises(KeyError):   mesh.getVertexData('3_1d')
    with pytest.raises(KeyError):   mesh.getVertexData('4d')
    with pytest.raises(ValueError): mesh.addVertexData('bad', dataBad)


def test_loadVertexData():

    verts = np.array(CUBE_VERTICES)
    tris  = np.array(CUBE_TRIANGLES_CCW)
    vdata = np.random.randint(1, 100, verts.shape[0]).reshape(-1, 1)
    mesh  = fslmesh.Mesh(tris, vertices=verts)

    with tempdir():
        np.savetxt('vdata.txt',    vdata)
        np.savetxt('badvdata.txt', vdata[:-1])

        key = op.abspath('vdata.txt')

        assert np.all(np.isclose(mesh.loadVertexData(key), vdata))
        assert np.all(np.isclose(mesh.getVertexData( key), vdata))
        assert np.all(np.isclose(mesh.loadVertexData(key, 'vdkey'), vdata))
        assert np.all(np.isclose(mesh.getVertexData(      'vdkey'), vdata))

        with pytest.raises(ValueError):
            mesh.loadVertexData('badvdata.txt')


def test_normals():

    # vertices of a cube
    verts         = np.array(CUBE_VERTICES)
    triangles_cw  = np.array(CUBE_TRIANGLES_CW)
    triangles_ccw = np.array(CUBE_TRIANGLES_CCW)
    fnormals      = np.array(CUBE_CCW_FACE_NORMALS)
    vnormals      = np.array(CUBE_CCW_VERTEX_NORMALS)

    cw_nofix  = fslmesh.Mesh(np.array(triangles_cw))
    cw_fix    = fslmesh.Mesh(np.array(triangles_cw))
    ccw_nofix = fslmesh.Mesh(np.array(triangles_ccw))
    ccw_fix   = fslmesh.Mesh(np.array(triangles_ccw))

    cw_nofix .addVertices(np.array(verts))
    cw_fix   .addVertices(np.array(verts), fixWinding=True)
    ccw_nofix.addVertices(np.array(verts))
    ccw_fix  .addVertices(np.array(verts), fixWinding=True)

    # ccw triangles should give correct
    # normals without unwinding
    assert np.all(np.isclose(cw_nofix .normals,  -fnormals))
    assert np.all(np.isclose(cw_nofix .vnormals, -vnormals))
    assert np.all(np.isclose(cw_fix   .normals,   fnormals))
    assert np.all(np.isclose(cw_fix   .vnormals,  vnormals))
    assert np.all(np.isclose(ccw_nofix.normals,   fnormals))
    assert np.all(np.isclose(ccw_nofix.vnormals,  vnormals))
    assert np.all(np.isclose(ccw_fix  .normals,   fnormals))
    assert np.all(np.isclose(ccw_fix  .vnormals,  vnormals))

    # Test standalone calcFaceNormals/
    # calcVertexNormals functions
    assert np.all(np.isclose(
        -fnormals, fslmesh.calcFaceNormals(verts, triangles_cw)))
    assert np.all(np.isclose(
        fnormals, fslmesh.calcFaceNormals(verts, triangles_ccw)))
    assert np.all(np.isclose(
        -vnormals, fslmesh.calcVertexNormals(verts, triangles_cw, -fnormals)))
    assert np.all(np.isclose(
        vnormals, fslmesh.calcVertexNormals(verts, triangles_ccw, fnormals)))


def test_needsFixing():

    verts    = np.array(CUBE_VERTICES)
    tris_cw  = np.array(CUBE_TRIANGLES_CW)
    tris_ccw = np.array(CUBE_TRIANGLES_CCW)
    fnormals = np.array(CUBE_CCW_FACE_NORMALS)
    blo      = verts.min(axis=0)
    bhi      = verts.max(axis=0)
    mesh     = fslmesh.Mesh(tris_cw, vertices=verts, fixWinding=True)

    assert not fslmesh.needsFixing(verts, tris_ccw, fnormals, blo, bhi)
    assert     fslmesh.needsFixing(verts, tris_cw, -fnormals, blo, bhi)
    assert     np.all(np.isclose(mesh.indices, tris_ccw))

    # regression: needsFixing used to use the first triangle
    # of the nearest vertex to the camera. But this will fail
    # if that triangle is facing away from the camera.
    verts = np.array([
        [ -1,    -1,   -1], # vertex 0 will be nearest the camera
        [  0.5,  -0.5,  0],
        [  1,    -1,    0],
        [  1,     1,    1],
        [  0,    -1,    1]])
    tris = np.array([
        [0, 4, 1], # first triangle will be facing away from the camera
        [0, 1, 2],
        [1, 3, 2],
        [0, 2, 4],
        [2, 3, 4],
        [1, 4, 3]])
    mesh     = fslmesh.Mesh(tris, vertices=verts, fixWinding=True)
    fnormals = fslmesh.calcFaceNormals(verts, tris)
    blo      = verts.min(axis=0)
    bhi      = verts.max(axis=0)
    assert not fslmesh.needsFixing(verts, tris, fnormals, blo, bhi)


def test_trimesh_no_trimesh():

    # Make sure trimesh and rtree
    # are imported before messing
    # with sys.modules, otherwise
    # weird things can happen.
    import trimesh
    import rtree

    mods = ['trimesh', 'rtree']

    for mod in mods:
        with mock.patch.dict('sys.modules', **{mod : None}):

            verts = np.array(CUBE_VERTICES)
            tris  = np.array(CUBE_TRIANGLES_CCW)
            mesh  = fslmesh.Mesh(tris, vertices=verts)

            assert mesh.trimesh is None
            locs, tris = mesh.rayIntersection([[0, 0, 0]], [[0, 0, 1]])
            assert locs.size == 0
            assert tris.size == 0

            nverts, idxs, dists = mesh.nearestVertex([[0, 0, 0]])
            assert nverts.size == 0
            assert idxs.size  == 0
            assert dists.size == 0

            lines, faces = mesh.planeIntersection([0, 0, 1], [0, 0, 0])
            assert lines.size == 0
            assert faces.size == 0


@pytest.mark.meshtest
def test_trimesh():

    import trimesh

    verts = np.array(CUBE_VERTICES)
    tris  = np.array(CUBE_TRIANGLES_CCW)

    mesh = fslmesh.Mesh(tris, vertices=verts)
    assert isinstance(mesh.trimesh, trimesh.Trimesh)


@pytest.mark.meshtest
def test_rayIntersection():

    verts     = np.array(CUBE_VERTICES)
    triangles = np.array(CUBE_TRIANGLES_CCW)
    mesh      = fslmesh.Mesh(triangles, vertices=verts)

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


@pytest.mark.meshtest
def test_nearestVertex():

    verts     = np.array(CUBE_VERTICES)
    triangles = np.array(CUBE_TRIANGLES_CCW)
    mesh      = fslmesh.Mesh(triangles, vertices=verts)

    nverts, nidxs, ndists = mesh.nearestVertex(verts * 2)

    assert np.all(np.isclose(nverts, verts))
    assert np.all(np.isclose(nidxs,  np.arange(len(verts))))
    assert np.all(np.isclose(ndists, np.sqrt(3)))


@pytest.mark.meshtest
def test_planeIntersection():

    verts     = np.array(CUBE_VERTICES)
    triangles = np.array(CUBE_TRIANGLES_CCW)
    mesh      = fslmesh.Mesh(triangles, vertices=verts)

    normal = [0, 0, 1]
    origin = [0, 0, 0]

    lines,  faces         = mesh.planeIntersection(normal, origin)
    lines2, faces2, dists = mesh.planeIntersection(normal,
                                                   origin,
                                                   distances=True)

    expLines = np.array([
        [[-1, -1,  0],
         [ 0, -1,  0]],
        [[ 1, -1,  0],
         [ 0, -1,  0]],

        [[ 1,  1,  0],
         [ 0,  1,  0]],

        [[-1,  1,  0],
         [ 0,  1,  0]],

        [[-1,  0,  0],
         [-1, -1,  0]],

        [[-1,  0,  0],
         [-1,  1,  0]],

        [[ 1,  0,  0],
         [ 1, -1,  0]],

        [[ 1,  0,  0],
         [ 1,  1,  0]]])

    expFaces = np.array([ 4,  5,  6,  7,  8,  9, 10, 11])
    expDists = np.array([
        [[0.5, 0,   0.5],
         [0,   0.5, 0.5]],

        [[0,   0.5, 0.5],
         [0.5, 0.5, 0]],

        [[0,   0.5, 0.5],
         [0.5, 0.5, 0]],

        [[0.5, 0.5, 0],
         [0.5, 0,   0.5]],

        [[0,   0.5, 0.5],
         [0.5, 0.5, 0]],

        [[0.5, 0,   0.5],
         [0,   0.5, 0.5]],

        [[0.5, 0.5, 0],
         [0.5, 0,   0.5]],

        [[0.5, 0,   0.5],
         [0,   0.5, 0.5]]])

    assert np.all(np.isclose(lines, lines2))
    assert np.all(np.isclose(faces, faces2))
    assert np.all(np.isclose(lines, expLines))
    assert np.all(np.isclose(faces, expFaces))
    assert np.all(np.isclose(dists, expDists))

    normal = [0, 0, 1]
    origin = [3, 3, 3]

    lines, faces, dists = mesh.planeIntersection(normal,
                                                 origin,
                                                 distances=True)

    assert lines.shape  == (0, 2, 3)
    assert faces.shape  == (0, )
    assert dists.shape  == (0, 2, 3)


def test_mesh_different_winding_orders():

    verts1    =  CUBE_VERTICES
    verts2    = -CUBE_VERTICES
    tris      =  CUBE_TRIANGLES_CCW
    trisfixed =  CUBE_TRIANGLES_CW

    mnofix = fslmesh.Mesh(tris)
    mfix   = fslmesh.Mesh(tris)

    mnofix.addVertices(verts1, key='v1', fixWinding=False)
    mnofix.addVertices(verts2, key='v2', fixWinding=False)
    mfix  .addVertices(verts1, key='v1', fixWinding=True)
    mfix  .addVertices(verts2, key='v2', fixWinding=True)
    mfix  .addVertices(verts1, key='v3', fixWinding=True, select=False)

    mnofix.vertices = 'v1'
    assert np.all(mnofix.indices == tris)
    mnofix.vertices = 'v2'
    assert np.all(mnofix.indices == tris)

    mfix.vertices = 'v1'
    assert np.all(mfix.indices == tris)
    mfix.vertices = 'v2'
    assert np.all(mfix.indices == trisfixed)
    mfix.vertices = 'v3'
    assert np.all(mfix.indices == tris)
