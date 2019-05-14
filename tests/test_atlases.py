#!/usr/bin/env python
#
# test_atlases.py - Unit tests for fsl.data.atlases. This module tests
#                   atlas management - see test_atlases_query.py for
#                   atlas query tests.
#
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import              os
import os.path   as op
import numpy     as np

import mock
import pytest

import tests
import fsl.utils.transform      as transform
import fsl.utils.image.resample as resample
import fsl.data.atlases         as atlases
import fsl.data.image           as fslimage


datadir = op.join(op.dirname(__file__), 'testdata')


pytestmark = pytest.mark.fsltest


def setup_module():
    if os.environ.get('FSLDIR', None) is None:
        raise Exception('FSLDIR is not set - atlas tests cannot be run')



dummy_atlas_desc = """<?xml version="1.0" encoding="ISO-8859-1"?>
<atlas version="1.0">
  <header>
    <name>{name}</name>
    <shortname>{shortname}</shortname>
    <type>Label</type>
    <images>
      <imagefile>/{shortname}/{filename}</imagefile>
       <summaryimagefile>/{shortname}/My{filename}</summaryimagefile>
    </images>
  </header>
  <data>
    <label index="1" x="5" y="5" z="5">First region</label>
    <label index="2" x="6" y="6" z="6">Second region</label>
  </data>
</atlas>
"""
def _make_dummy_atlas(savedir, name, shortName, filename):
    mladir     = op.join(savedir, shortName)
    mlaxmlfile = op.join(savedir, '{}.xml'.format(shortName))
    mlaimgfile = op.join(savedir, shortName, '{}.nii.gz'.format(filename))

    data = np.zeros((10, 10, 10))
    data[5, 5, 5] = 1
    data[6, 6, 6] = 2

    img = fslimage.Image(data, xform=np.eye(4))

    os.makedirs(mladir)
    img.save(mlaimgfile)

    with open(mlaxmlfile, 'wt') as f:
        desc = dummy_atlas_desc.format(
            name=name,
            shortname=shortName,
            filename=filename)
        f.write(desc)

    return mlaxmlfile


def test_registry():
    registry = atlases.registry
    registry.rescanAtlases()

    assert len(registry.listAtlases()) > 0
    assert registry.hasAtlas('harvardoxford-cortical')

    adesc = registry.getAtlasDescription('harvardoxford-cortical')

    assert isinstance(adesc, atlases.AtlasDescription)


    with pytest.raises(Exception):
        registry.getAtlasDescription('non-existent-atlas')


def test_AtlasDescription():
    registry = atlases.registry
    registry.rescanAtlases()

    tal  = registry.getAtlasDescription('talairach')
    cort = registry.getAtlasDescription('harvardoxford-cortical')

    assert str(tal) == 'AtlasDescription(talairach)'
    assert str(cort) == 'AtlasDescription(harvardoxford-cortical)'

    assert tal.atlasID == 'talairach'
    assert tal.name    == 'Talairach Daemon Labels'
    assert tal.specPath
    assert tal.atlasType == 'label'
    nimages = len(tal.images)
    assert nimages                >  0
    assert len(tal.summaryImages) >  0
    assert len(tal.pixdims)       == nimages
    assert len(tal.xforms)        == nimages
    assert len(tal.labels)        >  0

    for lbl in tal.labels:
        lbl.name
        lbl.index
        lbl.x
        lbl.y
        lbl.z

    assert cort.atlasID == 'harvardoxford-cortical'
    assert cort.name    == 'Harvard-Oxford Cortical Structural Atlas'
    assert cort.specPath
    assert cort.atlasType == 'probabilistic'
    nimages = len(cort.images)
    assert nimages                 >  0
    assert len(cort.summaryImages) >  0
    assert len(cort.pixdims)       == nimages
    assert len(cort.xforms)        == nimages
    assert len(cort.labels)        >  0

    for lbl in cort.labels:
        lbl.name
        lbl.index
        lbl.x
        lbl.y
        lbl.z

    with pytest.raises(Exception):
        registry.getAtlasDescription('non-existent-atlas')


def test_add_remove_atlas():

    with tests.testdir() as testdir:

        added   = [False]
        removed = [False]
        reg     = atlases.registry
        reg.rescanAtlases()

        def atlas_added(r, topic, val):
            assert topic == 'add'
            assert r is reg
            assert val.atlasID == 'mla'
            added[0] = True

        def atlas_removed(r, topic, val):
            assert r is reg
            assert topic == 'remove'
            assert val.atlasID == 'mla'
            removed[0] = True

        xmlfile = _make_dummy_atlas(testdir,
                                    'My Little Atlas',
                                    'MLA',
                                    'MyLittleAtlas')

        reg.register('added',   atlas_added,   topic='add')
        reg.register('removed', atlas_removed, topic='remove')

        # add an atlas with an ID that is taken
        with pytest.raises(KeyError):
            reg.addAtlas(xmlfile, atlasID='harvardoxford-cortical')

        reg.addAtlas(xmlfile)

        assert added[0]

        assert reg.hasAtlas('mla')

        reg.removeAtlas('mla')

        assert removed[0]


def test_extra_atlases():

    with tests.testdir() as testdir:

        atlas1spec = _make_dummy_atlas(
            testdir, 'My atlas 1', 'myatlas1', 'MyAtlas1')
        atlas2spec = _make_dummy_atlas(
            testdir, 'My atlas 2', 'myatlas2', 'MyAtlas2')

        badspec = op.join(testdir, 'badSpec.xml')
        with open(badspec, 'wt') as f:
            f.write('Bwahahahah!')

        extraAtlases = ':'.join([
            'myatlas1={}'.format(atlas1spec),
            'myatlas2={}'.format(atlas2spec),
            'badatlas1=non-existent-path',
            'badatlas2={}'.format(badspec)
        ])

        with mock.patch('fsl.data.atlases.fslsettings.read',
                        return_value=extraAtlases), \
             mock.patch('fsl.data.atlases.fslsettings.write',
                        return_value=None):

            reg = atlases.registry
            reg.rescanAtlases()

            assert     reg.hasAtlas('myatlas1')
            assert     reg.hasAtlas('myatlas2')
            assert not reg.hasAtlas('badatlas1')
            assert not reg.hasAtlas('badatlas2')


def test_load_atlas():

    reg = atlases.registry
    reg.rescanAtlases()

    probatlas    = reg.loadAtlas('harvardoxford-cortical',
                                 calcRange=False, loadData=False)
    probsumatlas = reg.loadAtlas('harvardoxford-cortical', loadSummary=True)
    lblatlas     = reg.loadAtlas('talairach')

    assert isinstance(probatlas,    atlases.ProbabilisticAtlas)
    assert isinstance(probsumatlas, atlases.LabelAtlas)
    assert isinstance(lblatlas,     atlases.LabelAtlas)


def test_get():

    reg = atlases.registry
    reg.rescanAtlases()

    probatlas = reg.loadAtlas('harvardoxford-cortical')
    lblatlas = reg.loadAtlas('talairach')
    for atlas in (probatlas, lblatlas):
        for idx, label in enumerate(atlas.desc.labels[:10]):
            target = probatlas[..., idx] if atlas is probatlas else lblatlas.data == label.value
            assert (target == atlas.get(label).data).all()
            assert label.name == atlas.get(label).name
            assert (target == atlas.get(index=label.index).data).all()
            assert (target == atlas.get(value=label.value).data).all()
            assert (target == atlas.get(name=label.name).data).all()


def test_find():

    reg = atlases.registry
    reg.rescanAtlases()

    probatlas    = reg.loadAtlas('harvardoxford-cortical',
                                 calcRange=False, loadData=False)
    probsumatlas = reg.loadAtlas('harvardoxford-cortical', loadSummary=True)
    lblatlas     = reg.loadAtlas('talairach')

    for atlas in [probatlas, probsumatlas, lblatlas]:
        labels = atlas.desc.labels

        for label in labels:

            assert atlas     .find(value=label.value) == label
            assert atlas     .find(index=label.index) == label
            assert atlas     .find(name=label.name) == label
            assert atlas.desc.find(value=label.value) == label
            assert atlas.desc.find(index=label.index) == label
            assert atlas.desc.find(name=label.name) == label

            if atlas is not lblatlas:
                # lblatlas has a lot of very similar label names
                assert atlas     .find(name=label.name[:-2]) == label
                assert atlas.desc.find(name=label.name[:-2]) == label

        with pytest.raises(ValueError):
            atlas.find()
        with pytest.raises(ValueError):
            atlas.find(index=1, value=1)
        with pytest.raises(ValueError):
            atlas.find(index=1, name=1)
        with pytest.raises(ValueError):
            atlas.find(value=1, name=1)

        with pytest.raises(IndexError):
            atlas.find(index=len(labels))
        with pytest.raises(IndexError):
            atlas.find(name='InvalidROI')
        with pytest.raises(IndexError):
            atlas.find(name='')

        maxval = max([l.value for l in labels])
        with pytest.raises(KeyError):
            atlas.find(value=maxval + 1)


def test_prepareMask():

    reg = atlases.registry
    reg.rescanAtlases()

    probatlas    = reg.loadAtlas('harvardoxford-cortical',
                                 loadData=False, calcRange=False)
    probsumatlas = reg.loadAtlas('harvardoxford-cortical', loadSummary=True)
    lblatlas     = reg.loadAtlas('talairach')

    for atlas in [probatlas, probsumatlas, lblatlas]:

        ashape        = list(atlas.shape[:3])
        m2shape       = [s * 1.5 for s in ashape]

        goodmask1     = fslimage.Image(
            np.array(np.random.random(ashape), dtype=np.float32),
            xform=atlas.voxToWorldMat)

        goodmask2, xf = resample.resample(goodmask1, m2shape)
        goodmask2     = fslimage.Image(goodmask2, xform=xf)

        wrongdims     = fslimage.Image(
            np.random.random(list(ashape) + [2]))
        wrongspace    = fslimage.Image(
            np.random.random((20, 20, 20)),
            xform=transform.concat(atlas.voxToWorldMat, np.diag([2, 2, 2, 1])))

        with pytest.raises(atlases.MaskError):
            atlas.prepareMask(wrongdims)
        with pytest.raises(atlases.MaskError):
            atlas.prepareMask(wrongspace)

        assert list(atlas.prepareMask(goodmask1).shape) == ashape
        assert list(atlas.prepareMask(goodmask2).shape) == ashape
