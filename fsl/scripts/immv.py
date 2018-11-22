#!/usr/bin/env python
#
# immv.py - Move image files.
#
# Author: Paul McCarthy <paulmc@fmrib.ox.ac.uk>
#

"""This module defines the ``immv`` application, for moving NIFTI image
files.

The :func:`main` function is essentially a wrapper around the
:func:`fsl.utils.imcp.immv` function - see its documentation for more details.
"""


from __future__ import print_function

import os.path        as op
import                   sys
import                   warnings

import fsl.utils.path as fslpath

# See atlasq.py for explanation
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=FutureWarning)
    import fsl.utils.imcp as imcp
    import fsl.data.image as fslimage


usage = """Usage:
  immv <file1> <file2>
  immv <file1> <directory>
  immv <file1> <file2> ... <fileN> <directory>

Moves images from <file1> to <file2>, or move all <file>s to <directory>

NB: filenames can be basenames or include an extension.

Recognised file extensions: {}
""".format(', '.join(fslimage.ALLOWED_EXTENSIONS))


def main(argv=None):
    """Parses CLI arguments (see the usage string), and calls the
    fsl.utils.imcp.immv function on each input.
    """

    if argv is None:
        argv = sys.argv[1:]

    if len(argv) < 2:
        print(usage)
        return 1

    srcs = argv[:-1]
    dest = argv[ -1]

    if len(srcs) > 1 and not op.isdir(dest):
        print(usage)
        return 1

    try:
        srcs = [fslimage.fixExt(s) for s in srcs]
        srcs = fslpath.removeDuplicates(
            srcs,
            allowedExts=fslimage.ALLOWED_EXTENSIONS,
            fileGroups=fslimage.FILE_GROUPS)

        for src in srcs:
            imcp.immv(src, dest, useDefaultExt=True, overwrite=True)

    except Exception as e:
        print(str(e))
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
