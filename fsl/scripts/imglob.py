#!/usr/bin/env python
#
# imglob.py - Expand image file names.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines the ``imglob`` application, which identifies unique
NIFTI/ANALYZE image files.
"""


import itertools      as it
import                   glob
import                   sys
import fsl.utils.path as fslpath


usage = """
Usage: imglob [-extension/extensions] <list of names>
       -extension for one image with full extension
       -extensions for image list with full extensions
""".strip()


# The lists below are defined in the
# fsl.data.image class, but are duplicated
# here for performance (to avoid import of
# nibabel/numpy/etc).
exts   = ['.nii.gz', '.nii', '.img', '.hdr', '.img.gz', '.hdr.gz']
"""List of supported image file extensions. """


groups = [('.hdr', '.img'), ('.hdr.gz', '.img.gz')]
"""List of known image file groups (image/header file pairs). """


def imglob(paths, output=None):
    """Given a list of file names, identifies and returns the unique
    NIFTI/ANALYZE image files that exist.

    :arg paths:  Sequence of paths/prefixes to glob.

    :arg output: One of ``'prefix'`` (the default), ``'all'``, or
                 ``'primary'``:

                  - ``'prefix'``:  Returns the files without extensions.
                  - ``'all'``:     Returns all files that match (e.g. both
                                   ``.img`` and ``.hdr`` files will be
                                   returned).
                  - ``'primary'``: Returns only the primary file of each
                                   matching file group, e.g. only the
                                   ``.hdr`` file would be returned from
                                   an ``.img``/``.hdr`` pair.

    :returns: A sequence of resolved path names, in the form specified
              by the ``output`` parameter.
    """

    if output is None:
        output = 'prefix'

    if output not in ('prefix', 'all', 'primary'):
        raise ValueError('Unsupported output format: {}'.format(output))

    imgfiles = []

    # Expand any wildcard paths if provided.
    # Depending on the way that imglob is
    # invoked, this may not get done by the
    # calling shell.
    #
    # We also have to handle incomplete
    # wildcards, e.g. if the user provides
    # "img_??", we need to add possible
    # file suffixes before it can be
    # expanded.
    expanded = []
    for path in paths:
        if any(c in path for c in '*?[]'):
            if fslpath.hasExt(path, exts):
                globs = [path]
            else:
                globs = [f'{path}{ext}' for ext in exts]
            globs = [glob.glob(g) for g in globs]
            expanded.extend(it.chain(*globs))
        else:
            expanded.append(path)

    paths = expanded

    # Build a list of all image files (both
    # hdr and img and otherwise) that match
    for path in paths:
        try:
            path = fslpath.removeExt(path, allowedExts=exts)
            imgfiles.extend(fslpath.addExt(path,
                                           allowedExts=exts,
                                           unambiguous=False))
        except fslpath.PathError:
            continue

    if output == 'prefix':
        imgfiles = fslpath.removeDuplicates(imgfiles,
                                            allowedExts=exts,
                                            fileGroups=groups)
        imgfiles = [fslpath.removeExt(f, exts) for f in imgfiles]

    elif output == 'primary':
        imgfiles = fslpath.removeDuplicates(imgfiles,
                                            allowedExts=exts,
                                            fileGroups=groups)

    return list(sorted(set(imgfiles)))


def main(argv=None):
    """The ``imglob`` application. Given a list of file names, identifies and
    prints the unique NIFTI/ANALYZE image files.
    """

    if argv is None:
        argv = sys.argv[1:]

    if len(argv) < 1:
        print(usage)
        return 1

    if   argv[0] == '-extension':  output = 'primary'
    elif argv[0] == '-extensions': output = 'all'
    else:                          output = 'prefix'

    if output == 'prefix': paths = argv
    else:                  paths = argv[1:]

    imgfiles = imglob(paths, output)

    if len(imgfiles) > 0:
        print(' '.join(imgfiles))

    return 0


if __name__ == '__main__':
    sys.exit(main())
