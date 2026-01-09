#!/usr/bin/env python
#
# fslio.py - Wrappers for the FSL im* scripts.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides wrapper functions for the FSL ``im*`` scripts.

These scripts are actually implemented within fslpy, so the wrapper functions
invoke the relevant code directly, rather than invoking a separate process.
"""

from fsl.scripts import (fslchfiletype as fslchfiletype_script,
                         imcp          as imcp_script,
                         imglob        as imglob_script,
                         imln          as imln_script,
                         immv          as immv_script,
                         imrm          as imrm_script,
                         imtest        as imtest_script,
                         remove_ext    as remove_ext_script,
                         tmpnam        as tmpnam_script)


def imcp(*paths):
    """Wrapper for the ``imcp`` script. """
    imcp_script.imcp(*paths)


def imglob(*images, extension=False, extensions=False):
    """Wrapper for the ``imglob`` script. Returns the result in a list. """
    if extension and extensions:
        raise ValueError('Only one of extension/extensions may be specified')

    if   extension:  output = 'primary'
    elif extensions: output = 'all'
    else:            output = 'prefix'

    return imglob_script.imglob(images, output)


def imln(target, linkbase):
    """Wrapper for the ``imln`` script. """
    imln_script.imln(target, linkbase)


def immv(*paths):
    """Wrapper for the ``immv`` script. """
    immv_script.immv(*paths)


def imrm(*paths):
    """Wrapper for the ``imrm`` script. """
    imrm_script.imrm(*paths)


def imtest(path):
    """Wrapper for the ``imcp`` script. Returns ``True`` if the given path
    exists, ``False`` otherwise.
    """
    return imtest_script.imtest(path)


def remove_ext(*paths):
    """Wrapper for the ``remove_ext`` script.

    Returns the specified paths with extensions removed. If one path is
    provided, a string is returned. Otherwise (multiple paths provided), a list
    is returned.
    """
    paths = remove_ext_script.remove_ext(*paths)

    if len(paths) == 1: return paths[0]
    else:               return paths


def tmpnam(path=None):
    """Wrapper for the ``tmpnam`` script. """
    return tmpnam_script.tmpnam(path)


def fslchfiletype(fmt, oldfile, newfile=None):
    """Wrapper for the ``fslchfiletype`` script. """
    fslchfiletype_script.fslchfiletype(fmt, oldfile, newfile)
