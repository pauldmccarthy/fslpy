#!/usr/bin/env python
#
# cluster.py - Wrapper for the FSL cluster command.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains the :func:`cluster` function, which calls
the FSL ``cluster`` / ``fsl-cluster``command.
"""


import io
import numpy as np

from . import wrapperutils as wutils


def cluster(infile, thres, load=True, **kwargs):
    """Wrapper function for the FSL ``cluster`/``fsl-cluster``) command.

    If ``load is True`` (the default) a tuple is returned, containing:
      - A numpy array containing the cluster table
      - A list of column titles
      - A dictionary containing references to the standard output as an
        attribute called ``stdout``, and to the output images if any,
        e.g. ``--oindex``.

    If ``load is False``, only the dictionary is returned.
    """

    result = _cluster(infile, thres, **kwargs)

    if load:
        header, data = result.stdout[0].split('\n', 1)
        titles       = header.split('\t')
        data         = np.loadtxt(io.StringIO(data), delimiter='\t')

        return data, titles, result
    else:
        return result


@wutils.fileOrImage('infile', 'othresh', 'olmaxim', 'osize',
                    'omax', 'omean', 'opvals', 'cope', 'warpvol',)
@wutils.fslwrapper
def _cluster(infile, thresh, **kwargs):
    """Actual wrapper function for the FSL ``cluster``/``fsl-cluster`` command.
    """

    valmap = {
        'fractional'     : wutils.SHOW_IF_TRUE,
        'mm'             : wutils.SHOW_IF_TRUE,
        'min'            : wutils.SHOW_IF_TRUE,
        'no_table'       : wutils.SHOW_IF_TRUE,
        'minclustersize' : wutils.SHOW_IF_TRUE,
        'scalarname'     : wutils.SHOW_IF_TRUE,
        'verbose'        : wutils.SHOW_IF_TRUE,
        'voxthresh'      : wutils.SHOW_IF_TRUE,
        'voxuncthresh'   : wutils.SHOW_IF_TRUE,
    }

    cmd  = ['fsl-cluster', '-i', infile, '-t', str(thresh)]
    cmd += wutils.applyArgStyle('--=', valmap=valmap, **kwargs)

    return cmd
