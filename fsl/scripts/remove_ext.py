#!/usr/bin/env python
#
# remove_ext.py - Remove file extensions from NIFTI image paths
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import sys
import warnings

import fsl.utils.path as fslpath

# See atlasq.py for explanation
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=FutureWarning)
    import fsl.data.image as fslimage


usage = """Usage: remove_ext <list of image paths to remove extension from>
""".strip()


ALLOWED_EXTENSIONS = fslimage.ALLOWED_EXTENSIONS + ['.mnc', '.mnc.gz']
"""List of file extensions that are removed by ``remove_ext``. """


def main(argv=None):
    """Removes file extensions from all paths which are specified on the
    command line.
    """

    if argv is None:
        argv = sys.argv[1:]

    if len(argv) < 1:
        print(usage)
        return 1

    removed = []

    for path in argv:
        removed.append(fslpath.removeExt(path, ALLOWED_EXTENSIONS))

    print(' '.join(removed))

    return 0


if __name__ == '__main__':
    sys.exit(main())
