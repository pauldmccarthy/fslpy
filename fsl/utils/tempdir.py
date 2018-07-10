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
def tempdir(root=None, changeto=True, override=None):
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
                   manager when a temporary directory already exists.
    """

    if override is None:
        testdir = tempfile.mkdtemp(dir=root)
        prevdir = os.getcwd()
    else:
        testdir = override

    try:
        if changeto:
            os.chdir(testdir)
        yield testdir

    finally:
        if override is None:
            if changeto:
                os.chdir(prevdir)
            shutil.rmtree(testdir)
