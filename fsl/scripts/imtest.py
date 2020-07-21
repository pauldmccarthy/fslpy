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
import                   warnings

import fsl.utils.path as fslpath

# See atlasq.py for explanation
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=FutureWarning)
    import fsl.data.image as fslimage


ALLOWED_EXTENSIONS = fslimage.ALLOWED_EXTENSIONS + ['.mnc', '.mnc.gz']
"""List of file extensions that are supported by ``imln``. """


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

    path = fslpath.removeExt(argv[0], ALLOWED_EXTENSIONS)
    path = op.realpath(path)

    # getFileGroup will raise an error
    # if the image (including all
    # components - i.e. header and
    # image) does not exist
    try:
        fslpath.getFileGroup(path,
                             allowedExts=ALLOWED_EXTENSIONS,
                             fileGroups=fslimage.FILE_GROUPS,
                             unambiguous=True)
        print('1')
    except fslpath.PathError:
        print('0')

    return 0


if __name__ == '__main__':
    sys.exit(main())
