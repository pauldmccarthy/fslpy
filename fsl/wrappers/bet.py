#!/usr/bin/env python
#
# bet.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import fsl.utils.assertions as asrt
import fsl.utils.run        as run
from . import wrapperutils  as wutils


@wutils.fileOrImage('input', 'output')
def bet(input, output, **kwargs):
    """Delete non-brain tissue from an image of the whole head.

    :arg input:         Required
    :arg output:        Required
    :arg mask:
    :arg robust:
    :arg fracintensity:
    :arg seg:

    Refer to the ``bet`` command-line help for details on all arguments.
    """

    asrt.assertIsNifti(input)

    argmap = {
        'mask'          : 'm',
        'robust'        : 'R',
        'fracintensity' : 'f',
        'seg'           : 'n',
    }

    valmap = {
        'm' : wutils.SHOW_IF_TRUE,
        'R' : wutils.SHOW_IF_TRUE,
        'n' : wutils.HIDE_IF_TRUE,
    }

    cmd  = ['bet', input, output]
    cmd += wutils.applyArgStyle('-', argmap, valmap, **kwargs)

    return run.runfsl(*cmd)
