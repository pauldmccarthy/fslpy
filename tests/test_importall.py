#!/usr/bin/env python
#
# test_importall.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import pkgutil


def test_importall():
    import fsl         as fsl
    import fsl.data    as data
    import fsl.utils   as utils
    import fsl.scripts as scripts

    for _, module, _ in pkgutil.iter_modules(fsl.__path__, 'fsl.'):
        __import__(module) 
    for _, module, _ in pkgutil.iter_modules(data.__path__, 'fsl.data.'):
        __import__(module)
    for _, module, _ in pkgutil.iter_modules(utils.__path__, 'fsl.utils.'):
        __import__(module)
    for _, module, _ in pkgutil.iter_modules(scripts.__path__, 'fsl.scripts.'):
        __import__(module) 
