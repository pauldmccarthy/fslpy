#!/usr/bin/env python
#
# layout.py - Utility functions for calculating canvas sizes and laying them
# out.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Utility functions for calculating canvas sizes and laying them out.


This module implements a simple layout manager, for laying out canvases and
associated orientation labels. It is used primarily by the :mod:`.render`
application, for off-screen rendering.

You can use the following classes to define a layout:

.. autosummary::
   :nosignatures:

   Bitmap
   Space
   HBox
   VBox


And the following functions to generate layouts and bitmaps:

.. autosummary::
   :nosignatures:

   buildOrthoLayout
   buildCanvasBox
   padBitmap
   layoutToBitmap


A few functions are also provided for calculating the display size, in pixels,
of one or more canvases which are displaying a defined coordinate system. The
canvas sizes are calculated so that their aspect ratio, relative to the
respective horizontal/vertical display axes, are maintained, and that the
canvases are sized proportionally with respect to each other. These functions
are used both by :mod:`.render`, and also by the :class:`.OrthoPanel` and
:class:`.LightBoxPanel`, for calculating canvas sizes when they are displayed
in :mod:`~.tools.fsleyes`. The following size calculation functions are
available:

.. autosummary::
   :nosignatures:

   calcSizes
   calcGridSizes
   calcHorizontalSizes
   calcVerticalSizes
   calcPixWidth
   calcPixHeight
"""


import logging

import numpy as np


log = logging.getLogger(__name__)


class Bitmap(object):
    """A class which encapsulates a RGBA bitmap, assumed to be a
    ``numpy.uint8`` array of shape :math:`height \\times width \\times 4`).

    .. warning:: Note the unusual array shape - height is the first axis,
                 and width the second!

    
    A ``Bitmap`` instance has the following attributes:

      - ``bitmap``: The bitmap data
      - ``width``:  Bitmap width in pixels
      - ``height``: Bitmap height in pixels
    """

    def __init__(self, bitmap):
        """Create a ``Bitmap``.

        :arg bitmap: :mod:`numpy` array containing the bitmap data.
        """
        self.bitmap = bitmap
        self.width  = bitmap.shape[1]
        self.height = bitmap.shape[0]

        
class Space(object):
    """A class which represents empty space of a specific width/height.

    
    A ``Space`` instance has the following attributes:

      - ``width``:  Width in pixels.
      - ``height``: Height in pixels.
    """

    def __init__(self, width, height):
        """Creat a ``Space``.

        :arg width:  Width in pixels.

        :arg height: Height in pixels.
        """
        self.width  = width
        self.height = height

        
class HBox(object):
    """A class which contains items to be laid out horizontally.

    After creation, new items should be added via the :meth:`append` method.

    A ``HBox`` instance has the following attributes:

      - ``width``:  Total width in pixels.
      - ``height``: Total height in pixels.
      - ``items``:  List of items in this ``HBox``.
    """

    
    def __init__(self, items=None):
        """Create a ``HBox``.

        :arg items: List of items contained in this ``HBox``.
        """
        self.width  = 0
        self.height = 0
        self.items  = []
        if items is not None: map(self.append, items)

        
    def append(self, item):
        """Append a new item to this ``HBox``. """
        self.items.append(item)
        self.width = self.width + item.width
        if item.height > self.height:
            self.height = item.height

            
class VBox(object):
    """A class which contains items to be laid out vertically.

    After creation, new items can be added via the :meth:`append` method.

    A ``VBox`` instance has the following attributes:

      - ``width``:  Total width in pixels.
      - ``height``: Total height in pixels.
      - ``items``:  List of items in this ``VBox``.    
    """
    
    def __init__(self, items=None):
        """Create a ``VBox``.

        :arg items: List of items contained in this ``VBox``.
        """ 
        self.width  = 0
        self.height = 0
        self.items  = []
        if items is not None: map(self.append, items)

        
    def append(self, item):
        """Append a new item to this ``VBox``. """
        self.items.append(item)
        self.height = self.height + item.height
        if item.width > self.width:
            self.width = item.width


def padBitmap(bitmap, width, height, vert, bgColour):
    """Pads the given bitmap with zeros along the secondary axis (specified
    with the ``vert`` parameter), so that it fits in the given
    ``width``/``height``.

    
    :arg bitmap:   A ``numpy.array`` of size :math:`x \\times y \\times 4`
                   containing a RGBA bitmap.
    
    :arg width:    Desired width in pixels.
    
    :arg height:   Desired height in pixels.
    
    :arg vert:     If ``vert`` is ``True``, the bitmap is padded 
                   horizontally to fit ``width``. Otherwise, the 
                   bitmap is padded vertically to fit ``height``.

    :arg bgColour: Background colour to use for padding. Must be
                   a ``(r, g, b, a)`` tuple with each channel in
                   the range ``[0 - 255]``.
    """
    
    iheight = bitmap.shape[0]
    iwidth  = bitmap.shape[1]
    
    if vert:
        if iwidth < width:
            lpad   = np.floor((width - iwidth) / 2.0)
            rpad   = np.ceil( (width - iwidth) / 2.0)
            lpad   = np.zeros((iheight, lpad, 4), dtype=np.uint8)
            rpad   = np.zeros((iheight, rpad, 4), dtype=np.uint8)
            lpad[:] = bgColour
            rpad[:] = bgColour
            bitmap = np.hstack((lpad, bitmap, rpad))
    else:
        if iheight < height:
            tpad   = np.floor((height - iheight) / 2.0)
            bpad   = np.ceil(( height - iheight) / 2.0)
            tpad   = np.zeros((tpad, iwidth, 4), dtype=np.uint8)
            bpad   = np.zeros((bpad, iwidth, 4), dtype=np.uint8)
            tpad[:] = bgColour
            bpad[:] = bgColour 
            bitmap = np.vstack((tpad, bitmap, bpad))

    return bitmap


def layoutToBitmap(layout, bgColour):
    """Recursively turns the given ``layout`` object into a bitmap.

    :arg layout:   A :class:`Bitmap`, :class:`Space`, :class:`HBox` or 
                   :class:`VBox` instance.

    :arg bgColour: Background colour used to fill in empty space. Must be
                   a ``(r, g, b, a)`` tuple with channel values in the range
                   ``[0, 255]``. Defaults to transparent.

    :returns:      a ``numpy.uint8`` array of size
                   :math:`height \\times width \\times 4`.
    """

    if bgColour is None: bgColour = [0, 0, 0, 0]
    bgColour = np.array(bgColour, dtype=np.uint8)

    # Space is easy 
    if isinstance(layout, Space):
        space = np.zeros((layout.height, layout.width, 4), dtype=np.uint8)
        space[:] = bgColour
        return space

    # Bitmap is easy
    elif isinstance(layout, Bitmap):
        return np.array(layout.bitmap, dtype=np.uint8)

    # Boxes require a bit of work
    if   isinstance(layout, HBox): vert = False
    elif isinstance(layout, VBox): vert = True

    # Recursively bitmapify the children of the box
    itemBmps = map(lambda i: layoutToBitmap(i, bgColour), layout.items)

    # Pad each of the bitmaps so they are all the same
    # size along the secondary axis (which is width
    # if the layout is a VBox, and height if the layout
    # is a HBox).
    width    = layout.width
    height   = layout.height 
    itemBmps = map(lambda bmp: padBitmap(bmp, width, height, vert, bgColour),
                   itemBmps)

    if vert: return np.vstack(itemBmps)
    else:    return np.hstack(itemBmps)


def buildCanvasBox(canvasBmp, labelBmps, showLabels, labelSize):
    """Builds a layout containing the given canvas bitmap, and orientation
    labels (if ``showLabels`` is ``True``).

    
    :arg canvasBmp:  A ``numpy.uint8`` array containing a bitmap.
    
    :arg labelBmps:  Only used if ``showLabels`` is ``True``. ``numpy.uint8``
                     arrays containing label bitmaps. Must be a
                     dictionary of ``{side : numpy.uint8}`` mappings,
                     and must have keys ``top``, ``bottom``, ``left`` and
                     ``right``.
    
    :arg showLabels: If ``True``, the orientation labels provided in
                     ``labelBmps`` are added to the layout.
    
    :arg labelSize:  Label sizes - the ``left``/``right`` label widths,
                     and ``top``/``bottom`` label heights are padded to this
                     size using ``Space`` objects.

    :returns:        A :class:`Bitmap`  or :class:`VBox` instance.
    """

    if not showLabels: return Bitmap(canvasBmp)

    row1Box = HBox([Space(labelSize, labelSize),
                    Bitmap(labelBmps['top']),
                    Space(labelSize, labelSize)])

    row2Box = HBox([Bitmap(labelBmps['left']),
                    Bitmap(canvasBmp),
                    Bitmap(labelBmps['right'])])

    row3Box = HBox([Space(labelSize, labelSize),
                    Bitmap(labelBmps['bottom']),
                    Space(labelSize, labelSize)])

    return VBox((row1Box, row2Box, row3Box))


def buildOrthoLayout(canvasBmps,
                     labelBmps,
                     layout,
                     showLabels,
                     labelSize):
    """Builds a layout containing the given canvas bitmaps, label bitmaps, and
    colour bar bitmap.

    
    :arg canvasBmps: A list of ``numpy.uint8`` arrays containing the canvas
                     bitmaps to be laid out.

    :arg layout:     One of ``'horizontal'``, ``'vertical'``, or ``'grid'``.

    See the :func:`buildCanvasBox` for details on the other parameters.

    
    :returns: A :class:`HBox` or :class:`VBox` describing the layout.
    """

    if labelBmps is None:
        labelBmps  = [None] * len(canvasBmps)
        showLabels = False

    canvasBoxes = map(lambda cbmp, lbmps: buildCanvasBox(cbmp,
                                                         lbmps,
                                                         showLabels,
                                                         labelSize),
                      canvasBmps,
                      labelBmps)

    if   layout == 'horizontal': canvasBox = HBox(canvasBoxes)
    elif layout == 'vertical':   canvasBox = VBox(canvasBoxes)
    elif layout == 'grid':
        row1Box   = HBox([canvasBoxes[0], canvasBoxes[1]])
        row2Box   = HBox([canvasBoxes[2], Space(canvasBoxes[1].width,
                                                canvasBoxes[2].height)])
        canvasBox = VBox((row1Box, row2Box))

    return canvasBox


def calcSizes(layout, canvasaxes, bounds, width, height):
    """Convenience function which, based upon whether the `layout` argument
    is ``'horizontal'``, ``'vertical'``, or ``'grid'``,  respectively calls
    one of:
    
      - :func:`calcHorizontalSizes`
      - :func:`calcVerticalSizes`
      - :func:`calcGridSizes`

    :arg layout:    String specifying the layout type.
    
    :arg canvsaxes: A list of tuples, one for each canvas to be laid out.
                    Each tuple contains two values, ``(i, j)``, where ``i``
                    is an index, into ``bounds``, specifying the canvas
                    width, and ``j`` is an index into ``bounds``, specifying
                    the canvas height, in the display coordinate system.
    
    :arg bounds:    A list of three values specifying the size of the display
                    space.
    
    :arg width:     Maximum width in pixels.
    
    :arg height:    Maximum height in pixels.

    :returns:       A list of ``(width, height)`` tuples, one for each canvas,
                    each specifying the canvas width and height in pixels.
    """
    
    layout = layout.lower()
    func   = None

    if   layout == 'horizontal': func = calcHorizontalSizes
    elif layout == 'vertical':   func = calcVerticalSizes
    elif layout == 'grid':       func = calcGridSizes

    # a bad value for layout
    # will result in an error
    sizes = func(canvasaxes, bounds, width, height)

    log.debug('For space ({}, {}) and {} layout, pixel '
              'sizes for canvases {} ({}) are: {}'.format(
                  width, height, layout, canvasaxes, bounds, sizes))

    return sizes

        
def calcGridSizes(canvasaxes, bounds, width, height):
    """Calculates the size of three canvases so that they are laid
    out in a grid, i.e.:

       0   1

       2


    .. note:: If less than three canvases are specified, they are passed to
              the :func:`calcHorizontalLayout` function.

    See :func:`calcSizes` for details on the arguments.
    """

    if len(canvasaxes) < 3:
        return calcHorizontalSizes(canvasaxes, bounds, width, height)

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


def calcVerticalSizes(canvasaxes, bounds, width, height):
    """Calculates the size of up to three canvases so they are laid out
    vertically.

    See :func:`calcSizes` for details on the arguments.
    """
    return _calcFlatSizes(canvasaxes, bounds, width, height, True)


def calcHorizontalSizes(canvasaxes, bounds, width, height):
    """Calculates the size of up to three canvases so they are laid out
    horizontally.

    See :func:`calcSizes` for details on the arguments.
    """ 
    return _calcFlatSizes(canvasaxes, bounds, width, height, False)

        
def _calcFlatSizes(canvasaxes, bounds, width, height, vert=True):
    """Used by :func:`calcVerticalSizes` and :func:`calcHorizontalSizes`.
    
    Calculates the width and height, in pixels, of each canvas.

    :arg vert: If ``True`` the sizes are calculated for a vertical layout;
               otherwise they are calculated for a horizontal layout.

    See :func:`calcSizes` for details on the other arguments.

    :returns:  A list of ``(width, height)`` tuples, one for each canvas,
               each specifying the canvas width and height in pixels. 
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

        if ttlWidth  == 0: cw = 0
        else:              cw = width  * (canvasWidths[ i] / ttlWidth)

        if ttlHeight == 0: ch = 0
        else:              ch = height * (canvasHeights[i] / ttlHeight)

        sizes.append((cw, ch))

    return sizes


def calcPixWidth(wldWidth, wldHeight, pixHeight):
    """Given the dimensions of a space to be displayed, and the available
    height in pixels, calculates the required pixel width.

    :arg wldWidth:   Width of the display coordinate system

    :arg wldHeight:  Height of the display coordinate system

    :arg pixHeight:  Available height in pixels.

    :returns:        The required width in pixels.
    """
    return _adjustPixelSize(wldWidth,
                            wldHeight,
                            pixHeight * (2 ** 32),
                            pixHeight)[0]


def calcPixHeight(wldWidth, wldHeight, pixWidth):
    """Given the dimensions of a space to be displayed, and the available
    width in pixels, calculates the required pixel height.

    :arg wldWidth:   Width of the display coordinate system

    :arg wldHeight:  Height of the display coordinate system

    :arg pixWidth:   Available width in pixels.

    :returns:        The required height in pixels. 
    """ 
    return _adjustPixelSize(wldWidth,
                            wldHeight,
                            pixWidth,
                            pixWidth * (2 ** 32))[1]



def _adjustPixelSize(wldWidth, wldHeight, pixWidth, pixHeight):
    """Used by :func:`calcPixelWidth` and :func:`calcPixelHeight`.

    Potentially reduces the given pixel width/height such that the
    display space aspect ratio is maintained.
    """

    if any((pixWidth  == 0,
            pixHeight == 0,
            wldWidth  == 0,
            wldHeight == 0)):
        return 0, 0

    pixRatio = float(pixWidth) / pixHeight
    wldRatio = float(wldWidth) / wldHeight

    if   pixRatio > wldRatio:
        pixWidth  = wldWidth  * (pixHeight / wldHeight)
            
    elif pixRatio < wldRatio:
        pixHeight = wldHeight * (pixWidth  / wldWidth)

    return pixWidth, pixHeight
