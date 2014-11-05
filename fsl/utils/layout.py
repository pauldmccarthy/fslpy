#!/usr/bin/env python
#
# layout.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

        
def calcGridLayout(canvasaxes, bounds, width, height):
    """Fixes the size of each canvas so that aspect ratio is
    preserved, and the canvases are scaled relative to each other.
    """

    if len(canvasaxes) < 3:
        return calcHorizontalLayout(canvasaxes, bounds, width, height)

    canvasWidths  = [bounds.getLen(c[0]) for c in canvasaxes]
    canvasHeights = [bounds.getLen(c[1]) for c in canvasaxes]
    
    ttlWidth      = float(canvasWidths[ 0] + canvasWidths[ 1])
    ttlHeight     = float(canvasHeights[0] + canvasHeights[2])

    sizes = []

    for i in range(len(canvasaxes)):

        cw = width  * (canvasWidths[ i] / ttlWidth)
        ch = height * (canvasHeights[i] / ttlHeight) 

        acw, ach = _adjustPixelSize(canvasWidths[ i],
                                    canvasHeights[i],
                                    cw,
                                    ch)

        if (float(cw) / ch) > (float(acw) / ach): cw, ch = cw, ach
        else:                                     cw, ch = acw, ch
        
        sizes.append((cw, ch))

    return sizes

def calcVerticalLayout(canvasaxes, bounds, width, height):
    return _calcFlatLayout(canvasaxes, bounds, width, height, True)

def calcHorizontalLayout(canvasaxes, bounds, width, height):
    return _calcFlatLayout(canvasaxes, bounds, width, height, False)

        
def _calcFlatLayout(canvasaxes, bounds, width, height, vert=True):
    """Calculates sizes for each displayed canvas such that the aspect
    ratio is maintained across them when laid out vertically
    (``vert=True``) or horizontally (``vert=False``).
    """

    # Get the canvas dimensions in world space
    canvasWidths  = [bounds.getLen(c[0]) for c in canvasaxes]
    canvasHeights = [bounds.getLen(c[1]) for c in canvasaxes]

    maxWidth  = float(max(canvasWidths))
    maxHeight = float(max(canvasHeights))
    ttlWidth  = float(sum(canvasWidths))
    ttlHeight = float(sum(canvasHeights))

    if vert: ttlWidth  = maxWidth
    else:    ttlHeight = maxHeight

    sizes = []
    for i in range(len(canvasaxes)):

        cw = width  * (canvasWidths[ i] / ttlWidth)
        ch = height * (canvasHeights[i] / ttlHeight)

        acw, ach = _adjustPixelSize(canvasWidths[ i],
                                    canvasHeights[i],
                                    cw,
                                    ch)

        if vert: ch, cw = ach, width
        else:    cw, ch = acw, height

        sizes.append((cw, ch))

    return sizes


def _adjustPixelSize(wldWidth, wldHeight, pixWidth, pixHeight):
    """Adjusts the pixel width/height for the given canvas such that
    the world space aspect ratio is maintained.
    """        

    pixRatio = float(pixWidth) / pixHeight
    wldRatio = float(wldWidth) / wldHeight

    if   pixRatio > wldRatio:
        pixWidth  = wldWidth  * (pixHeight / wldHeight)
            
    elif pixRatio < wldRatio:
        pixHeight = wldHeight * (pixWidth  / wldWidth)

    return pixWidth, pixHeight
