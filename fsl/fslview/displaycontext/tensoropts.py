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
        ('lines', 'rgb'),
        labels=[strings.choices['TensorOpts.displayType.lines'],
                strings.choices['TensorOpts.displayType.rgb']])


    colour = props.Colour()

    def __init__(self, image, display, imageList, displayCtx, parent=None):
        fsldisplay.DisplayOpts.__init__(self,
                                        display,
                                        imageList,
                                        displayCtx,
                                        parent) 
