#!/usr/bin/env python
#
# avwutils.py - Wrappers for AVW Utils FSL command-line tools.
#
# Author: Fidel Alfaro Almagro <fidel.alfaroalmagro@ndcn.ox.ac.uk>
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains wrapper functions for various `FSL
<https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/>`_ command-line tools.
"""


import functools as ft

import fsl.utils.assertions as asrt
from . import wrapperutils  as wutils


def fslmerge(axis, output, *images, **kwargs):
    """Wrapper for the ``fslmerge`` command.

    This function emulates the ``fslmerge`` command-line, despite its
    inconsistencies::

        fslmerge -<txyza> out in1 in2 in3
        fslmerge -tr      out in1 in2 in3 <tr>
        fslmerge -n <n>   out in1 in2 in3

    If ``axis == 'n'``, the first positional argument is assumed to be
    the volume index.

    If ``axis == 'tr'``, the last positional argument is assumed to be
    the TR time.

    Refer to the ``fslmerge`` command-line help for details on all arguments.
    """

    if axis == 'n':
        n      = images[0]
        images = images[1:]
        func   = ft.partial(_fslmerge_n, n=n)
    elif axis == 'tr':
        tr     = images[-1]
        images = images[:-1]
        func   = ft.partial(_fslmerge_tr, tr=tr)
    else:
        func   = ft.partial(_fslmerge, axis=axis)

    asrt.assertIsNifti(*images)
    return func(axis, output, *images, **kwargs)


@wutils.fileOrImage('images', 'output')
@wutils.fslwrapper
def _fslmerge(axis, output, *images):
    """Calls ``fslmerge -<txyza> output [image image ...]``. """
    return ['fslmerge', f'-{axis}', output] + list(images)


@wutils.fileOrImage('images', 'output')
@wutils.fslwrapper
def _fslmerge_n(n, output, *images):
    """Calls ``fslmerge -n <n> output [image image ...]``. """
    return ['fslmerge', '-n', str(n), output] + list(images)


@wutils.fileOrImage('images', 'output')
@wutils.fslwrapper
def _fslmerge_tr(tr, output, *images):
    """Calls ``fslmerge -tr output [image image ...] <tr>``. """
    return ['fslmerge', '-tr', output] + list(images) + [str(tr)]
