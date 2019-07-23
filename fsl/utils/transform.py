#!/usr/bin/env python
#
# transforms.py - Deprecated
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The ``fsl.utils.transform`` module is deprecated - use the
:mod:`fsl.transform` module instead.
"""


import fsl.utils.deprecated as     deprecated
from   fsl.transform.affine import *                     # noqa
from   fsl.transform.flirt  import (flirtMatrixToSform,  # noqa
                                    sformToFlirtMatrix)


deprecated.warn('fsl.utils.transform',
                vin='2.4.0',
                rin='3.0.0',
                msg='Use the fsl.transform module instead')
