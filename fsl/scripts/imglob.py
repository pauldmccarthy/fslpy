#!/usr/bin/env python
#
# imglob.py - Expand image file names.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines the ``imglob`` application, which identifies unique
NIFTI/ANALYZE image files.
"""


from __future__ import print_function

import                   sys
import itertools      as it
import fsl.utils.path as fslpath
import fsl.data.image as fslimage


usage = """
Usage: imglob [-extension/extensions] <list of names>
       -extension for one image with full extension
       -extensions for image list with full extensions
""".strip()

exts   = fslimage.ALLOWED_EXTENSIONS
groups = fslimage.FILE_GROUPS


def main(argv=None):
    """The ``imglob`` utility. Given a list of file names, identifies and prints
    the unique NIFTI/ANALYZE image files.
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

    imgfiles = []

    # Build a list of all image files (both
    # hdr and img and otherwise) that match
    for path in paths:
        try:
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

    imgfiles = sorted(set(imgfiles))

    print(' '.join(imgfiles))

    return 0


if __name__ == '__main__':
    sys.exit(main())
