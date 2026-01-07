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
import            tempfile


def main(argv=None):

    if argv is None:
        argv = sys.argv[1:]

    if len(argv) not in (0, 1):
        raise ValueError('Invalid input - tmpnam expects '
                         'zero or one arguments')

    # Usage #1 - create file in $TMPDIR
    if len(argv) == 0:
        prefix  = 'fsl'
        dirname = None

    elif len(argv) == 1:
        dirname, prefix = op.split(argv[0])

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
        f, name = tempfile.mkstemp(prefix=prefix + '_', dir=dirname)
        os.close(f)
    except Exception as e:
        raise RuntimeError(f'Could not create temporary file '
                           f'(dir: {dirname}, prefix: {prefix})') from e

    print(op.abspath(name))
