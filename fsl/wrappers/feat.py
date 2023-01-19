#!/usr/bin/env python
#
# feat.py - Wrapper for the FSL feat command.
#
# Author: Fidel Alfaro Almagro <fidel.alfaroalmagro@ndcn.ox.ac.uk>
#         Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :func:`feast` function, a wrapper for the FSL
`FEAT <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FEAT>`_ command.
"""

from . import wrapperutils  as wutils

@wutils.fslwrapper
def feat(fsf):
    """Wrapper for the ``feat`` command.

    :arg fsf:       Input fsf (configuration) file


    """

    cmd  = ['feat', fsf]
 
    return cmd
