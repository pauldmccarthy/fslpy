#!/usr/bin/env python
#
# globject.py - Mapping between fsl.data.image types and
# OpenGL representations.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""
GL Objects must have the following methods:
  - setAxes(self, xax, yax)
  - destroy(self)
  - draw(self, zpos)
"""

import logging
log = logging.getLogger(__name__)


import fsl.fslview.gl.glimage as glimage

def createGLObject(imageType, image, display):

    if   imageType == 'volume':
        return glimage.GLImage(image, display)
        pass
    elif imageType == 'circle':
        pass
    elif imageType == 'tensor':
        pass 
