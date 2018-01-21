#!/usr/bin/env python
#
# test_vtk.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import            tempfile
import            shutil
import os.path as op

import numpy as np

import pytest

import fsl.data.vtk as fslvtk


datadir = op.join(op.dirname(__file__), 'testdata')


def test_create_vtkmesh():

    # Test:
    #  - create from file
    #  - create from inmem data
    testbase = 'test_mesh.vtk'
    testfile = op.join(datadir, testbase)

    verts, lens, indices = fslvtk.loadVTKPolydataFile(testfile)

    mesh = fslvtk.VTKMesh(testfile)

    assert mesh.name       == testbase
    assert mesh.dataSource == testfile

    assert mesh.vertices.shape == (642,  3)
    assert mesh.indices.shape  == (1280, 3)

    minbounds = np.array([ 59.50759888,  88.43039703,  72.10890198])
    maxbounds = np.array([ 77.72619629, 128.40600586,  94.82050323])

    meshBounds = mesh.bounds

    assert np.all(np.isclose(meshBounds[0], minbounds))
    assert np.all(np.isclose(meshBounds[1], maxbounds))


def test_loadVTKPolydataFile():

    testfile = op.join(datadir, 'test_mesh.vtk')
    verts, lens, indices = fslvtk.loadVTKPolydataFile(testfile)

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
            fslvtk.getFIRSTPrefix(f)

    for fname, expected in passes:
        assert fslvtk.getFIRSTPrefix(fname) == expected



def test_findReferenceImage():

    testdir  = tempfile.mkdtemp()
    vtkfiles = ['struc-L_Thal_first.vtk',
                'struc_first-L_Thal_first.vtk']

    assert fslvtk.findReferenceImage('nofile') is None

    try:

        for fname in vtkfiles:

            assert fslvtk.findReferenceImage(fname) is None

            prefix   = fslvtk.getFIRSTPrefix(fname)
            imgfname = op.join(testdir, '{}.nii.gz'.format(prefix))
            fname    = op.join(testdir, fname)

            with open(fname,    'wt') as f: f.write(fname)
            with open(imgfname, 'wt') as f: f.write(imgfname)

            assert fslvtk.findReferenceImage(fname) == imgfname

    finally:
        shutil.rmtree(testdir)
