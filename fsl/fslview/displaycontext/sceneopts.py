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
        labels=[strings.choices['SceneOpts.colourBarLocation.top'],
                strings.choices['SceneOpts.colourBarLocation.bottom'],
                strings.choices['SceneOpts.colourBarLocation.left'],
                strings.choices['SceneOpts.colourBarLocation.right']])

    
    colourBarLabelSide = copy.copy(colourbarcanvas.ColourBarCanvas.labelSide)
