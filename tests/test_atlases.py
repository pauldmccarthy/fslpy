#!/usr/bin/env python
#
# test_atlases.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import              os
import os.path   as op
import itertools as it
import numpy     as np

import mock
import pytest

import tests
import fsl.data.atlases as atlases
import fsl.data.image   as fslimage


datadir = op.join(op.dirname(__file__), 'testdata')


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

    probatlas    = reg.loadAtlas('harvardoxford-cortical')
    probsumatlas = reg.loadAtlas('harvardoxford-cortical', loadSummary=True)
    lblatlas     = reg.loadAtlas('talairach')

    assert isinstance(probatlas,    atlases.ProbabilisticAtlas)
    assert isinstance(probsumatlas, atlases.LabelAtlas)
    assert isinstance(lblatlas,     atlases.LabelAtlas)


def test_find():

    reg = atlases.registry
    reg.rescanAtlases

    probatlas    = reg.loadAtlas('harvardoxford-cortical')
    probsumatlas = reg.loadAtlas('harvardoxford-cortical', loadSummary=True)
    lblatlas     = reg.loadAtlas('talairach')

    for atlas in [probatlas, probsumatlas, lblatlas]:
        labels = atlas.desc.labels

        for label in labels:

            assert atlas     .find(value=label.value) == label
            assert atlas     .find(index=label.index) == label
            assert atlas.desc.find(value=label.value) == label
            assert atlas.desc.find(index=label.index) == label

        with pytest.raises(ValueError):
            atlas.find()
        with pytest.raises(ValueError):
            atlas.find(index=1, value=1)

        with pytest.raises(IndexError):
            atlas.find(index=len(labels))

        maxval = max([l.value for l in labels])
        with pytest.raises(KeyError):
            atlas.find(value=maxval + 1)


def test_label_atlas_coord():
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
        assert atlas.label(     coords) == expected
        assert atlas.coordLabel(coords) == expected

    assert atlas.label([ 999,  999,  999]) is None
    assert atlas.label([-999, -999, -999]) is None

    # Summary atlas (a thresholded probabilistic atlas)
    atlas    = reg.loadAtlas('harvardoxford-cortical', loadSummary=True)
    hoctests = [
        ([-23,  58,  20], 1),
        ([-23,  27, -20], 33),
        ([-37, -75,  29], 22),
        ([ -1,  37,   6], 29),
        ([ 54, -44, -27], 16)]

    for coords, expected in hoctests:
        assert atlas.label(     coords) == expected
        assert atlas.coordLabel(coords) == expected

    assert atlas.label([ 999,  999,  999]) is None
    assert atlas.label([-999, -999, -999]) is None


def test_prob_atlas_coord():
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


def test_prob_atlas_mask():
    # test the maskProportions function
    reg = atlases.registry
    reg.rescanAtlases()

    hotests = [
        'test_atlases_ho_mask_1mm',
        'test_atlases_ho_mask_2mm'
    ]
    resolutions = [1, 2]

    for prefix, res in it.product(hotests, resolutions):
        maskfile    = op.join(datadir, '{}.nii.gz'   .format(prefix))
        resultsfile = op.join(datadir, '{}_res{}.txt'.format(prefix, res))
        atlas       = reg.loadAtlas('harvardoxford-cortical', resolution=res)
        mask        = fslimage.Image(maskfile)

        props  = atlas.maskProportions(mask)
        props2 = atlas.proportions(mask)

        expected = np.loadtxt(resultsfile)
        expvols  = list(expected[:, 0])
        expprops = list(expected[:, 1])

        assert np.all(np.isclose(props,  props2))
        for i in range(len(props)):
            try:
                expi = expvols.index(i)
                assert np.isclose(props[i], expprops[expi])
            except ValueError:
                assert np.isclose(props[i], 0)



def test_summary_atlas_mask():
    # test the maskLabels function on a probabilistic label atlas
    reg = atlases.registry
    reg.rescanAtlases()

    hotests = [
        'test_atlases_ho_mask_1mm',
        'test_atlases_ho_mask_2mm'
    ]
    resolutions = [1, 2]

    for prefix, res in it.product(hotests, resolutions):
        maskfile    = op.join(datadir, '{}.nii.gz'           .format(prefix))
        resultsfile = op.join(datadir, '{}_res{}_summary.txt'.format(prefix,
                                                                     res))
        atlas       = reg.loadAtlas('harvardoxford-cortical',
                                    loadSummary=True,
                                    resolution=res)
        mask        = fslimage.Image(maskfile)

        labels,  props  = atlas.maskLabel(mask)
        labels2, props2 = atlas.label(    mask)

        expected  = np.loadtxt(resultsfile)
        explabels = list(expected[:, 0])
        expprops  = list(expected[:, 1])

        assert np.all(np.isclose(labels, labels2))
        assert np.all(np.isclose(props,  props2))
        assert np.all(np.isclose(labels, explabels))
        assert np.all(np.isclose(props,  expprops))


def test_label_atlas_mask():
    # Test the maskLabel function
    reg = atlases.registry
    reg.rescanAtlases()

    taltests = [
        'test_atlases_tal_mask_1mm',
        'test_atlases_tal_mask_2mm'
    ]
    resolutions = [1, 2]

    for prefix, res in it.product(taltests, resolutions):
        maskfile    = op.join(datadir, '{}.nii.gz'   .format(prefix))
        resultsfile = op.join(datadir, '{}_res{}.txt'.format(prefix, res))
        atlas       = reg.loadAtlas('talairach', resolution=res)
        mask        = fslimage.Image(maskfile)

        labels, props   = atlas.maskLabel(mask)
        labels2, props2 = atlas.label(mask)

        expected  = np.loadtxt(resultsfile)
        explabels = expected[:, 0]
        expprops  = expected[:, 1]

        assert np.all(np.isclose(labels, labels2))
        assert np.all(np.isclose(props,  props2))
        assert np.all(np.isclose(labels, explabels))
        assert np.all(np.isclose(props,  expprops))
