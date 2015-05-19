#!/usr/bin/env python
#
# modelopts.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import numpy as np

import props

import display as fsldisplay


class ModelOpts(fsldisplay.DisplayOpts):

    colour  = props.Colour()
    outline = props.Boolean(default=False)


    def __init__(self, *args, **kwargs):
        
        fsldisplay.DisplayOpts.__init__(self, *args, **kwargs)
        
        colour                  = np.random.random(3)
        colour[colour.argmax()] = 1
        colour[colour.argmin()] = 0
        
        np.random.shuffle(colour)

        self.colour = np.concatenate((colour, [1.0]))


    def getDisplayBounds(self):
        return self.overlay.getBounds()


    def getOldDisplayBounds(self):
        return self.overlay.getBounds()
