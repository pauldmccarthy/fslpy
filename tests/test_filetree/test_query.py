#!/usr/bin/env python
#
# test_query.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os
import glob
import shutil
import os.path as op
import contextlib
import textwrap as tw
import itertools as it

from .. import testdir

import fsl.utils.filetree       as filetree
import fsl.utils.filetree.query as ftquery


_test_tree = """
subj-{participant}
  [ses-{session}]
    T1w.nii.gz (T1w)
    T2w.nii.gz (T2w)
    {hemi}.{surf}.gii (surface)
""".strip()

_subjs = ['01', '02', '03']
_sess  = ['1', '2']
_hemis = ['L', 'R']
_surfs = ['midthickness', 'pial', 'white']


@contextlib.contextmanager
def _test_data():

    files = []

    for subj, ses in it.product(_subjs, _sess):
        sesdir = op.join('subj-{}'.format(subj), 'ses-{}'.format(ses))
        files.append(op.join(sesdir, 'T1w.nii.gz'))
        files.append(op.join(sesdir, 'T2w.nii.gz'))

        for hemi, surf in it.product(_hemis, _surfs):
            files.append(op.join(sesdir, '{}.{}.gii'.format(hemi, surf)))

    with testdir(files):
        with open('_test_tree.tree', 'wt') as f:
            f.write(_test_tree)
        yield


def _expected_matches(short_name, **kwargs):

    matches = []
    subjs   = kwargs.get('participant', _subjs)
    sess    = kwargs.get('session',     _sess)
    surfs   = kwargs.get('surf',        _surfs)
    hemis   = kwargs.get('hemi',        _hemis)

    for subj, ses in it.product(subjs, sess):

        sesdir = op.join('subj-{}'.format(subj), 'ses-{}'.format(ses))

        if short_name in ('T1w', 'T2w'):
            f = op.join(sesdir, '{}.nii.gz'.format(short_name))
            matches.append(ftquery.Match(f,
                                         short_name,
                                         {'participant' : subj,
                                          'session'     : ses}))

        elif short_name == 'surface':
            for hemi, surf in it.product(hemis, surfs):
                f = op.join(sesdir, '{}.{}.gii'.format(hemi, surf))
                matches.append(ftquery.Match(f,
                                             short_name,
                                             {'participant' : subj,
                                              'session'     : ses,
                                              'hemi'        : hemi,
                                              'surf'        : surf}))

    return matches


def _run_and_check_query(query, short_name, asarray=False, **vars):

    gotmatches = query.query(      short_name, asarray=asarray, **vars)
    expmatches = _expected_matches(short_name, **{k : [v]
                                                  for k, v
                                                  in vars.items()})

    if not asarray:
        assert len(gotmatches) == len(expmatches)
        for got, exp in zip(sorted(gotmatches), sorted(expmatches)):
            assert got == exp
    else:
        snvars = query.variables(short_name)

        assert len(snvars) == len(gotmatches.shape)

        for i, var in enumerate(sorted(snvars.keys())):
            if var not in vars or vars[var] == '*':
                assert len(snvars[var]) == gotmatches.shape[i]
            else:
                assert gotmatches.shape[i] == 1

        for expmatch in expmatches:
            slc = []
            for var in query.axes(short_name):
                if var not in vars or vars[var] == '*':
                    vidx = snvars[var].index(expmatch.variables[var])
                    slc.append(vidx)
                else:
                    slc.append(0)


def test_query_properties():
    with _test_data():

        tree  = filetree.FileTree.read('_test_tree.tree', '.')
        query = filetree.FileTreeQuery(tree)

        assert sorted(query.axes('T1w'))     == ['participant', 'session']
        assert sorted(query.axes('T2w'))     == ['participant', 'session']
        assert sorted(query.axes('surface')) == ['hemi',
                                                 'participant',
                                                 'session',
                                                 'surf']
        assert sorted(query.short_names)     == ['T1w', 'T2w', 'surface']

        assert query.variables('T1w')     == {'participant' : ['01', '02', '03'],
                                              'session'     : ['1', '2']}
        assert query.variables('T2w')     == {'participant' : ['01', '02', '03'],
                                              'session'     : ['1', '2']}
        assert query.variables('surface') == {'participant' : ['01', '02', '03'],
                                              'session'     : ['1', '2'],
                                              'surf'        : ['midthickness',
                                                               'pial',
                                                               'white'],
                                              'hemi'        : ['L', 'R']}
        assert query.variables()          == {'participant' : ['01', '02', '03'],
                                              'session'     : ['1', '2'],
                                              'surf'        : ['midthickness',
                                                               'pial',
                                                               'white'],
                                              'hemi'        : ['L', 'R']}


def test_query():
    with _test_data():
        tree  = filetree.FileTree.read('_test_tree.tree', '.')
        query = filetree.FileTreeQuery(tree)

    _run_and_check_query(query, 'T1w')
    _run_and_check_query(query, 'T1w', participant='01')
    _run_and_check_query(query, 'T1w', session='2')
    _run_and_check_query(query, 'T1w', participant='02', session='1')
    _run_and_check_query(query, 'T2w')
    _run_and_check_query(query, 'T2w', participant='01')
    _run_and_check_query(query, 'T2w', session='2')
    _run_and_check_query(query, 'T2w', participant='02', session='1')
    _run_and_check_query(query, 'surface')
    _run_and_check_query(query, 'surface', hemi='L')
    _run_and_check_query(query, 'surface', surf='midthickness')
    _run_and_check_query(query, 'surface', hemi='R', surf='pial')
    _run_and_check_query(query, 'surface', participant='03', surf='pial')
    _run_and_check_query(query, 'surface', participant='03', sssion='2')


def test_query_optional_var_folder():
    with _test_data():

        # make subj-01 have no session sub-directories
        for f in glob.glob(op.join('subj-01', 'ses-1', '*')):
            shutil.move(f, 'subj-01')
        shutil.rmtree(op.join('subj-01', 'ses-1'))
        shutil.rmtree(op.join('subj-01', 'ses-2'))

        tree  = filetree.FileTree.read('_test_tree.tree', '.')
        query = filetree.FileTreeQuery(tree)

        assert query.variables()['session'] == [None, '1', '2']

        m = query.query('T1w', participant='01')
        assert len(m) == 1
        assert m[0].filename == op.join('subj-01', 'T1w.nii.gz')


def test_query_optional_var_filename():

    treefile = tw.dedent("""
    sub-{subject}
        img[-{modality}].nii.gz (image)
    """).strip()

    files = [
        op.join('sub-01', 'img.nii.gz'),
        op.join('sub-02', 'img-t1.nii.gz'),
        op.join('sub-02', 'img-t2.nii.gz'),
        op.join('sub-03', 'img-t1.nii.gz'),
        op.join('sub-04', 'img.nii.gz')]

    with testdir(files):
        with open('_test_tree.tree', 'wt') as f:
            f.write(treefile)

        tree  = filetree.FileTree.read('_test_tree.tree', '.')
        query = filetree.FileTreeQuery(tree)

        qvars = query.variables()

        assert sorted(qvars.keys()) == ['modality', 'subject']
        assert qvars['subject']  == ['01', '02', '03', '04']
        assert qvars['modality'] == [None, 't1', 't2']

        got = query.query('image', modality=None)
        assert [m.filename for m in sorted(got)] == [
            op.join('sub-01', 'img.nii.gz'),
            op.join('sub-04', 'img.nii.gz')]

        got = query.query('image', modality='t1')
        assert [m.filename for m in sorted(got)] == [
            op.join('sub-02', 'img-t1.nii.gz'),
            op.join('sub-03', 'img-t1.nii.gz')]

        got = query.query('image', modality='t2')
        assert len(got) == 1
        assert got[0].filename == op.join('sub-02', 'img-t2.nii.gz')


def test_query_missing_files():
    with _test_data():

        os.remove(op.join('subj-01', 'ses-1', 'T1w.nii.gz'))
        os.remove(op.join('subj-02', 'ses-2', 'T2w.nii.gz'))
        os.remove(op.join('subj-03', 'ses-1', 'L.white.gii'))
        os.remove(op.join('subj-03', 'ses-1', 'L.midthickness.gii'))
        os.remove(op.join('subj-03', 'ses-1', 'L.pial.gii'))

        tree  = filetree.FileTree.read('_test_tree.tree', '.')
        query = filetree.FileTreeQuery(tree)

        got = query.query('T1w', session='1')
        assert [m.filename for m in sorted(got)] == [
            op.join('subj-02', 'ses-1', 'T1w.nii.gz'),
            op.join('subj-03', 'ses-1', 'T1w.nii.gz')]

        got = query.query('T2w', session='2')
        assert [m.filename for m in sorted(got)] == [
            op.join('subj-01', 'ses-2', 'T2w.nii.gz'),
            op.join('subj-03', 'ses-2', 'T2w.nii.gz')]

        got = query.query('surface', session='1', hemi='L')
        assert [m.filename for m in sorted(got)] == [
            op.join('subj-01', 'ses-1', 'L.midthickness.gii'),
            op.join('subj-01', 'ses-1', 'L.pial.gii'),
            op.join('subj-01', 'ses-1', 'L.white.gii'),
            op.join('subj-02', 'ses-1', 'L.midthickness.gii'),
            op.join('subj-02', 'ses-1', 'L.pial.gii'),
            op.join('subj-02', 'ses-1', 'L.white.gii')]


def test_query_asarray():
    with _test_data():
        tree  = filetree.FileTree.read('_test_tree.tree', '.')
        query = filetree.FileTreeQuery(tree)

        _run_and_check_query(query, 'T1w', asarray=True)
        _run_and_check_query(query, 'T1w', asarray=True, participant='01')
        _run_and_check_query(query, 'T1w', asarray=True, session='2')
        _run_and_check_query(query, 'T1w', asarray=True, participant='02', session='1')
        _run_and_check_query(query, 'T2w', asarray=True)
        _run_and_check_query(query, 'T2w', asarray=True, participant='01')
        _run_and_check_query(query, 'T2w', asarray=True, session='2')
        _run_and_check_query(query, 'T2w', asarray=True, participant='02', session='1')
        _run_and_check_query(query, 'surface', asarray=True)
        _run_and_check_query(query, 'surface', asarray=True, hemi='L')
        _run_and_check_query(query, 'surface', asarray=True, surf='midthickness')
        _run_and_check_query(query, 'surface', asarray=True, hemi='R', surf='pial')
        _run_and_check_query(query, 'surface', asarray=True, participant='03', surf='pial')
        _run_and_check_query(query, 'surface', asarray=True, participant='03', sssion='2')


def test_query_subtree():
    tree1 = tw.dedent("""
    subj-{participant}
        T1w.nii.gz (T1w)
        surf
            ->surface (surfdir)
    """)
    tree2 = tw.dedent("""
    {hemi}.{surf}.gii (surface)
    """)

    files = [
        op.join('subj-01', 'T1w.nii.gz'),
        op.join('subj-01', 'surf', 'L.pial.gii'),
        op.join('subj-01', 'surf', 'R.pial.gii'),
        op.join('subj-01', 'surf', 'L.white.gii'),
        op.join('subj-01', 'surf', 'R.white.gii'),
        op.join('subj-02', 'T1w.nii.gz'),
        op.join('subj-02', 'surf', 'L.pial.gii'),
        op.join('subj-02', 'surf', 'R.pial.gii'),
        op.join('subj-02', 'surf', 'L.white.gii'),
        op.join('subj-02', 'surf', 'R.white.gii'),
        op.join('subj-03', 'T1w.nii.gz'),
        op.join('subj-03', 'surf', 'L.pial.gii'),
        op.join('subj-03', 'surf', 'R.pial.gii'),
        op.join('subj-03', 'surf', 'L.white.gii'),
        op.join('subj-03', 'surf', 'R.white.gii')]

    with testdir(files):
        with open('tree1.tree',   'wt') as f: f.write(tree1)
        with open('surface.tree', 'wt') as f: f.write(tree2)

        tree = filetree.FileTree.read('tree1.tree', '.')
        query = filetree.FileTreeQuery(tree)

        assert sorted(query.short_names) == ['T1w', 'surface']

        qvars = query.variables()
        assert sorted(qvars.keys()) == ['hemi', 'participant', 'surf']
        assert qvars['hemi']        == ['L', 'R']
        assert qvars['participant'] == ['01', '02', '03']
        assert qvars['surf']        == ['pial', 'white']

        qvars = query.variables('T1w')
        assert sorted(qvars.keys()) == ['participant']
        assert qvars['participant'] == ['01', '02', '03']

        qvars = query.variables('surface')
        assert sorted(qvars.keys()) == ['hemi', 'participant', 'surf']
        assert qvars['hemi']        == ['L', 'R']
        assert qvars['participant'] == ['01', '02', '03']
        assert qvars['surf']        == ['pial', 'white']

        got = query.query('T1w')
        assert [m.filename for m in sorted(got)] == [
            op.join('subj-01', 'T1w.nii.gz'),
            op.join('subj-02', 'T1w.nii.gz'),
            op.join('subj-03', 'T1w.nii.gz')]

        got = query.query('T1w', participant='01')
        assert [m.filename for m in sorted(got)] == [
            op.join('subj-01', 'T1w.nii.gz')]

        got = query.query('surface')
        assert [m.filename for m in sorted(got)] == [
            op.join('subj-01', 'surf', 'L.pial.gii'),
            op.join('subj-01', 'surf', 'L.white.gii'),
            op.join('subj-01', 'surf', 'R.pial.gii'),
            op.join('subj-01', 'surf', 'R.white.gii'),
            op.join('subj-02', 'surf', 'L.pial.gii'),
            op.join('subj-02', 'surf', 'L.white.gii'),
            op.join('subj-02', 'surf', 'R.pial.gii'),
            op.join('subj-02', 'surf', 'R.white.gii'),
            op.join('subj-03', 'surf', 'L.pial.gii'),
            op.join('subj-03', 'surf', 'L.white.gii'),
            op.join('subj-03', 'surf', 'R.pial.gii'),
            op.join('subj-03', 'surf', 'R.white.gii')]

        got = query.query('surface', hemi='L')
        assert [m.filename for m in sorted(got)] == [
            op.join('subj-01', 'surf', 'L.pial.gii'),
            op.join('subj-01', 'surf', 'L.white.gii'),
            op.join('subj-02', 'surf', 'L.pial.gii'),
            op.join('subj-02', 'surf', 'L.white.gii'),
            op.join('subj-03', 'surf', 'L.pial.gii'),
            op.join('subj-03', 'surf', 'L.white.gii')]

        got = query.query('surface', surf='white')
        assert [m.filename for m in sorted(got)] == [
            op.join('subj-01', 'surf', 'L.white.gii'),
            op.join('subj-01', 'surf', 'R.white.gii'),
            op.join('subj-02', 'surf', 'L.white.gii'),
            op.join('subj-02', 'surf', 'R.white.gii'),
            op.join('subj-03', 'surf', 'L.white.gii'),
            op.join('subj-03', 'surf', 'R.white.gii')]


def test_scan():

    with _test_data():
        tree    = filetree.FileTree.read('_test_tree.tree', '.')
        gotmatches = ftquery.scan(tree)

    expmatches = []

    for subj, ses in it.product(_subjs, _sess):

        sesdir = op.join('subj-{}'.format(subj), 'ses-{}'.format(ses))
        t1wf   = op.join(sesdir, 'T1w.nii.gz')
        t2wf   = op.join(sesdir, 'T2w.nii.gz')

        expmatches.append(ftquery.Match(t1wf, 'T1w', {'participant' : subj,
                                                      'session'     : ses}))
        expmatches.append(ftquery.Match(t2wf, 'T2w', {'participant' : subj,
                                                      'session'     : ses}))

        for hemi, surf in it.product(_hemis, _surfs):
            surff = op.join(sesdir, '{}.{}.gii'.format(hemi, surf))

            expmatches.append(ftquery.Match(surff,
                                            'surface',
                                            {'participant' : subj,
                                             'session'     : ses,
                                             'surf'        : surf,
                                             'hemi'        : hemi}))


    assert len(gotmatches) == len(expmatches)

    for got, exp in zip(sorted(gotmatches), sorted(expmatches)):
        assert got.filename   == exp.filename
        assert got.short_name == exp.short_name
        assert got.variables  == exp.variables


def test_allVariables():
    with _test_data():
        tree          = filetree.FileTree.read('_test_tree.tree', '.')
        matches       = ftquery.scan(tree)
        qvars, snames = ftquery.allVariables(tree, matches)

        expqvars = {
            'participant' : _subjs,
            'session'     : _sess,
            'surf'        : _surfs,
            'hemi'        : _hemis}
        expsnames = {
            'T1w'     : ['participant', 'session'],
            'T2w'     : ['participant', 'session'],
            'surface' : ['hemi', 'participant', 'session', 'surf']}

        assert qvars  == expqvars
        assert snames == expsnames
