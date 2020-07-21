#!/usr/bin/env python
#
# Vest2Text.py - Convert a VEST matrix file into a plain text ASCII file.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""``Vest2Text`` takes a VEST file containing a 2D matrix, and converts it
into a plain-text ASCII file.
"""


import sys

import numpy as np

import fsl.data.vest as fslvest


usage = "Usage: Vest2Text <vest_file> <text_file>"


def main(argv=None):
    """Convert a VEST file to a plain text file. """

    if argv is None:
        argv = sys.argv[1:]

    if len(argv) != 2:
        print(usage)
        return 0

    infile, outfile = argv
    data            = fslvest.loadVestFile(infile)

    if np.issubdtype(data.dtype, np.integer): fmt = '%d'
    else:                                     fmt = '%0.12f'

    np.savetxt(outfile, data, fmt=fmt)

    return 0


if __name__ == '__main__':
    sys.exit(main())
