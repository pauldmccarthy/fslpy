#!/usr/bin/env python
#
# fsl_abspath.py - Make a path absolute
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The fsl_abspath command - makes relative paths absolute.
"""


import os.path as op
import            sys


usage = """
usage: fsl_abspath path
""".strip()


def main(argv=None):
    """fsl_abspath - make a relative path absolute. """

    if argv is None:
        argv = sys.argv[1:]

    if len(argv) != 1:
        print(usage)
        return 1

    print(op.realpath(argv[0]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
