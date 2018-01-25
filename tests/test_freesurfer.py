 #!/usr/bin/env python
#
# test_freesurfer.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os
import os.path as op
import shutil

import numpy as np

import nibabel             as nib
import nibabel.freesurfer  as nibfs

import pytest

import fsl.data.freesurfer as fslfs

from .test_mesh import (CUBE_VERTICES, CUBE_TRIANGLES_CCW)

from . import tempdir, touch


def gen_freesurfer_geometry(fname, verts, tris):
    nibfs.write_geometry(fname, verts, tris)

def gen_freesurfer_morph(fname, vdata):
    nibfs.write_morph_data(fname, vdata)

def gen_freesurfer_label(fname, verts, vdata):
    with open(fname, 'wt') as f:
        f.write('# Comment\n')
        f.write('{}\n'.format(len(verts)))
        for v, vd in zip(verts, vdata):
            f.write('{} 0.0 0.0 0.0 {}\n'.format(v, vd))


def gen_freesurfer_annot(fname, labels, rgbal, names):
    nibfs.write_annot(fname, labels, rgbal, names)

def test_FreesurferMesh_create():

    verts = np.array(CUBE_VERTICES)
    tris  = np.array(CUBE_TRIANGLES_CCW)

    with tempdir():
        gen_freesurfer_geometry('lh.pial', verts, tris)

        mesh = fslfs.FreesurferMesh('lh.pial')

        assert mesh.name == 'lh.pial'
        assert np.all(np.isclose(mesh.vertices, verts))
        assert np.all(np.isclose(mesh.indices,  tris))


def test_FreesurferMesh_create_loadall():

    verts = np.array(CUBE_VERTICES)
    tris  = np.array(CUBE_TRIANGLES_CCW)

    with tempdir():
        gen_freesurfer_geometry('lh.pial', verts, tris)

        vertSets = ['lh.orig', 'lh.white', 'lh.inflated']
        for vs in vertSets:
            shutil.copy('lh.pial', vs)

        mesh = fslfs.FreesurferMesh('lh.pial', loadAll=True)

        assert list(sorted(mesh.vertexSets())) == \
            list(sorted([op.abspath(p) for p in ['lh.pial'] + vertSets]))


def test_loadVertices():

    verts = np.array(CUBE_VERTICES)
    tris  = np.array(CUBE_TRIANGLES_CCW)

    with tempdir():
        gen_freesurfer_geometry('lh.pial', verts,     tris)
        gen_freesurfer_geometry('rh.pial', verts * 2, tris)

        # bad
        gen_freesurfer_geometry('lh.orig', verts[:-1, :], tris)

        np.savetxt('verts.txt', verts * 3)

        mesh = fslfs.FreesurferMesh('lh.pial')

        assert np.all(np.isclose(mesh.loadVertices('rh.pial'),   verts * 2))
        assert np.all(np.isclose(mesh.loadVertices('verts.txt'), verts * 3))

        with pytest.raises(ValueError):
            mesh.loadVertices('lh.orig')


def test_loadVertexData_morph():

    verts = np.array(CUBE_VERTICES)
    tris  = np.array(CUBE_TRIANGLES_CCW)

    with tempdir():
        vdata1 = np.random.randint(1, 100, verts.shape[0])
        vdata2 = np.random.randint(1, 100, verts.shape[0])
        vdata3 = np.random.randint(1, 100, verts.shape[0])

        gen_freesurfer_geometry('lh.pial', verts, tris)

        gen_freesurfer_morph('lh.curv',      vdata1)
        gen_freesurfer_morph('lh.thickness', vdata2)
        np.savetxt(          'vdata.txt',    vdata3)

        # bad
        gen_freesurfer_morph('rh.sulc', vdata2[:-1])

        mesh = fslfs.FreesurferMesh('lh.pial')

        assert np.all(np.isclose(mesh.loadVertexData('lh.curv'),      vdata1.reshape(-1, 1)))
        assert np.all(np.isclose(mesh.loadVertexData('lh.thickness'), vdata2.reshape(-1, 1)))
        assert np.all(np.isclose(mesh.loadVertexData('vdata.txt'),    vdata3.reshape(-1, 1)))

        with pytest.raises(ValueError):
            mesh.loadVertexData('rh.sulc')


def test_loadVertexData_label():

    verts  = np.array(CUBE_VERTICES)
    tris   = np.array(CUBE_TRIANGLES_CCW)
    nverts = verts.shape[0]

    with tempdir():

        # Currently, vertex scalar data is
        # ignored by the FreesurferMesh class
        lverts = np.random.choice(np.arange(nverts), 4)
        vdata  = np.random.randint(1, 100, 4)

        gen_freesurfer_geometry('lh.pial', verts, tris)
        gen_freesurfer_label('lh.vdata.label', lverts, vdata)

        mesh = fslfs.FreesurferMesh('lh.pial')

        exp = np.zeros((nverts, 1))
        exp[lverts, :] = 1

        assert np.all(np.isclose(mesh.loadVertexData('lh.vdata.label'), exp))


def test_loadVertexData_mgh():

    verts  = np.array(CUBE_VERTICES)
    tris   = np.array(CUBE_TRIANGLES_CCW)
    nverts = verts.shape[0]

    with tempdir():

        data = np.random.randint(1, 100, (nverts, 1, 1), dtype=np.int32)
        img  = nib.freesurfer.mghformat.MGHImage(data, np.eye(4))

        nib.save(img, 'lh.vdata.mgh')

        gen_freesurfer_geometry('lh.pial', verts, tris)

        mesh = fslfs.FreesurferMesh('lh.pial')
        assert np.all(np.isclose(mesh.loadVertexData('lh.vdata.mgh'), data.reshape(-1, 1)))







def test_loadVertexData_annot():

    import nibabel.info as nibinfo

    # assume nibabel 2.*
    # nibabel 2.2.1 is broken w.r.t. .annot files.
    if nibinfo._version_minor == 2 and nibinfo._version_micro <= 1:
        return

    verts = np.array(CUBE_VERTICES)
    tris  = np.array(CUBE_TRIANGLES_CCW)

    with tempdir():
        nlabels      = 3
        names        = ['label {}'.format(l) for l in range(1, nlabels + 1)]
        rgba         = np.random.randint(0, 255, (nlabels, 4), dtype=np.int32)
        labels       = list(range(nlabels)) + list(np.random.randint(0, nlabels, verts.shape[0] - nlabels))
        labels       = np.array(labels, dtype=np.int32)

        np.random.shuffle(labels)

        gen_freesurfer_geometry('lh.pial', verts, tris)
        gen_freesurfer_annot('lh.aparc.annot', labels, rgba, names)

        mesh = fslfs.FreesurferMesh('lh.pial')

        vdfile = op.abspath('lh.aparc.annot')

        loaded = mesh.loadVertexData(vdfile)
        ergbal, enames = mesh.getVertexDataColourTable(vdfile)

        assert np.all(np.isclose(loaded, labels.reshape(-1, 1)))
        assert list(enames) == list(names)
        assert np.all(np.isclose(ergbal[:, :4], rgba))


def test_relatedGeometryFiles():

    with tempdir():
        touch('not.geometry')
        touch('lh.pial')
        touch('lh.sphere')
        touch('lhinflated')
        touch('rh.blob')
        touch('rhsphere')
        touch('rh.pial')
        touch('rh.orig')
        touch('rh.white')
        touch('rh.blob')

        def a(paths):
            return [op.abspath(p) for p in paths]

        assert        fslfs.relatedGeometryFiles('not.geometry') == []
        assert        fslfs.relatedGeometryFiles('lh.blob')      == []
        assert        fslfs.relatedGeometryFiles('lh.pial')      == a(['lh.sphere'])
        assert        fslfs.relatedGeometryFiles('lh.sphere')    == a(['lh.pial'])
        assert        fslfs.relatedGeometryFiles('rh.blob')      == []
        assert sorted(fslfs.relatedGeometryFiles('rh.pial'))     == a(['rh.orig', 'rh.white'])
        assert sorted(fslfs.relatedGeometryFiles('rh.orig'))     == a(['rh.pial', 'rh.white'])
        assert sorted(fslfs.relatedGeometryFiles('rh.white'))    == a(['rh.orig', 'rh.pial'])


def test_relatedVertexDataFiles():
    with tempdir():
        touch('lh.pial')
        touch('rh.pial')
        touch('rh.area')
        touch('foo.mgz')
        touch('lh.blob.mgz')
        touch('lh.blob.mgh')
        touch('lhthickness')
        touch('lh.thickness')
        touch('lh.curv')
        touch('lh.area')
        touch('lh.sulc')
        touch('lh.what.label')
        touch('lh.aparc.annot')

        def a(paths):
            return [op.abspath(p) for p in paths]

        assert fslfs.relatedVertexDataFiles('rh.pial') == a(['rh.area'])
        assert fslfs.relatedVertexDataFiles('rh.area') == []

        exp = sorted(['lh.blob.mgz',
                      'lh.blob.mgh',
                      'lh.thickness',
                      'lh.curv',
                      'lh.area',
                      'lh.sulc',
                      'lh.what.label',
                      'lh.aparc.annot'])

        assert sorted(fslfs.relatedVertexDataFiles('lh.pial')) == a(exp)


def test_findReferenceImage():
    with tempdir():

        surf = op.join('surf', 'lh.pial')
        t1   = op.join('mri',  'T1.mgz')

        os.mkdir('surf')
        os.mkdir('mri')
        touch(surf)
        touch(t1)

        assert fslfs.findReferenceImage(surf) == op.abspath(t1)

        os.remove(t1)

        assert fslfs.findReferenceImage(surf) is None
