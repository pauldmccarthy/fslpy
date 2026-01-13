#!/usr/bin/env python
#
# tempdir.py - Utilities for working with temporary directories.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains utilities for working with temporary files and
directories. It currently contains the following functions:

.. autosummary::
   :nosignatures:

   tempdir
   indir
   mkstemp
"""


import os
import shutil
import tempfile
import contextlib


@contextlib.contextmanager
def tempdir(root=None, changeto=True, override=None, prefix=None, delete=True):
    """Returns a context manager which creates and returns a temporary
    directory, and then deletes it on exit.

    :arg root:     If provided, specifies a directroy in which to create the
                   new temporary directory. Otherwise the system default is
                   used (see the ``tempfile.mkdtemp`` documentation).

    :arg changeto: If ``True`` (the default), current working directory is set
                   to the new temporary directory before yielding, and restored
                   afterwards.

    :arg override: Don't create a temporary directory, but use this one
                   instead. This allows ``tempdir`` to be used as a context
                   manager when a temporary directory already exists. Implies
                   ``delete=False``.

    :arg prefix:   Create the temporary directory with a name starting with
                   this prefix.

    :arg delete:   If ``True`` (the default), the directory is deleted on exit.
                   Otherwise the caller is responsible for deleting the
                   directory.
    """

    if root is not None:
        root = os.path.abspath(root)

    if override is None:
        testdir = tempfile.mkdtemp(dir=root, prefix=prefix)
    else:
        testdir = override
        delete  = False

    prevdir = os.getcwd()

    try:
        if changeto:
            os.chdir(testdir)
        yield testdir

    finally:
        if delete:
            shutil.rmtree(testdir)
        if changeto:
            os.chdir(prevdir)


@contextlib.contextmanager
def indir(path):
    """Context manager which changes into the specified directory, then changes
    back afterwards.
    """

    prevdir = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prevdir)


def mkstemp(*args, **kwargs):
    """Wrapper around ``tempfile.mkstemp``. Does the same as that
    function, but closes the file, and just returns the file name.
    """
    hd, fname = tempfile.mkstemp(*args, **kwargs)
    os.close(hd)
    return fname
