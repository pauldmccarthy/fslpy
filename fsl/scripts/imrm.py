#!/usr/bin/env python
#
# imrm.py - Remove image files.
#
# Author: Paul McCarthy <paulmc@fmrib.ox.ac.uk>
#
"""This module defines the ``imrm`` application, for removing NIFTI image
files.
"""


import itertools      as it
import os.path        as op
import                   os
import                   sys
import fsl.utils.path as fslpath


usage = """Usage: imrm <list of image names to remove>
NB: filenames can be basenames or not
""".strip()


# This list is defined in the
# fsl.data.image class, but are duplicated
# here for performance (to avoid import of
# nibabel/numpy/etc).
exts = ['.nii.gz', '.nii',
        '.img',    '.hdr',
        '.img.gz', '.hdr.gz',
        '.mnc',    '.mnc.gz']
"""List of file extensions that are removed by ``imrm``. """


def main(argv=None):
    """Removes all images which are specified on the command line. """

    if argv is None:
        argv = sys.argv[1:]

    if len(argv) < 1:
        print(usage)
        return 1

    prefixes = [fslpath.removeExt(p, exts) for p in argv]

    for prefix, ext in it.product(prefixes, exts):

        path = f'{prefix}{ext}'

        if op.exists(path):
            os.remove(path)

    return 0


if __name__ == '__main__':
    sys.exit(main())
