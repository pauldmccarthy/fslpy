#!/usr/bin/env python
#
# imglob.py - Expand image file names.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines the ``imglob`` application, which identifies unique
NIFTI/ANALYZE image files.
"""


import                   sys
import                   warnings
import fsl.utils.path as fslpath

# See atlasq.py for explanation
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=FutureWarning)
    import fsl.data.image as fslimage


usage = """
Usage: imglob [-extension/extensions] <list of names>
       -extension for one image with full extension
       -extensions for image list with full extensions
""".strip()

exts   = fslimage.ALLOWED_EXTENSIONS
groups = fslimage.FILE_GROUPS


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

    # Build a list of all image files (both
    # hdr and img and otherwise) that match
    for path in paths:
        try:
            path = fslimage.removeExt(path)
            imgfiles.extend(fslimage.addExt(path, unambiguous=False))
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
