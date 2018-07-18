#!/usr/bin/env python
#
# fast.py - Wrapper for the FSL fast command.
#
# Author: Martin Craig <martin.craig@eng.ox.ac.uk>
#         Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :func:`fast` function, a wrapper for the FSL
`FAST <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FAST>`_ command.
"""


import six

import fsl.utils.assertions as asrt
from . import wrapperutils  as wutils


@wutils.fileOrImage('imgs', 'A', 's', 'manualseg', outprefix='out')
@wutils.fileOrArray('a')
@wutils.fslwrapper
def fast(imgs, out='fast', **kwargs):
    """Wrapper for the ``fast`` command.

    :arg imgs:      Input image(s)
    :arg out:       Output basename
    :arg n_classes: Number of tissue classes (corresponds to the ``--class``
                    command line option)
    """

    if isinstance(imgs, six.string_types):
        imgs = [imgs]

    asrt.assertIsNifti(*imgs)

    argmap = {
        'n_classes' : 'class',
    }

    cmd  = ['fast', '-v', '--out=%s' % out]
    cmd += wutils.applyArgStyle('--=', argmap=argmap, **kwargs)
    cmd += imgs

    return cmd
