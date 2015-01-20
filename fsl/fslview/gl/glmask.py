#!/usr/bin/env python
#
# glmask.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)


class GLMask(object):
    """
    """
    
    def __init__(self, image, display):
        self.image   = image
        self.display = display


    def init(self, xax, yax):
        pass

    def ready(self):
        return True

    def setAxes(self, xax, yax):
        pass

    def destroy(self):
        pass

    def preDraw(self):
        pass

    def draw(self, zpos, xform=None):
        pass

    def postDraw(self):
        pass
