#!/usr/bin/env python
#
# Data format conversion script (between various nifti and Analyze flavours)
#
# Author: Mark Jenkinson
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The ``fslchfiletype`` command can be used to change the format of
NIfTI/ANALYZE image files.
"""

import os
import sys
import contextlib

from fsl.wrappers import (imtest,
                          imcp,
                          immv,
                          imrm,
                          remove_ext,
                          tmpnam)


USAGE = """
Usage: fslchfiletype <filetype> <filename> [filename2]
Changes the file type of the image file [ or copies to new file ].
Valid values for filetype are:
  NIFTI
  NIFTI_GZ
  NIFTI_ZST
  NIFTI_BZ2
  NIFTI_PAIR
  NIFTI_PAIR_GZ
  NIFTI_PAIR_ZST
  NIFTI_PAIR_BZ2
  NIFTI2
  NIFTI2_GZ
  NIFTI2_ZST
  NIFTI2_BZ2
  NIFTI2_PAIR
  NIFTI2_PAIR_GZ
  NIFTI2_PAIR_ZST
  NIFTI2_PAIR_BZ2
""".strip()


@contextlib.contextmanager
def patchenv(**kwargs):
    """Context manager which temporarily modifies environment
    variable values in ``os.environ``.
    """
    oldvals = {k : os.environ.get(k, None) for k in kwargs.keys()}

    for k, v in kwargs.items():
        os.environ[k] = v

    try:
        yield

    finally:
        for k, v in oldvals.items():
            if v is None:
                os.environ.pop(k)
            else:
                os.environ[k] = v


def fslchfiletype(fmt, oldfile, newfile=None):
    """Change the format of ``oldfile`` to ``fmt``, saving the result
    in-place, or to ``newfile``.
    """

    oldfile = remove_ext(oldfile)
    inplace = newfile is None

    if not inplace:
        newfile = remove_ext(newfile)
    else:
        # for in-place conversions we save the conversion to
        # a temp file, then remove the original and move the
        # conversion to its place. This is done so that we
        # don't end up in the situation of having image files
        # with the same prefix and different suffixes in the
        # same directory, as this would confuse imrm.
        newfile = tmpnam()

    with patchenv(FSLOUTPUTTYPE=fmt):

        # do the copy / type conversion
        imcp(oldfile, newfile)

        # For inplace conversion remove and copy original file.
        # Exact mechanism is to be careful not to remove old if a
        # new one isn't writable in this place (eg over quota).
        if inplace and imtest(newfile):
            oldtmp = f'{oldfile}TMP'
            immv(newfile, oldtmp)
            if imtest(oldtmp):
                imrm(oldfile)
                immv(oldtmp, oldfile)


def main(argv=None):
    """The ``fslchfiletype`` script.  Changes the format of a NIfTI/ANALYZE
    file.
    """

    if argv is None:
        argv = sys.argv[1:]

    if len(argv) not in (2, 3):
          print(USAGE)
          return 1

    try:
        fslchfiletype(*argv)

    except Exception as e:
        print(f'fslchfiletype error: {e}')
        return 1

    return 0
