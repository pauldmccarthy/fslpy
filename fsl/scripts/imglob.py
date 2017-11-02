#!/usr/bin/env python
#
# imglob.py - Expand image file names.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines the ``imglob`` application, for expanding glob patterns
involving NIFTI/ANALYZE image file name.
"""


from __future__ import print_function

import os.path        as op
import                   sys
import                   glob
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
    """The ``imglob`` utility. Prints image files which match one or more
    shell-style wildcard patterns.
    """

    if argv is None:
        argv = sys.argv[1:]

    if len(argv) < 1:
        raise RuntimeError(usage)

    if   argv[0] == '-extension':  output = 'primary'
    elif argv[0] == '-extensions': output = 'all'
    else:                          output = 'prefix'

    if output == 'prefix': patterns = argv
    else:                  patterns = argv[1:]

    paths = []

    for pattern in patterns:

        hits = glob.glob(pattern)
        hits = [fslimage.looksLikeImage(h) for h in hits]

        if output == 'prefix':

            hits = fslpath.removeDuplicates(hits,
                                            allowedExts=exts,
                                            fileGroups=groups)
            hits = [fslpath.removeExt(h, exts) for h in hits]
        elif output == 'primary':
            hits = fslpath.removeDuplicates(hits,
                                            allowedExts=exts,
                                            fileGroups=groups)

        paths.extend(hits)

    print(' '.join(paths))


if __name__ == '__main__':
    sys.exit(main())
