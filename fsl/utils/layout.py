#!/usr/bin/env python
#
# layout.py - Utility functions for calculating canvas sizes.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Utility functions for calculating canvas sizes.

This module provides a few functions, for calculating the display size, in
pixels, of one or more canvases which are displaying a defined coordinate
system. The canvas sizes are calculated so that their aspect ratio, relative
to the respective horizontal/vertical display axes, are maintained, and that
the canvases are sized proportionally with respect to each other.

The following functions are available:

  - :func:`calcGridLayout`:       Calculates canvas sizes for laying out in a
                                  grid
  - :func:`calcHorizontalLayout`: Calculates canvas sizes for laying out
                                  horizontally.
  - :func:`calcVerticaLayout`:    Calculates canvas sizes for laying out
                                  verticall.

Each of these functions require the following parameters:

  - ``canvasaxes``: A sequence of 2-tuples, one for each canvas, with each
                    tuple specifying the indices of the coordinate system
                    axes which map to the horizontal and vertical canvas
                    axes.
 
  - ``bounds``:     A sequence of three floating point values, specifying the
                    length of each axis in the coordinate system being
                    displayed.

  - ``width``:      The total available width in which all of the canvases are
                    to be displayed.

  - ``height``:     The total available height in which all of the canvases are
                    to be displayed.

A convenience function :func:`calcLayout` is also available which, in addition
to the above parameters, accepts a string as its first parameter which must be
equal to one of ``horizontal``, ``vertical``, or ``grid``. It will then call
the appropriate layout-specific function.
"""

import logging
log = logging.getLogger(__name__)


def calcLayout(layout, canvasaxes, bounds, width, height):
    """Convenience function which, based upon whether the `layout` argument
    is `horizontal`, `vertical`, or `grid`,  respectively calls one of:
      - :func:`calcHorizontalLayout`
      - :func:`calcVerticalLayout`
      - :func:`calcGridLayout`
    """
    
    layout = layout.lower()
    func   = None

    if   layout == 'horizontal': func = calcHorizontalLayout
    elif layout == 'vertical':   func = calcVerticalLayout
    elif layout == 'grid':       func = calcGridLayout

    # a bad value for layout
    # will result in an error
    return func(canvasaxes, bounds, width, height)

        
def calcGridLayout(canvasaxes, bounds, width, height):
    """Calculates the size of three canvases so that they are laid
    out in a grid, i.e.:

       0   1

       2

    If less than three canvases are specified, they are passed to the
    :func:`calcHorizontalLayout` function.
    """

    if len(canvasaxes) < 3:
        return calcHorizontalLayout(canvasaxes, bounds, width, height)

    canvasWidths  = [bounds[c[0]] for c in canvasaxes]
    canvasHeights = [bounds[c[1]] for c in canvasaxes]
    
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
    """Calculates the size of up to three canvases so  they are laid out
    vertically.
    """
    return _calcFlatLayout(canvasaxes, bounds, width, height, True)


def calcHorizontalLayout(canvasaxes, bounds, width, height):
    """Calculates the size of up to three canvases so  they are laid out
    horizontally.
    """ 
    return _calcFlatLayout(canvasaxes, bounds, width, height, False)

        
def _calcFlatLayout(canvasaxes, bounds, width, height, vert=True):
    """Used by the :func:`calcVerticalLayout` and :func:`calcHorizontalLayout`
    functions to lay the canvases out vertically (``vert=True``) or
    horizontally (``vert=False``).
    """

    # Get the canvas dimensions in world space
    canvasWidths  = [bounds[c[0]] for c in canvasaxes]
    canvasHeights = [bounds[c[1]] for c in canvasaxes]

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
    """Potentially reduces the given pixel width/height such that the
    display space aspect ratio is maintained.
    """        

    pixRatio = float(pixWidth) / pixHeight
    wldRatio = float(wldWidth) / wldHeight

    if   pixRatio > wldRatio:
        pixWidth  = wldWidth  * (pixHeight / wldHeight)
            
    elif pixRatio < wldRatio:
        pixHeight = wldHeight * (pixWidth  / wldWidth)

    return pixWidth, pixHeight
