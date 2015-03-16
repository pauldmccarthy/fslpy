#!/usr/bin/env python
#
# sceneopts.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import copy

import props

import fsl.fslview.gl.colourbarcanvas as colourbarcanvas

import fsl.data.strings as strings

class SceneOpts(props.HasProperties):
    
    showCursor = props.Boolean(default=True)

    zoom = props.Percentage(minval=10, maxval=1000, default=100, clamped=True)

    showColourBar = props.Boolean(default=False)

    colourBarLocation  = props.Choice(
        ('top', 'bottom', 'left', 'right'),
        labels=[strings.choices['CanvasPanel.colourBarLocation.top'],
                strings.choices['CanvasPanel.colourBarLocation.bottom'],
                strings.choices['CanvasPanel.colourBarLocation.left'],
                strings.choices['CanvasPanel.colourBarLocation.right']])

    
    colourBarLabelSide = copy.copy(colourbarcanvas.ColourBarCanvas.labelSide)
