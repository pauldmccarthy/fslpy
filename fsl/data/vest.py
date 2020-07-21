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
   loadVestFile
   generateVest
"""


import textwrap as tw
import             io

import numpy as np


def looksLikeVestLutFile(path):
    """Returns ``True`` if the given ``path`` looks like a VEST LUT file,
    ``False`` otherwise.
    """
    with open(path, 'rt') as f:

        lines = []
        for i in range(10):
            line = f.readline()
            if line is None: break
            else:            lines.append(line.strip())

    validHeaders = ('%!VEST-LUT', '%BeginInstance', '%%BeginInstance')

    return len(lines) > 0 and lines[0] in validHeaders


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


def loadVestFile(path, ignoreHeader=True):
    """Loads numeric data from a VEST file, returning it as a ``numpy`` array.

    :arg ignoreHeader: if ``True`` (the default), the matrix shape specified
                       in the VEST header information is ignored, and the shape
                       inferred from the data. Otherwise, if the number of
                       rows/columns specified in the VEST header information
                       does not match the matrix shape, a ``ValueError`` is
                       raised.

    :returns:          a ``numpy`` array containing the matrix data in the
                       VEST file.
    """

    data = np.loadtxt(path, comments=['#', '/'])

    if not ignoreHeader:
        nrows, ncols = None, None
        with open(path, 'rt') as f:
            for line in f:
                if   'NumWaves'  in line: ncols = int(line.split()[1])
                elif 'NumPoints' in line: nrows = int(line.split()[1])
                else: continue

                if (ncols is not None) and (nrows is not None):
                    break

        if tuple(data.shape) != (nrows, ncols):
            raise ValueError(f'Invalid VEST file ({path}) - data shape '
                             f'({data.shape}) does not match header '
                             f'({nrows}, {ncols})')

    return data


def generateVest(data):
    """Generates VEST-formatted text for the given ``numpy`` array.

    :arg data: A 1D or 2D numpy array.
    :returns:  A string containing a VEST header, and the ``data``.
    """

    data = np.asanyarray(data)

    if len(data.shape) not in (1, 2):
        raise ValueError(f'unsupported number of dimensions: {data.shape}')

    data = np.atleast_2d(data)

    if np.issubdtype(data.dtype, np.integer): fmt = '%d'
    else:                                     fmt = '%0.12f'

    sdata = io.StringIO()
    np.savetxt(sdata, data, fmt=fmt)
    sdata = sdata.getvalue()

    nrows, ncols = data.shape

    vest = tw.dedent(f"""
    /NumWaves {ncols}
    /NumPoints {nrows}
    /Matrix
    """).strip() + '\n' + sdata

    return vest.strip()
