#!/usr/bin/env python
#
# tmpnam - create temporary file names.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The ``tmpnam`` script has the following usage scenarios

 1. ``$FSLDIR/bin/tmpnam``

     Create a file in ``$TMPDIR``, called ``$TMPDIR/fsl_XXXXXX``

 2. ``$FSLDIR/bin/tmpnam prefix``

    Create a file in the current directory called ``prefix_XXXXXX``

 3. ``$FSLDIR/bin/tmpnam /some/dir/``

    Create a file in the ``/some/dir/`` called ``fsl_XXXXXX``

 4. ``$FSLDIR/bin/tmpnam /some/dir/prefix``

    Create a file in the ``/some/dir/`` called ``prefix_XXXXXX``

 5. ``$FSLDIR/bin/tmpnam /tmp/prefix``

    A special case of #4.
    Create a file in ``$TMPDIR`` called ``$TMPDIR/prefix_XXXXXX``
    (i.e. ``/tmp/`` is replaced with ``$TMPDIR``)

In all cases, the name of the file that was created is printed to standard
output.
"""


import            os
import os.path as op
import            sys

from fsl.utils import tempdir


def tmpnam(path=None):
    """``tmpnam`` function - create a named temporary file, returning its
    path.
    """
    # Usage #1 - create file in $TMPDIR
    if path is None:
        prefix  = 'fsl'
        dirname = None

    else:
        dirname, prefix = op.split(path)

        # Usage #2 - create file in cwd
        if dirname == '':
            dirname = os.getcwd()

        # usage #5 - replace /tmp with $TMPDIR
        elif dirname == '/tmp':
            dirname = None

        # Usage #3
        if prefix == '':
            prefix = 'fsl'

    try:
        name = tempdir.mkstemp(prefix=prefix + '_', dir=dirname)

    except Exception as e:
        raise RuntimeError(f'Could not create temporary file '
                           f'(dir: {dirname}, prefix: {prefix})') from e

    return op.abspath(name)


def main(argv=None):
    """``tmpnam`` entry point. """

    if argv is None:
        argv = sys.argv[1:]

    if len(argv) not in (0, 1):
        print('Invalid input - tmpnam expects '
              'zero or one arguments')
        return 1

    if len(argv) == 0: path = None
    else:              path = argv[0]

    try:
        path = tmpnam(path)
        print(path)
        return 0

    except Exception as e:
        print(f'tmpnam error: {e}')
        return 1
