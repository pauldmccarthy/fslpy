#!/usr/bin/env python
#
# test_atlases.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import            os
import os.path as op
import numpy   as np

import pytest

import tests
import fsl.data.atlases as atlases
import fsl.data.image   as fslimage


def setup_module():
    if os.environ.get('FSLDIR', None) is None:
        raise Exception('FSLDIR is not set - atlas tests cannot be run')


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



dummy_atlas_desc = """<?xml version="1.0" encoding="ISO-8859-1"?>
<atlas version="1.0">
  <header>
    <name>My Little Atlas</name>
    <shortname>MLA</shortname>
    <type>Label</type>
    <images>
      <imagefile>/MLA/MyLittleAtlas</imagefile>
       <summaryimagefile>/MLA/MyLittleAtlas</summaryimagefile>
    </images>
  </header>
  <data>
    <label index="1" x="5" y="5" z="5">First little region</label>
    <label index="2" x="6" y="6" z="6">Second little region</label>
  </data>
</atlas>
"""


def test_add_remove_atlas():

    with tests.testdir() as testdir:

        mladir     = op.join(testdir, 'MLA')
        mlaxmlfile = op.join(testdir, 'MLA.xml')
        mlaimgfile = op.join(testdir, 'MLA', 'MyLittleAtlas.nii.gz')

        def _make_dummy_atlas():

            data = np.zeros((10, 10, 10))
            data[5, 5, 5] = 1
            data[6, 6, 6] = 2

            img = fslimage.Image(data, xform=np.eye(4))

            os.makedirs(mladir)
            img.save(mlaimgfile)

            with open(mlaxmlfile, 'wt') as f:
                f.write(dummy_atlas_desc)

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

        _make_dummy_atlas()

        reg.register('added',   atlas_added,   topic='add')
        reg.register('removed', atlas_removed, topic='remove')

        # add an atlas with an ID that is taken
        with pytest.raises(Exception):
            reg.addAtlas(mlaxmlfile, atlasID='harvardoxford-cortical')

        reg.addAtlas(mlaxmlfile)

        assert added[0]

        assert reg.hasAtlas('mla')

        reg.removeAtlas('mla')

        assert removed[0]


def test_load_atlas():

    reg = atlases.registry
    reg.rescanAtlases()

    probatlas    = reg.loadAtlas('harvardoxford-cortical')
    probsumatlas = reg.loadAtlas('harvardoxford-cortical', loadSummary=True)
    lblatlas     = reg.loadAtlas('talairach')

    assert isinstance(probatlas,    atlases.ProbabilisticAtlas)
    assert isinstance(probsumatlas, atlases.LabelAtlas)
    assert isinstance(lblatlas,     atlases.LabelAtlas)


def test_label_atlas():
    reg = atlases.registry
    reg.rescanAtlases()

    # Label atlas (i.e. not a probabilistic atlas)
    atlas = reg.loadAtlas('talairach')

    # coordinates are MNI152
    taltests = [
        ([ 23, -37, -22], 89),
        ([-29, -78, -22], 157),
        ([ 48,  39, -22], 196),
        ([  6,  56,  37], 1034),
        ([  6, -78,  50], 862)]

    for coords, expected in taltests:
        assert atlas.label(coords) == expected

    assert atlas.label([ 999,  999,  999]) is None
    assert atlas.label([-999, -999, -999]) is None

    # Summary atlas (a thresholded probabilistic atlas)
    atlas    = reg.loadAtlas('harvardoxford-cortical', loadSummary=True)
    hoctests = [
        ([-23,  58,  20], 0),
        ([-23,  27, -20], 32),
        ([-37, -75,  29], 21),
        ([ -1,  37,   6], 28),
        ([ 54, -44, -27], 15)]

    for coords, expected in hoctests:
        assert atlas.label(coords) == expected

    assert atlas.label([ 999,  999,  999]) is None
    assert atlas.label([-999, -999, -999]) is None


def test_prob_atlas():
    reg = atlases.registry
    reg.rescanAtlases()

    atlas = reg.loadAtlas('harvardoxford-cortical')

    assert len(atlas.proportions([ 999,  999,  999])) == 0
    assert len(atlas.proportions([-999, -999, -999])) == 0

    # Coordinates are MNI152
    # Expected proportions are lists of (volume, proportion) tuples
    hoctests = [
        ([ 41, -14,  18], [( 1,  5), (41, 74), (42, 10)]),
        ([ 41, -72,  34], [(21, 72)]),
        ([-39, -21,  58], [(6,  39), (16, 19)]),
        ([-37, -28,  13], [(42,  4), (44, 48), (45, 19)]),
        ([-29, -42, -11], [(34, 21), (35, 23), (37, 26), (38, 24)])]

    for coords, expected in hoctests:
        
        result  = atlas.proportions(coords)
        expidxs = [e[0] for e in expected]
        
        for i in range(len(result)):
            if i not in expidxs:
                assert result[i] == 0

        for expidx, expprob in expected:
            assert result[expidx] == expprob
