#!/usr/bin/env python
#
# feat.py - Wrapper for the FSL feat command.
#
# Author: Fidel Alfaro Almagro <fidel.alfaroalmagro@ndcn.ox.ac.uk>
#
"""This module provides the :func:`feast` function, a wrapper for the FSL
`FEAT <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FEAT>`_ command.
"""

from . import wrapperutils as wutils

@wutils.fslwrapper
def feat(fsf):
    """Wrapper for the ``feat`` command.

    :arg fsf: Input fsf (configuration) file
    """
    return ['feat', fsf]


@wutils.fileOrImage('mask')
@wutils.fslwrapper
def featquery(featdirs, stats, outputRootName, mask, **kwargs):
    """Wrapper for the ``featquery`` command. """

    # featquery purports to accept a number of
    # flag arguments, but every argument is
    # in fact a positional (i.e. all flags must
    # be provided in a specific order)
    featdirs = list(featdirs)
    stats    = list(stats)
    vox      = kwargs.pop('vox', None)
    mm       = kwargs.pop('mm',  None)
    a        = kwargs.pop('a',   None)
    p        = kwargs.pop('p',   False)
    t        = kwargs.pop('t',   None)
    i        = kwargs.pop('i',   None)
    s        = kwargs.pop('s',   False)
    w        = kwargs.pop('w',   False)
    b        = kwargs.pop('b',   False)

    if vox is not None and mm is not None:
        raise ValueError('Only one of vox or mm can be provided')

    # featquery arguments must be ordered as follows:
    #   - featdirs
    #   - stats
    #   - output
    #   - -a -p -t -i -s -w -b
    #   - mask
    #   - -vox/-mm
    cmd  = ['featquery']
    cmd += [str(len(featdirs))] + featdirs
    cmd += [str(len(stats))]    + stats
    cmd += [outputRootName]

    if a is not None: cmd += ['-a', a]
    if p:             cmd += ['-p']
    if t is not None: cmd += ['-t', str(t)]
    if i is not None: cmd += ['-i', str(i)]
    if s:             cmd += ['-s']
    if w:             cmd += ['-w']
    if b:             cmd += ['-b']

    cmd += [mask]

    if   vox is not None: cmd += ['-vox'] + [str(v) for v in vox]
    elif mm  is not None: cmd += ['-mm']  + [str(m) for m in mm]

    return cmd
