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

from fsl.scripts import (imcp   as imcp_script,
                         imglob as imglob_script,
                         imln   as imln_script,
                         immv   as immv_script,
                         imrm   as imrm_script,
                         imtest as imtest_script)


def imcp(*args):
    """Wrapper for the ``imcp`` script. """
    imcp_script.main(args)


def imglob(*images, extension=False, extensions=False):
    """Wrapper for the ``imglob`` script. Returns the result in a list. """
    if extension and extensions:
        raise ValueError('Only one of extension/extensions may be specified')

    if   extension:  output = 'primary'
    elif extensions: output = 'all'
    else:            output = 'prefix'

    return imglob_script.imglob(images, output)


def imln(*args):
    """Wrapper for the ``imln`` script. """
    imln_script.main(args)


def immv(*args):
    """Wrapper for the ``immv`` script. """
    immv_script.main(args)


def imrm(*args):
    """Wrapper for the ``imrm`` script. """
    imrm_script.main(args)


def imtest(path):
    """Wrapper for the ``imcp`` script. Returns ``True`` if the given path
    exists, ``False`` otherwise.
    """
    return imtest_script.imtest(path)
