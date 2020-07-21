#!/usr/bin/env python
#
# imln.py - Create symbolic links to image files.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines the ``imln`` application, for creating sym-links
to NIFTI image files.

.. note:: When creating links to relative paths, ln requires that the path is
          relative to the link location, rather than the invocation
          location. This is *not* currently supported by imln, and possibly
          never will be.
"""


import os.path        as op
import                   os
import                   sys
import                   warnings

import fsl.utils.path as fslpath


# See atlasq.py for explanation
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=FutureWarning)
    import fsl.data.image as fslimage


ALLOWED_EXTENSIONS = fslimage.ALLOWED_EXTENSIONS + ['.mnc', '.mnc.gz']
"""List of file extensions that are supported by ``imln``. """


usage = """
Usage: imln <file1> <file2>
  Makes a link (called file2) to file1
  NB: filenames can be basenames or include an extension
""".strip()


def main(argv=None):
    """``imln`` - create sym-links to images. """

    if argv is None:
        argv = sys.argv[1:]

    if len(argv) != 2:
        print(usage)
        return 1

    target, linkbase = argv
    target           = fslpath.removeExt(target,   ALLOWED_EXTENSIONS)
    linkbase         = fslpath.removeExt(linkbase, ALLOWED_EXTENSIONS)

    # Target must exist, so we can
    # infer the correct extension(s).
    # Error on incomplete file groups
    # (e.g. a.img without a.hdr).
    try:
        targets = fslpath.getFileGroup(target,
                                       allowedExts=ALLOWED_EXTENSIONS,
                                       fileGroups=fslimage.FILE_GROUPS,
                                       unambiguous=True)
    except Exception as e:
        print(f'Error: {e}')
        return 1

    for target in targets:
        if not op.exists(target):
            continue

        ext  = fslpath.getExt(target, ALLOWED_EXTENSIONS)
        link = f'{linkbase}{ext}'

        try:

            # emulate old imln behaviour - if
            # link already exists, it is removed
            if op.exists(link):
                os.remove(link)

            os.symlink(target, link)

        except Exception as e:
            print(f'Error: {e}')
            return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
