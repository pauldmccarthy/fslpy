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
   addExt
   removeExt
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


def addExt(prefix, allowedExts, mustExist=True, defaultExt=None):
    """Adds a file extension to the given file ``prefix``.

    If ``mustExist`` is False, and the file does not already have a 
    supported extension, the default extension is appended and the new
    file name returned. If the prefix already has a supported extension,
    it is returned unchanged.

    If ``mustExist`` is ``True`` (the default), the function checks to see 
    if any files exist that have the given prefix, and a supported file 
    extension.  A :exc:`ValueError` is raised if:

       - No files exist with the given prefix and a supported extension.
       - More than one file exists with the given prefix, and a supported
         extension.

    Otherwise the full file name is returned.

    :arg prefix:      The file name refix to modify.
    :arg mustExist:   Whether the file must exist or not.
    :arg allowedExts: List of allowed file extensions.
    :arg defaultExt:  Default file extension to use.
    """

    if not mustExist:

        # the provided file name already
        # ends with a supported extension
        if any([prefix.endswith(ext) for ext in allowedExts]):
            return prefix

        if defaultExt is not None: return prefix + defaultExt
        else:                      return None

    # If the provided prefix already ends with a
    # supported extension , check to see that it exists
    if any([prefix.endswith(ext) for ext in allowedExts]):
        extended = [prefix]
        
    # Otherwise, make a bunch of file names, one per
    # supported extension, and test to see if exactly
    # one of them exists.
    else:
        extended = [prefix + ext for ext in allowedExts]

    exists = [op.isfile(e) for e in extended]

    # Could not find any supported file
    # with the specified prefix
    if not any(exists):
        raise ValueError(
            'Could not find a supported file with prefix {}'.format(prefix))

    # Ambiguity! More than one supported
    # file with the specified prefix
    if sum(exists) > 1:
        raise ValueError('More than one file with prefix {}'.format(prefix))

    # Return the full file name of the
    # supported file that was found
    extIdx = exists.index(True)
    return extended[extIdx]


def removeExt(filename, allowedExts):
    """Removes the extension from the given file name. Returns the filename
    unmodified if it does not have a supported extension.

    :arg filename:    The file name to strip.
    
    :arg allowedExts: A list of strings containing the allowed file
                      extensions.    
    """

    # figure out the extension of the given file
    extMatches = [filename.endswith(ext) for ext in allowedExts]

    # the file does not have a supported extension
    if not any(extMatches):
        return filename

    # figure out the length of the matched extension
    extIdx = extMatches.index(True)
    extLen = len(allowedExts[extIdx])

    # and trim it from the file name
    return filename[:-extLen]
