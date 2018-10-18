#!/usr/bin/env python
#
# extract_noise.py - Deprecated - replaced by fsl_ents.py
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module is deprecated - it has been replaced by :mod:`.fsl_ents`. """


import sys


if __name__ == '__main__':
    print('extract_noise is deprecated and will be removed in fslpy 2.0. '
          'Use fsl_ents instead.')
    from fsl.scripts.fsl_ents import main
    sys.exit(main())
