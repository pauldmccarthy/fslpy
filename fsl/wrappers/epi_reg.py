#!/usr/bin/env python
#
# epi_reg.py - Wrapper for the epi_reg command.
#
# Author: 
#
"""This module provides the :func:`epi_reg` function, a wrapper for the FSL
`epi_reg <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FLIRT/UserGuide#epi_reg>`_ command.
"""

import fsl.utils.assertions as asrt
from . import wrapperutils  as wutils

@wutils.fileOrImage('epi', 't1', 't1brain', 'fmap', 'fmapmag', 'fmapmagbrain', 'gdc', 'wmseg', 'weight', outprefix='out')
@wutils.fslwrapper
def epi_reg(epi, t1, t1brain, out='epi_reg', **kwargs):
    """Wrapper for the ``epi_reg`` command.

    :arg epi:       Input EPI image
    :arg t1:        Input wholehead T1 image
    :arg t1brain:   Input brain extracted T1 image
    :arg out:       Output name
    """
    asrt.assertIsNifti(epi)
    asrt.assertIsNifti(t1)
    asrt.assertIsNifti(t1brain)

    valmap = {
        'nofmapreg' : wutils.SHOW_IF_TRUE,
        'noclean' : wutils.SHOW_IF_TRUE,
        'v' : wutils.SHOW_IF_TRUE,
    }

    cmd  = ['epi_reg', '--epi='+epi, '--t1='+t1, '--t1brain='+t1brain, '--out='+out]

    cmd += wutils.applyArgStyle('--=',
                                valmap=valmap,
                                singlechar_args=True,
                                **kwargs)

    return cmd
