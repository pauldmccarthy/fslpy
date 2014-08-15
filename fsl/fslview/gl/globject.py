#!/usr/bin/env python
#
# globject.py - Mapping between fsl.data.image types and
# OpenGL representations.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""
GL Objects must have the following methods:
  - __init__(self, image, display)
  - init(   self, xax, yax)
  - ready(self)
  - setAxes(self, xax, yax)
  - destroy(self)
  - draw(self, zpos)
"""

import logging
log = logging.getLogger(__name__)


import fsl.fslview.gl.glimage as glimage

def createGLObject(image, display):

    if   display.imageType == 'volume':
        return glimage.GLImage(image, display)
    elif display.imageType == 'circle':
        pass
    elif display.imageType == 'tensor':
        pass 
