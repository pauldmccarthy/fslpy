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
import                   warnings

import fsl.utils.path as fslpath

# See atlasq.py for explanation
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=FutureWarning)
    import fsl.data.image as fslimage


usage = """Usage: imrm <list of image names to remove>
NB: filenames can be basenames or not
""".strip()


ALLOWED_EXTENSIONS = fslimage.ALLOWED_EXTENSIONS + ['.mnc', '.mnc.gz']
"""List of file extensions that are removed by ``imrm``. """


def main(argv=None):
    """Removes all images which are specified on the command line. """

    if argv is None:
        argv = sys.argv[1:]

    if len(argv) < 1:
        print(usage)
        return 1

    prefixes = [fslpath.removeExt(p, ALLOWED_EXTENSIONS) for p in argv]

    for prefix, ext in it.product(prefixes, ALLOWED_EXTENSIONS):

        path = f'{prefix}{ext}'

        if op.exists(path):
            os.remove(path)

    return 0


if __name__ == '__main__':
    sys.exit(main())
