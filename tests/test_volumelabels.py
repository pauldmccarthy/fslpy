#!/usr/bin/env python
#
# test_volumelabels.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path   as op
import itertools as it
import              textwrap

import pytest

import tests
import fsl.data.fixlabels    as fixlbls
import fsl.data.volumelabels as vollbls


def test_add_get_hasLabel():
    
    ncomps = 5
    labels = ['Label {}'.format(i) for i in range(ncomps)]
    lowers = [lbl.lower()          for lbl in labels]
    lblobj = vollbls.VolumeLabels(ncomps)

    called = [False]
    
    def labelAdded(lo, topic, value):
        called[0] = True

    lblobj.register('callback', labelAdded, topic='added')

    for i in range(ncomps):
        
        called[0] = False
        
        assert lblobj.addLabel(i, labels[i])
        assert called[0]
        assert lblobj.getLabels(i)              == [lowers[i]]
        assert lblobj.getDisplayLabel(lowers[i]) == labels[i]

        assert lblobj.hasLabel(i, labels[i])
        assert lblobj.hasLabel(i, lowers[i])

        # Attempt to add the same label should
        # return False
        called[0] = False
        assert not lblobj.addLabel(i, labels[i])
        assert not called[0]
        
        # Labels are case insensitive
        assert not lblobj.addLabel(i, lowers[i])
        assert not called[0]

    assert sorted(lblobj.getAllLabels()) == lowers


def test_removeLabel():
    
    ncomps = 5
    labels = ['Label {}'.format(i) for i in range(ncomps)]
    lowers = [lbl.lower()          for lbl in labels]
    lblobj = vollbls.VolumeLabels(ncomps)

    for i in range(ncomps):
        lblobj.addLabel(i, labels[i])

    called = [False]
    
    def removed(*a):
        called[0] = True

    lblobj.register('callback', removed, topic='removed')


    assert not lblobj.removeLabel(0, 'notalabel')
    assert not called[0]

    for i in range(ncomps):

        called[0] = False
        assert lblobj.removeLabel(i, labels[i])
        assert called[0] 
        
        assert lblobj.getLabels(i) == []
        assert sorted(lblobj.getAllLabels()) == lowers[i + 1:]


def test_clearLabels():
    
    ncomps = 5
    labels = [('Label {}'.format(i), 'Label b')
              for i in range(ncomps)]
    lowers = [[l.lower() for l in ll] for ll in labels]
    lblobj = vollbls.VolumeLabels(ncomps)

    for i in range(ncomps):
        for l in labels[i]:
            lblobj.addLabel(i, l)

    calledValue = []
    
    def removed(lo, topic, value):
        calledValue.append(value)

    lblobj.register('callback', removed, topic='removed')

    expectedAllLabels = list(it.chain(*[list(l) for l in lowers]))

    for i in range(ncomps):

        calledValue = []
        lblobj.clearLabels(i)
        assert calledValue[0] == list(zip([i, i], lowers[i]))
        assert lblobj.getLabels(i) == []

        [expectedAllLabels.remove(l) for l in lowers[i]]
        assert sorted(lblobj.getAllLabels()) == sorted(set(expectedAllLabels))


def test_add_get_hasComponents():

    ncomps = 5
    labels = ['label a', 'label b', 'label c', 'label d', 'label e']
    lblobj = vollbls.VolumeLabels(ncomps)

    called = [False]
    
    def labelAdded(lo, topic, value):
        called[0] = True

    lblobj.register('callback', labelAdded, topic='added')

    for i in range(ncomps):
        
        called[0] = False
        assert lblobj.addComponent(labels[i], i)
        assert called[0]
        assert lblobj.hasComponent(labels[i], i)
        assert lblobj.hasLabel(    i, labels[i])
        assert lblobj.getComponents(labels[i]) == [i]

        called[0] = False
        assert not lblobj.addComponent(labels[i], i)
        assert not called[0]


def test_removeComponent():
    ncomps = 5
    labels = ['label a', 'label b', 'label c', 'label d', 'label e']
    lblobj = vollbls.VolumeLabels(ncomps)

    called = [False]

    for i in range(ncomps):
        lblobj.addLabel(i, labels[i])

    def removed(*a):
        called[0] = True

    lblobj.register('callback', removed, topic='removed')

    assert not lblobj.removeComponent('notalabel', 0)
    assert not called[0]

    for i in range(ncomps):

        called[0] = False
        assert lblobj.removeComponent(labels[i], i)
        assert called[0] 
        
        assert lblobj.getComponents(labels[i]) == []
        assert sorted(lblobj.getAllLabels()) == labels[i + 1:]


def test_clearComponents():

    ncomps = 5
    labels = [('label {}'.format(i), 'label b') for i in range(ncomps)]
    lblobj = vollbls.VolumeLabels(ncomps)

    for i in range(ncomps):
        for l in labels[i]:
            lblobj.addLabel(i, l)

    calledValue = []
    
    def removed(lo, topic, value):
        calledValue.append(value)

    lblobj.register('callback', removed, topic='removed')

    lblobj.clearComponents('label b')
    assert sorted(calledValue[0]) == list(zip(list(range(ncomps)), ['label b'] * ncomps))
    assert sorted(lblobj.getAllLabels()) == [l[0] for l in labels]

    # expectedAllLabels = list(it.chain(*[list(l) for l in lowers]))

    labels = [l[0] for l in labels]

    for i in range(ncomps):
        
        calledValue = []
        
        lblobj.clearComponents(labels[i])
        
        assert calledValue[0]                  == [(i, labels[i])]
        assert lblobj.getComponents(labels[i]) == []
        assert lblobj.getLabels(i)             == []

        assert sorted(lblobj.getAllLabels()) == labels[i + 1:]


def test_load_fixfile_long():

    contents = """
    path/to/analysis.ica
    1, Signal, False
    2, Unknown, False
    3, Movement, True
    4, Unclassified Noise, Random label, True
    [3, 4]
    """.strip()

    expected = [['signal'],
                ['unknown'],
                ['movement'],
                ['unclassified noise', 'random label']]

    with tests.testdir() as testdir:
        fname = op.join(testdir, 'labels.txt')
        with open(fname, 'wt') as f:
            f.write(contents)

        # Too many labels in the file
        lblobj = vollbls.VolumeLabels(3)
        with pytest.raises(fixlbls.InvalidLabelFileError):
            lblobj.load(fname)

        # Not enough labels in the file -
        # this is ok. Remaining labels
        # should be given 'Unknown'
        lblobj = vollbls.VolumeLabels(5)
        lblobj.load(fname)
        for i in range(4):
            assert lblobj.getLabels(i) == expected[i]
        assert lblobj.getLabels(4) == ['unknown']

        # Right number of labels
        lblobj = vollbls.VolumeLabels(4)
        lblobj.load(fname)
        for i in range(4):
            assert lblobj.getLabels(i) == expected[i] 


def test_load_fixfile_short():

    contents = """[2, 3, 5]""".strip()
    expected = [['signal'],
                ['unclassified noise'],
                ['unclassified noise'],
                ['signal'],
                ['unclassified noise']]

    with tests.testdir() as testdir:
        fname = op.join(testdir, 'labels.txt')
        with open(fname, 'wt') as f:
            f.write(contents)

        # Too many labels in the file
        lblobj = vollbls.VolumeLabels(3)
        with pytest.raises(fixlbls.InvalidLabelFileError):
            lblobj.load(fname)

        # Not enough labels in the file -
        # this is ok. Remaining labels
        # should be given 'Unknown'
        lblobj = vollbls.VolumeLabels(6)
        lblobj.load(fname)
        for i in range(4):
            assert lblobj.getLabels(i) == expected[i]
        assert lblobj.getLabels(5) == ['unknown']

        # Right number of labels
        lblobj = vollbls.VolumeLabels(5)
        lblobj.load(fname)
        for i in range(4):
            assert lblobj.getLabels(i) == expected[i] 


def test_load_aromafile():

    contents = """2, 3, 5""".strip()
    expected = [['unknown'],
                ['movement'],
                ['movement'],
                ['unknown'],
                ['movement']]

    with tests.testdir() as testdir:
        fname = op.join(testdir, 'labels.txt')
        with open(fname, 'wt') as f:
            f.write(contents)

        # Too many labels in the file
        lblobj = vollbls.VolumeLabels(3)
        with pytest.raises(fixlbls.InvalidLabelFileError):
            lblobj.load(fname)

        # Not enough labels in the file -
        # this is ok. Remaining labels
        # should be given 'Unknown'
        lblobj = vollbls.VolumeLabels(6)
        lblobj.load(fname)
        for i in range(4):
            assert lblobj.getLabels(i) == expected[i]
        assert lblobj.getLabels(5) == ['unknown']

        # Right number of labels
        lblobj = vollbls.VolumeLabels(5)
        lblobj.load(fname)
        for i in range(4):
            assert lblobj.getLabels(i) == expected[i] 


def test_save():

    expected = textwrap.dedent("""
    1, Signal, Default mode, False
    2, Unknown, False
    3, Unclassified noise, True
    4, Movement, True
    [3, 4]
    """).strip()

    lbls = vollbls.VolumeLabels(4)
    lbls.addLabel(0, 'Signal')
    lbls.addLabel(0, 'Default mode')
    lbls.addLabel(1, 'Unknown')
    lbls.addLabel(2, 'Unclassified noise')
    lbls.addLabel(3, 'Movement')

    with tests.testdir() as testdir:
        
        fname = op.join(testdir, 'labels.txt')

        # Test saving without dirname
        lbls.save(fname)
        exp = '.\n{}'.format(expected) 
        with open(fname, 'rt') as f:
            assert f.read().strip() == exp.strip()
 
        # And with dirname
        lbls.save(fname, 'path/to/analysis.ica')
        exp = 'path/to/analysis.ica\n{}'.format(expected)

        with open(fname, 'rt') as f:
            assert f.read().strip() == exp.strip()
