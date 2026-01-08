#!/usr/bin/env python
#
# remove_ext.py - Remove file extensions from NIFTI image paths
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import                   sys
import fsl.utils.path as fslpath


usage = """Usage: remove_ext <list of image paths to remove extension from>
""".strip()


# This list is defined in the
# fsl.data.image class, but are duplicated
# here for performance (to avoid import of
# nibabel/numpy/etc).
exts = ['.nii.gz',  '.nii',
        '.nii.zst', '.nii.bz2',
        '.img',     '.hdr',
        '.img.gz',  '.hdr.gz',
        '.img.zst', '.hdr.zst',
        '.img.bz2', '.hdr.bz2',
        '.mnc',     '.mnc.gz']
"""List of file extensions that are removed by ``remove_ext``. """


def remove_ext(*paths):
    """Remove the file extension from all specified paths. """

    removed = []

    for path in paths:
        removed.append(fslpath.removeExt(path, exts))

    return removed


def main(argv=None):
    """Removes file extensions from all paths which are specified on the
    command line.
    """

    if argv is None:
        argv = sys.argv[1:]

    if len(argv) < 1:
        print(usage)
        return 1

    try:
        removed = remove_ext(*argv)

    except Exception as e:
        print(f'remove_ext error: {e}')
        return 1

    print(' '.join(removed))

    return 0


if __name__ == '__main__':
    sys.exit(main())
