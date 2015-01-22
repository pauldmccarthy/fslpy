#!/usr/bin/env python
#
# tensoropts.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import props

import fsl.data.strings as strings
import display          as fsldisplay

class TensorOpts(fsldisplay.DisplayOpts):

    displayMode = props.Choice(
        ('line', 'rgb'),
        labels=[strings.choices['TensorOpts.displayType.line'],
                strings.choices['TensorOpts.displayType.rgb']])


    xColour = props.Colour(default=(1.0, 0.0, 0.0))

    
    yColour = props.Colour(default=(0.0, 1.0, 0.0))

    
    zColour = props.Colour(default=(0.0, 0.0, 1.0))


    suppressX = props.Boolean(default=False)

    
    suppressY = props.Boolean(default=False)

    
    suppressZ = props.Boolean(default=False)

    
    def __init__(self, image, display, imageList, displayCtx, parent=None):
        fsldisplay.DisplayOpts.__init__(self,
                                        display,
                                        imageList,
                                        displayCtx,
                                        parent) 
