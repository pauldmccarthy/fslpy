#!/usr/bin/env python
#
# Text2Vest.py - Convert an ASCII text matrix file into a VEST file.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""``Text2Vest`` simply takes a plain text ASCII text matrix file, and
adds a VEST header.
"""


import sys

import numpy as np

import fsl.data.vest as fslvest


usage = "Usage: Text2Vest <text_file> <vest_file>"


def main(argv=None):
    """Convert a plain text file to a VEST file. """

    if argv is None:
        argv = sys.argv[1:]

    if len(argv) != 2:
        print(usage)
        return 0

    infile, outfile = argv
    data            = np.loadtxt(infile)
    vest            = fslvest.generateVest(data)

    with open(outfile, 'wt') as f:
        f.write(vest)

    return 0


if __name__ == '__main__':
    sys.exit(main())
