#!/usr/bin/env python
#
# imrm.py - Remove image files.
#
# Author: Paul McCarthy <paulmc@fmrib.ox.ac.uk>
#
"""This module defines the ``imrm`` application, for removing NIFTI image
files.
"""


import os.path            as op
import                       os
import                       sys
import fsl.scripts.imglob as imglob


usage = """Usage: imrm <list of image names to remove>
NB: filenames can be basenames or not
""".strip()


def main(argv=None):
    """Removes all images which are specified on the command line. """

    if argv is None:
        argv = sys.argv[1:]

    if len(argv) < 1:
        print(usage)
        return 1

    paths = imglob.imglob(argv, 'all')

    for path in paths:
        if op.exists(path):
            os.remove(path)

    return 0


if __name__ == '__main__':
    sys.exit(main())
