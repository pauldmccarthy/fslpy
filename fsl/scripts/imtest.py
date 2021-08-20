#!/usr/bin/env python
#
# imtest.py - Test whether an image file exists or not.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The ``imtest`` script can be used to test whether an image file exists or
not, without having to know the file suffix (.nii, .nii.gz, etc).
"""


import os.path        as op
import                   sys
import fsl.utils.path as fslpath


# The lists below are defined in the
# fsl.data.image class, but are duplicated
# here for performance (to avoid import of
# nibabel/numpy/etc).
exts = ['.nii.gz', '.nii',
        '.img',    '.hdr',
        '.img.gz', '.hdr.gz',
        '.mnc',    '.mnc.gz']
"""List of file extensions that are supported by ``imtest``.
"""

groups = [('.hdr', '.img'), ('.hdr.gz', '.img.gz')]
"""List of known image file groups (image/header file pairs). """


def main(argv=None):
    """Test if an image path exists, and prints ``'1'`` if it does or ``'0'``
    if it doesn't.
    """

    if argv is None:
        argv = sys.argv[1:]

    # emulate old fslio/imtest - always return 0
    if len(argv) != 1:
        print('0')
        return 0

    path = fslpath.removeExt(argv[0], exts)
    path = op.realpath(path)

    # getFileGroup will raise an error
    # if the image (including all
    # components - i.e. header and
    # image) does not exist
    try:
        fslpath.getFileGroup(path,
                             allowedExts=exts,
                             fileGroups=groups,
                             unambiguous=True)
        print('1')
    except fslpath.PathError:
        print('0')

    return 0


if __name__ == '__main__':
    sys.exit(main())
