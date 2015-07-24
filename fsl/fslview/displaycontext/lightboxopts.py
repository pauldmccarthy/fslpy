#!/usr/bin/env python
#
# lightboxopts.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import copy

import sceneopts

import fsl.fslview.gl.lightboxcanvas as lightboxcanvas


class LightBoxOpts(sceneopts.SceneOpts):
    nrows          = copy.copy(lightboxcanvas.LightBoxCanvas.nrows)
    ncols          = copy.copy(lightboxcanvas.LightBoxCanvas.ncols)
    topRow         = copy.copy(lightboxcanvas.LightBoxCanvas.topRow)
    sliceSpacing   = copy.copy(lightboxcanvas.LightBoxCanvas.sliceSpacing)
    zrange         = copy.copy(lightboxcanvas.LightBoxCanvas.zrange)
    zax            = copy.copy(lightboxcanvas.LightBoxCanvas.zax)
    showGridLines  = copy.copy(lightboxcanvas.LightBoxCanvas.showGridLines)
    highlightSlice = copy.copy(lightboxcanvas.LightBoxCanvas.highlightSlice)     
