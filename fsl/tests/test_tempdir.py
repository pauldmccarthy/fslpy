#!/usr/bin/env python
#
# test_tempdir.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import glob
import os
import os.path as op

import fsl.utils.tempdir as tempdir


def test_tempdir():

    # use ctx manager with or without arg
    with tempdir.tempdir():
        d = os.getcwd()

    # dir is removed after ctx manager exit
    assert not op.exists(d)

    with tempdir.tempdir() as td:

        d = td

        assert op.exists(d)

        # pwd is dir when in ctx manager
        assert op.realpath(os.getcwd()) == op.realpath(td)

    assert not op.exists(d)


def test_tempdir_root():

    # this first tempdir is then used
    # as the root for another temp dir
    with tempdir.tempdir() as root:
        with tempdir.tempdir(root=root) as td:
            assert op.dirname(td) == root


def test_tempdir_changeto():

    cwd = op.realpath(os.getcwd())

    # make sure cwd is not changed
    with tempdir.tempdir(changeto=False):
        assert op.realpath(os.getcwd()) == cwd

    assert op.realpath(os.getcwd()) == cwd


def test_tempdir_prefix():
    with tempdir.tempdir(prefix='mytempdirtest') as tdir:
        assert op.basename(tdir).startswith('mytempdirtest')

    with tempdir.tempdir() as parent:
        with tempdir.tempdir(prefix='mytempdirtest', root='.') as tdir:
            assert list(glob.glob(op.join(parent, 'mytempdirtest*'))) == [tdir]


def test_tempdir_override():
    with tempdir.tempdir() as parent:
        override = op.abspath((op.join('override', 'directory')))

        os.makedirs(override)

        # tempdir should not create/change to
        # a new temp directory, but should
        # stay in the override directory
        with tempdir.tempdir(override=override):
            assert op.realpath(os.getcwd()) == op.realpath(override)
        # override should not be deleted
        assert op.exists(override)
        # and we should be moved back into the original cwd
        assert op.realpath(os.getcwd()) == op.realpath(parent)


def test_tempdir_delete():
    with tempdir.tempdir() as parent:
        # default is to delete on exit
        with tempdir.tempdir(root='.') as td:
            pass
        assert not op.exists(td)

        # delete=False -> tempdir should not be deleted
        with tempdir.tempdir(root='.', delete=False) as td:
            pass
        assert op.exists(td)

        # overrire not none -> should not be deleted
        os.makedirs('override')
        with tempdir.tempdir(root='.', override='override') as td:
            pass
        assert op.exists(td)
        with tempdir.tempdir(root='.', override='override', delete=True) as td:
            pass
        assert op.exists(td)
