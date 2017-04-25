#!/usr/bin/env python
#
# vest.py - Functions for working with VEST files.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains a handful of functions for working with VEST files.

.. autosummary::
   :nosignatures:

   looksLikeVestLutFile
   loadVestLutFile
"""


import numpy as np


def looksLikeVestLutFile(path):
    """Returns ``True`` if the given ``path`` looks like a VEST LUT file,
    ``False`` otherwise.
    """
    with open(path, 'rt') as f:
        return f.readline().strip() == '%!VEST-LUT'


def loadVestLutFile(path, normalise=True):
    """Assumes that the given file is a VEST LUT file, and attempts to load it.

    Returns a ``numpy.float32`` array of shape ``(n, 3)``, where ``n`` is the
    number of colours in the file.

    If ``normalise=True`` (the default), the colour values are normalised to
    the range ``0-1``.
    """

    with open(path, 'rt') as f:
        lines = f.readlines()

    # We over-allocate the colour array
    # here, and truncate the array after
    # reading. idx keepsd track of the
    # number of colours read in.
    idx     = 0
    colours = np.zeros((len(lines), 3), dtype=np.float32)

    for line in lines:

        if not line.startswith('<-color{'):
            continue

        start = line.index('{') + 1
        end   = line.index('}')

        r, g, b         = line[start:end].split(',')
        colours[idx, :] = float(r), float(g), float(b)

        idx += 1

    colours = colours[:idx, :]

    if normalise:
        cmin = colours.min()
        cmax = colours.max()
        return (colours - cmin) / (cmax - cmin)

    else:
        return colours
