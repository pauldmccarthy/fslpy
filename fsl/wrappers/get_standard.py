#!/usr/bin/env python
#
# fugue.py - Wrapper for the fsl_get_standard command.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains wrapper function for the ``fsl_get_standard`` command.
"""


from . import wrapperutils as wutils


def get_standard(image_type=None, modality=None, **kwargs):
    """Wrapper for the ``fsl_get_standard`` command.
    Only returns standard output - the standard error is suppressed.
    """
    return _get_standard(image_type, modality, **kwargs)[0].strip()


@wutils.fslwrapper
def _get_standard(image_type=None, modality=None, **kwargs):
    """Real wrapper for the ``fsl_get_standard`` command."""

    cmd = ['fsl_get_standard']

    if image_type is not None: cmd += [image_type]
    if modality   is not None: cmd += [modality]

    return cmd + wutils.applyArgStyle('--=', **kwargs)
