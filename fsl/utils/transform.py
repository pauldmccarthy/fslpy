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
from   fsl.transform        import *          # noqa


deprecated.warn('fsl.utils.transform',
                vin='2.2.0',
                rin='3.0.0',
                msg='Use the fsl.transform module instead')
