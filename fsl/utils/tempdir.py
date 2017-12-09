#!/usr/bin/env python
#
# tempdir.py - Utilities for working with temporary directories.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains utilities for working with temporary files and
directories. It currently only contains one function:

.. autosummary::
   :nosignature:

   tempdir
"""


import os
import shutil
import tempfile
import contextlib


@contextlib.contextmanager
def tempdir():
    """Returns a context manager which creates and returns a temporary
    directory, and then deletes it on exit.
    """

    testdir = tempfile.mkdtemp()
    prevdir = os.getcwd()
    try:

        os.chdir(testdir)
        yield testdir

    finally:
        os.chdir(prevdir)
        shutil.rmtree(testdir)
