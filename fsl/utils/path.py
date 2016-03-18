#!/usr/bin/env python
#
# path.py - Utility functions for working with file/directory paths.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains a few utility functions for working with file system
paths.


.. autosummary::
   :nosignatures:

   deepest
   shallowest 
"""


import os.path as op


def deepest(path, suffixes):
    """Finds the deepest directory which ends with one of the given
    sequence of suffixes, or returns ``None`` if no directories end
    with any of the suffixes.
    """

    path = path.strip()

    if path == op.sep or path == '':
        return None

    path = path.rstrip(op.sep)

    if any([path.endswith(s) for s in suffixes]):
        return path

    return deepest(op.dirname(path), suffixes)


def shallowest(path, suffixes):
    """Finds the shallowest directory which ends with one of the given
    sequence of suffixes, or returns ``None`` if no directories end
    with any of the suffixes.
    """ 
    
    path = path.strip()

    # We've reached the root of the file system
    if path == op.sep or path == '':
        return None

    path   = path.rstrip(op.sep)
    parent = shallowest(op.dirname(path), suffixes)

    if parent is not None:
        return parent

    if any([path.endswith(s) for s in suffixes]):
        return path

    return None 
