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


import fsl.utils.assertions as asrt
from . import wrapperutils  as wutils


@wutils.fileOrImage('out')
@wutils.fslwrapper
def fslmerge(how, out, *images, tr=None, n=None):
    """Wrapper for the ``fslmerge`` command.

    :arg how:           Specifies how the concatenation is done: <-x/y/z/t/a/tr>
                           -t : concatenate images in time
                           -x : concatenate images in the x direction
                           -y : concatenate images in the y direction
                           -z : concatenate images in the z direction
                           -a : auto-choose: single slices -> volume, 
                                             volumes -> 4D (time series)
                           -tr : Concatenate images in time and set the 
                                 output image tr to the final option value
    :arg out:           Output image   
    :arg images:        Different images to concatenate
    :arg tr             tr for the output image when concatenating in ``tr`` mode
    :arg n:             Only use volume <n> from each input file 
                        (first volume is 0, not 1)

    Refer to the ``fslmerge`` command-line help for details on all arguments.
    """

    asrt.assertIsNifti(*images)

    cmd  = ['fslmerge', '-'+how, out] + list(images)
    if tr is not None:
        cmd.append(tr)
    if n is not None:
        cmd.append('-n ' + str(n))

    return cmd
