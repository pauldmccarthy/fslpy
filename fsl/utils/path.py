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
   getExt
   splitExt
   getFileGroup
   imcp
   immv
"""


import os.path as op
import            shutil


class PathError(Exception):
    """``Exception`` class raised by the functions defined in this module
    when something goes wrong.
    """
    pass


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


def addExt(prefix,
           allowedExts,
           mustExist=True,
           defaultExt=None,
           fileGroups=None):
    """Adds a file extension to the given file ``prefix``.

    If ``mustExist`` is False, and the file does not already have a 
    supported extension, the default extension is appended and the new
    file name returned. If the prefix already has a supported extension,
    it is returned unchanged.

    If ``mustExist`` is ``True`` (the default), the function checks to see 
    if any files exist that have the given prefix, and a supported file 
    extension.  A :exc:`PathError` is raised if:

       - No files exist with the given prefix and a supported extension.
    
       - ``fileGroups`` is ``None``, and more than one file exists with the
         given prefix, and a supported extension. 

    Otherwise the full file name is returned.

    :arg prefix:      The file name prefix to modify.

    :arg allowedExts: List of allowed file extensions.
    
    :arg mustExist:   Whether the file must exist or not.
    
    :arg defaultExt:  Default file extension to use.

    :arg fileGroups:  Recognised file groups - see :func:`getFileGroup`.
    """

    if fileGroups is None:
        fileGroups = {}

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
        allPaths = [prefix]
        
    # Otherwise, make a bunch of file names, one per
    # supported extension, and test to see if exactly
    # one of them exists.
    else:
        allPaths = [prefix + ext for ext in allowedExts]

    allPaths = [p for p in allPaths if op.isfile(p)]
    nexists  = len(allPaths)

    # Could not find any supported file
    # with the specified prefix
    if nexists == 0:
        raise PathError('Could not find a supported file '
                        'with prefix "{}"'.format(prefix))

    # Ambiguity! More than one supported
    # file with the specified prefix.
    elif nexists > 1:

        # Remove non-existent paths from the
        # extended list, get all their
        # suffixes, and see if they match
        # any file groups.
        suffixes     = [getExt(p, allowedExts) for p in allPaths]
        groupMatches = [sorted(suffixes) == sorted(g) for g in fileGroups]

        # Is there a match for a file suffix group?
        # If not, multiple files with the specified
        # prefix exist, and there is no way to
        # resolve the ambiguity.
        if sum(groupMatches) != 1:
            raise PathError('More than one file with '
                            'prefix "{}"'.format(prefix))

        # Otherwise, we return a path 
        # to the file which matches the 
        # first suffix in the group.
        groupIdx = groupMatches.index(True)
        allPaths = [prefix + fileGroups[groupIdx][0]]

    # Return the full file name of the
    # supported file that was found
    return allPaths[0]


def removeExt(filename, allowedExts=None):
    """Returns the base name of the given file name.  See :func:`splitExt`. """

    return splitExt(filename, allowedExts)[0]


def getExt(filename, allowedExts=None):
    """Returns the extension of the given file name.  See :func:`splitExt`. """

    return splitExt(filename, allowedExts)[1]


def splitExt(filename, allowedExts=None):
    """Returns the base name and the extension from the given file name.

    If ``allowedExts`` is ``None``, this function is equivalent to using::
    
        os.path.splitext(filename)

    If ``allowedExts`` is provided, but the file does not end with an allowed
    extension, a tuple containing ``(filename, '')`` is returned.

    :arg filename:    The file name to split.
    
    :arg allowedExts: Allowed/recognised file extensions.
    """

    # If allowedExts is not specified,
    # we just use op.splitext
    if allowedExts is None:
        return op.splitext(filename)

    # Otherwise, try and find a suffix match
    extMatches = [filename.endswith(ext) for ext in allowedExts]

    # No match, assume there is no extension
    if not any(extMatches):
        return filename, ''

    # Otherwise split the filename 
    # into its base and its extension
    extIdx = extMatches.index(True)
    extLen = len(allowedExts[extIdx])

    return filename[:-extLen], filename[-extLen:]


def getFileGroup(path, allowedExts=None, fileGroups=None, fullPaths=True):
    """If the given ``path`` is part of a ``fileGroup``, returns a list 
    containing the paths to all other files in the group (including the
    ``path`` itself).

    If the ``path`` does not appear to be part of a file group, a list
    containing only the ``path`` is returned.

    File groups can be used to specify a collection of file suffixes which
    should always exist alongside each other. This can be used to resolve
    ambiguity when multiple files exist with the same ``prefix`` and supported
    extensions (e.g. ``file.hdr`` and ``file.img``). The file groups are
    specified as a list of sequences, for example::
    
        [('.img',    '.hdr'),
         ('.img.gz', '.hdr.gz')]
    
    If you specify``fileGroups=[('.img', '.hdr')]`` and ``prefix='file'``, and
    both ``file.img`` and ``file.hdr`` exist, the :func:`addExt` function would
    return ``file.img`` (i.e. the file which matches the first extension in
    the group).

    Similarly, if you call the :func:`imcp` or :func:`immv` functions with the
    above parameters, both ``file.img`` and ``file.hdr`` will be moved.

    .. note:: The primary use-case of file groups is to resolve ambiguity with
              respect to NIFTI and ANALYSE75 image pairs. By specifying
              ``fileGroups=[('.img', '.hdr'), ('.img.gz', '.hdr.gz')]``, the
              :func:`addExt`, :func:`immv` and :func:`imcp` functions are able
              to figure out what you mean when you specify ``file``, and both
              ``file.hdr`` and ``file.img`` (or ``file.hdr.gz`` and
              ``file.img.gz``) exist.
    
    :arg path:        Path to the file. Must contain the file extension.
    
    :arg allowedExts: Allowed/recognised file extensions.
    
    :arg fileGroups:  Recognised file groups.
    
    :arg fullPaths:   If ``True`` (the default), full file paths (relative to
                      the ``path``) are returned. Otherwise, only the file
                      extensions in the group are returned.
    """

    if fileGroups is None:
        return [path]

    base, ext = splitExt(path, allowedExts)

    matchedGroups     = []
    matchedGroupFiles = []

    for group in fileGroups:

        if ext not in group:
            continue

        groupFiles = [base + s for s in group]

        if not all([op.exists(f) for f in groupFiles]):
            continue

        matchedGroups    .append(group)
        matchedGroupFiles.append(groupFiles)

    # If the given path is part of more 
    # than one existing file group, we 
    # can't resolve this ambiguity.
    if len(matchedGroupFiles) != 1:
        if fullPaths: return [path]
        else:         return [ext]
    else:
        if fullPaths: return matchedGroupFiles[0]
        else:         return matchedGroups[    0]


def imcp(src,
         dest,
         allowedExts=None,
         fileGroups=None,
         overwrite=False,
         move=False):
    """Copy the given ``src`` file to destination ``dest``.

    :arg src:         Path to copy. If ``allowedExts`` is provided,
                      the file extension can be omitted.
    
    :arg dest:        Destination path. Can be an incomplete file
                      specification (i.e. without the extension), or a 
                      directory. 
    
    :arg allowedExts: Allowed/recognised file extensions.
    
    :arg fileGroups:  Recognised file groups - see the :func:`getFileGroup`
                      documentation.

    :arg overwrite:   If ``True`` this function will overwrite files that 
                      already exist. Defaults to ``False``.
    
    :arg move:        If ``True``, the files are moved, instead of being
                      copied.
    """

    base, ext = splitExt(src, allowedExts)
    destIsDir = op.isdir(dest)

    # If dest has been specified 
    # as a file name, we don't 
    # care about its extension.
    if not destIsDir:
        dest = removeExt(dest, allowedExts)

    # src was specified without an
    # extension, or the specitifed
    # src does not have an allowed
    # extension. 
    if ext == '':

        # Try to resolve the specified src
        # path - if src does not exist, or
        # does not have an allowed extension,
        # addExt will raise an error
        src = addExt(src,
                     allowedExts,
                     mustExist=True,
                     fileGroups=fileGroups)

        # We've resolved src to a 
        # full filename - split it 
        # again to get its extension
        base, ext = splitExt(src, allowedExts)

    # If the source is part of a file group,
    # e.g. src.img/src.hdr, we want to copy
    # the whole set of files. So here we
    # build a list of source files that need
    # to be copied/moved. The getFileGroup
    # function returns all other files that
    # are associated with this file (i.e.
    # part of the same group).
    #
    # We store the sources as separate
    # (base, ext) tuples, so we don't
    # have to re-split when creating
    # destination paths.
    copySrcs = getFileGroup(src, allowedExts, fileGroups, fullPaths=False)
    copySrcs = [(base, e) for e in copySrcs]

    # Note that these additional files 
    # do not have to exist, e.g.
    # imcp('blah.img', ...)  will still
    # work if there is no blah.hdr
    copySrcs = [(b, e) for (b, e) in copySrcs if op.exists(b + e)]

    # Build a list of destinations for each
    # copy source - we build this list in
    # advance, so we can fail if any of the
    # destinations already exist.
    copyDests = []
    for i, (base, ext) in enumerate(copySrcs):

        # We'll also take this opportunity 
        # to re-combine the source paths
        copySrcs[i] = base + ext

        if destIsDir: copyDests.append(dest)
        else:         copyDests.append(dest + ext)

    # Fail if any of the destination 
    # paths already exist
    if not overwrite:
        if not destIsDir and any([op.exists(d) for d in copyDests]):
            raise PathError('imcp error - a destination path already '
                            'exists ({})'.format(', '.join(copyDests)))
 
    # Do the copy/move
    for src, dest in zip(copySrcs, copyDests):

        if move: shutil.move(src, dest)
        else:    shutil.copy(src, dest)


def immv(src, dest, allowedExts=None, fileGroups=None, overwrite=False):
    """Move the specified ``src`` to the specified ``dest``. See :func:`imcp`.
    """
    imcp(src, dest, allowedExts, fileGroups, overwrite, move=True)
