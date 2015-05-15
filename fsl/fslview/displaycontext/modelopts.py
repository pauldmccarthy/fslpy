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
    outline = props.Boolean(default=True)


    def __init__(self, *args, **kwargs):
        
        fsldisplay.DisplayOpts.__init__(self, *args, **kwargs)
        
        colour      = np.random.random(4)
        colour[3]   = 1.0
        self.colour = colour
