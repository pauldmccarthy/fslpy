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

    # Suppress stdout unless otherwise instructed
    kwargs['log'] = kwargs.get('log', {'tee' : False})

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


def smoothest(inimg=None, **kwargs):
    """Wrapper for the ``smoothest`` command.

    The residual or zstatistic image may be passed as the first positional
    argument (``inimg``) - its type is inferred from the image file name if
    possible.  If this is not possible (e.g. non-standard file names or
    in-memory images), you must specify residual images via ``res``, or
    zstatistic images via ``zstat``.

    Returns a dictionary containing the parameters estimated by ``smoothest``,
    e.g.::

        {
            'DLH'       : 1.25903,
            'VOLUME'    : 239991,
            'RESELS'    : 3.69574,
            'FWHMvoxel' : [1.57816, 1.64219, 1.42603],
            'FWHMmm'    : [3.15631, 3.28437, 2.85206]
        }
    """

    # Suppress stdout unless otherwise instructed
    kwargs['log'] = kwargs.get('log', {'tee' : False})

    result = _smoothest(**kwargs)
    result = result.stdout[0]
    result = result.strip().split('\n')[-5:]
    values = {}

    for line in result:
        key, vals = line.split(maxsplit=1)
        vals      = [float(v) for v in vals.split()]

        if len(vals) == 1:
            vals = vals[0]

        values[key] = vals

    return values


@wutils.fileOrImage('inimg', 'r', 'res', 'z', 'zstat', 'm', 'mask')
@wutils.fslwrapper
def _smoothest(inimg=None, **kwargs):
    """Actual wrapper for the ``smoothest`` command."""

    if inimg is not None:
        if   'res4d' in inimg: kwargs['res']   = inimg
        elif 'zstat' in inimg: kwargs['zstat'] = inimg
        else: raise RuntimeError('Cannot infer type of input '
                                 f'image {inimg.name}')

    valmap = {
        'V'       : wutils.SHOW_IF_TRUE,
        'verbose' : wutils.SHOW_IF_TRUE,
    }

    return ['smoothest'] + wutils.applyArgStyle('--=', valmap=valmap, **kwargs)
