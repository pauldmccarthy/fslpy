#!/usr/bin/env python
#
# tempdir.py - Utilities for working with temporary directories.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains utilities for working with temporary files and
directories. It currently only contains one function:

.. autosummary::
   :nosignatures:

   tempdir
"""


import os
import shutil
import tempfile
import contextlib


@contextlib.contextmanager
def tempdir(root=None, changeto=True):
    """Returns a context manager which creates and returns a temporary
    directory, and then deletes it on exit.

    :arg root:     If provided, specifies a directroy in which to create the
                   new temporary directory. Otherwise the system default is
                   used (see the ``tempfile.mkdtemp`` documentation).

    :arg changeto: If ``True`` (the default), current working directory is set
                   to the new temporary directory before yielding, and restored
                   afterwards.
    """

    testdir = tempfile.mkdtemp(dir=root)
    prevdir = os.getcwd()
    try:

        if changeto:
            os.chdir(testdir)
        yield testdir

    finally:
        if changeto:
            os.chdir(prevdir)
        shutil.rmtree(testdir)
