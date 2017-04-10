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
import            pytest

import fsl.data.mesh as fslmesh


datadir = op.join(op.dirname(__file__), 'testdata')


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
