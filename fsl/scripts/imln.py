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
import fsl.utils.path as fslpath


# The lists below are defined in the
# fsl.data.image class, but are duplicated
# here for performance (to avoid import of
# nibabel/numpy/etc).
exts = ['.nii.gz',   '.nii',
        '.nii.zst',  '.nii.bz2',
        '.img',      '.hdr',
        '.img.gz' ,  '.hdr.gz',
        '.img.zst' , '.hdr.zst',
        '.img.bz2' , '.hdr.bz2',
        '.mnc',      '.mnc.gz']
"""List of file extensions that are supported by ``imln``. """

groups = [('.hdr',     '.img'),
          ('.hdr.gz',  '.img.gz'),
          ('.hdr.zst', '.img.zst'),
          ('.hdr.bz2', '.img.bz2')]
"""List of known image file groups (image/header file pairs). """


usage = """
Usage: imln <file1> <file2>
  Makes a link (called file2) to file1
  NB: filenames can be basenames or include an extension
""".strip()


def imln(target, linkbase):
    """Create a symlink to the target image. """
    target   = fslpath.removeExt(target,   exts)
    linkbase = fslpath.removeExt(linkbase, exts)

    # Target must exist, so we can
    # infer the correct extension(s).
    # Error on incomplete file groups
    # (e.g. a.img without a.hdr).
    targets = fslpath.getFileGroup(target,
                                   allowedExts=exts,
                                   fileGroups=groups,
                                   unambiguous=True)

    for target in targets:
        if not op.exists(target):
            continue

        ext  = fslpath.getExt(target, exts)
        link = f'{linkbase}{ext}'

        # emulate old imln behaviour - if
        # link already exists, it is removed
        if op.exists(link):
            os.remove(link)

        os.symlink(target, link)

    return 0


def main(argv=None):
    """``imln`` - create sym-links to images. """

    if argv is None:
        argv = sys.argv[1:]

    if len(argv) != 2:
        print(usage)
        return 1

    target, linkbase = argv

    try:
        imln(target, linkbase)

    except Exception as e:
        print(f'Error: {e}')
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
