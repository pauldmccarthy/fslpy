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
   allFiles
   hasExt
   addExt
   removeExt
   getExt
   splitExt
   getFileGroup
   removeDuplicates
   uniquePrefix
   commonBase
"""


import os.path as op
import            os
import            glob
import            operator


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
    if path == op.sep or path == '' or op.splitdrive(path)[1] == '':
        return None

    path   = path.rstrip(op.sep)
    parent = shallowest(op.dirname(path), suffixes)

    if parent is not None:
        return parent

    if any([path.endswith(s) for s in suffixes]):
        return path

    return None


def allFiles(root):
    """Return a list containing all files which exist underneath the specified
    ``root`` directory.
    """

    files = []

    for dirpath, _, filenames in os.walk(root):
        filenames = [op.join(dirpath, f) for f in filenames]
        files.extend(filenames)

    return files


def hasExt(path, allowedExts):
    """Convenience function which returns ``True`` if the given ``path``
    ends with any of the given ``allowedExts``, ``False`` otherwise.
    """
    return any([path.endswith(e) for e in allowedExts])


def addExt(prefix,
           allowedExts=None,
           mustExist=True,
           defaultExt=None,
           fileGroups=None,
           unambiguous=True):
    """Adds a file extension to the given file ``prefix``.

    If ``mustExist`` is False, and the file does not already have a
    supported extension, the default extension is appended and the new
    file name returned. If the prefix already has a supported extension,
    it is returned unchanged.

    If ``mustExist`` is ``True`` (the default), the function checks to see
    if any files exist that have the given prefix, and a supported file
    extension.  A :exc:`PathError` is raised if:

       - No files exist with the given prefix and a supported extension.

       - ``fileGroups is None`` and ``unambiguous is True``, and more than
         one file exists with the given prefix, and a supported extension.

    Otherwise the full file name is returned.

    :arg prefix:      The file name prefix to modify.

    :arg allowedExts: List of allowed file extensions.

    :arg mustExist:   Whether the file must exist or not.

    :arg defaultExt:  Default file extension to use.

    :arg fileGroups:  Recognised file groups - see :func:`getFileGroup`.

    :arg unambiguous: If ``True`` (the default), and more than one file
                      exists with the specified ``prefix``, a
                      :exc:`PathError` is raised. Otherwise, a list
                      containing *all* matching files is returned.
    """

    if allowedExts is None: allowedExts = []
    if fileGroups  is None: fileGroups  = {}

    if defaultExt is not None and defaultExt not in allowedExts:
        allowedExts.append(defaultExt)

    if not mustExist:

        # the provided file name already
        # ends with a supported extension
        if hasExt(prefix, allowedExts):
            return prefix

        if defaultExt is not None: return prefix + defaultExt
        else:                      return prefix

    # If no allowed extensions were
    # provided, or the provided prefix
    # already ends with a supported
    # extension, check to see that it
    # exists.
    if len(allowedExts) == 0 or hasExt(prefix, allowedExts):
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

    # If ambiguity is ok, return
    # all matching paths
    elif not unambiguous:
        return allPaths

    # Ambiguity is not ok! More than
    # one supported file with the
    # specified prefix.
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


def getFileGroup(path,
                 allowedExts=None,
                 fileGroups=None,
                 fullPaths=True,
                 unambiguous=False):
    """If the given ``path`` is part of a ``fileGroup``, returns a list
    containing the paths to all other files in the group (including the
    ``path`` itself).

    If the ``path`` does not appear to be part of a file group, or appears to
    be part of an incomplete file group, a list containing only the ``path``
    is returned.

    If the ``path`` does not exist, or appears to be part of more than one
    file group, a :exc:`PathError` is raised.

    File groups can be used to specify a collection of file suffixes which
    should always exist alongside each other. This can be used to resolve
    ambiguity when multiple files exist with the same ``prefix`` and supported
    extensions (e.g. ``file.hdr`` and ``file.img``). The file groups are
    specified as a list of sequences, for example::

        [('.img',    '.hdr'),
         ('.img.gz', '.hdr.gz')]

    If you specify ``fileGroups=[('.img', '.hdr')]`` and ``prefix='file'``, and
    both ``file.img`` and ``file.hdr`` exist, the :func:`addExt` function would
    return ``file.img`` (i.e. the file which matches the first extension in
    the group).

    Similarly, if you call the :func:`.imcp.imcp` or :func:`.imcp.immv`
    functions with the above parameters, both ``file.img`` and ``file.hdr``
    will be moved.

    .. note:: The primary use-case of file groups is to resolve ambiguity with
              respect to NIFTI and ANALYSE75 image pairs. By specifying
              ``fileGroups=[('.img', '.hdr'), ('.img.gz', '.hdr.gz')]``, the
              :func:`addExt`, :func:`.imcp.immv` and :func:`.imcp.imcp`
              functions are able to figure out what you mean when you specify
              ``file``, and both ``file.hdr`` and ``file.img`` (or
              ``file.hdr.gz`` and ``file.img.gz``) exist.

    :arg path:        Path to the file. Must contain the file extension.

    :arg allowedExts: Allowed/recognised file extensions.

    :arg fileGroups:  Recognised file groups.

    :arg fullPaths:   If ``True`` (the default), full file paths (relative to
                      the ``path``) are returned. Otherwise, only the file
                      extensions in the group are returned.

    :arg unambiguous: Defaults to ``False``. If ``True``, and the path
                      is not unambiguously part of one group, or part of
                      no groups, a :exc:`PathError` is raised.
                      Otherwise, the path is returned.
    """

    path = addExt(path, allowedExts, mustExist=True, fileGroups=fileGroups)
    base, ext = splitExt(path, allowedExts)

    if fileGroups is None:
        if fullPaths: return [path]
        else:         return [ext]

    matchedGroups     = []
    matchedGroupFiles = []
    fullMatches       = 0
    partialMatches    = 0

    for group in fileGroups:

        if ext != '' and ext not in group:
            continue

        groupFiles = [base + s for s in group]
        exist      = [op.exists(f) for f in groupFiles]

        if any(exist):
            partialMatches += 1

        if all(exist):
            fullMatches += 1
            matchedGroups    .append(group)
            matchedGroupFiles.append(groupFiles)

    # Path is not part of any group
    if partialMatches == 0:
        if fullPaths: return [path]
        else:         return [ext]

    # If the given path is part of more
    # than one existing file group, we
    # can't resolve this ambiguity.
    if fullMatches > 1:
        raise PathError('Path is part of multiple '
                        'file groups: {}'.format(path))

    # If the unambiguous flag is not set,
    # we don't care about partial matches
    if not unambiguous:
        partialMatches = 0

    # The path is unambiguously part of a
    # complete file group - resolve it to
    # the first element of the group
    if fullMatches == 1 and partialMatches <= 1:
        if fullPaths: return matchedGroupFiles[0]
        else:         return matchedGroups[    0]

    # The path appears to be part of
    # an incomplete group - this is
    # potentially ambiguous, so give
    # up (but see the partialMatches
    # clobber above).
    elif partialMatches > 0:
        raise PathError('Path is part of an incomplete '
                        'file group: {}'.format(path))

    else:
        if fullPaths: return [path]
        else:         return [ext]


def removeDuplicates(paths, allowedExts=None, fileGroups=None):
    """Reduces the list of ``paths`` down to those which are unique with
    respect to the specified ``fileGroups``.

    For example, if you have a directory containing::

        001.hdr
        001.img
        002.hdr
        002.img
        003.hdr
        003.img

    And you call ``removeDuplicates`` like so::

         paths       = ['001.img', '001.hdr',
                        '002.img', '002.hdr',
                        '003.img', '003.hdr']

         allowedExts = ['.img',  '.hdr']
         fileGroups  = [('.img', '.hdr')]

         removeDuplicates(paths, allowedExts, fileGroups)

    The returned list will be::

         ['001.img', '002.img', '003.img']

    If you provide ``allowedExts``, you may specify incomplete ``paths`` (i.e.
    without extensions), as long as there are no path ambiguities.

    A :exc:`PathError` will be raised if any of the ``paths`` do not exist,
    or if there are any ambiguities with respect to incomplete paths.

    :arg paths:       List of paths to reduce.

    :arg allowedExts: Allowed/recognised file extensions.

    :arg fileGroups:  Recognised file groups - see :func:`getFileGroup`.
    """

    unique = []

    for path in paths:

        groupFiles = getFileGroup(path, allowedExts, fileGroups)

        if not any([p in unique for p in groupFiles]):
            unique.append(groupFiles[0])

    return unique


def uniquePrefix(path):
    """Return the longest prefix for the given file name which unambiguously
    identifies it, relative to the other files in the same directory.

    Raises a :exc:`PathError` if a unique prefix could not be found (which
    will never happen if the path is valid).
    """

    dirname, filename = op.split(path)

    idx    = 0
    prefix = op.join(dirname, filename[0])
    hits   = glob.glob('{}*'.format(prefix))

    while True:

        # Found a unique prefix
        if len(hits) == 1:
            break

        # Should never happen if path is valid
        elif len(hits) == 0 or idx >= len(filename) - 1:
            raise PathError('No unique prefix for {}'.format(filename))

        # Not unique - continue looping
        else:
            idx    += 1
            prefix  = prefix + filename[idx]
            hits    = [h for h in hits if h.startswith(prefix)]

    return prefix


def commonBase(paths):
    """Identifies the deepest common base directory shared by all files
    in ``paths``.

    Raises a :exc:`PathError` if the paths have no common base. This will
    never happen for absolute paths (as the base will be e.g. ``'/'``).
    """

    depths = [len(p.split(op.sep)) for p in paths]
    base   = max(zip(depths, paths), key=operator.itemgetter(0))[1]
    last   = base

    while True:

        base = op.split(base)[0]

        if base == last or len(base) == 0:
            break

        last = base

        if all([p.startswith(base) for p in paths]):
            return base

    raise PathError('No common base')
