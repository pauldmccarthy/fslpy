#!/usr/bin/env python
#
# render.py - Generate screenshots of images using OpenGL.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module implements an application which provides off-screen rendering
capability for scenes which can otherwise be displayed via fslview.

See:
  - :mod:`fsl.tools.fslview`
  - :mod:`fsl.tools.fslview_parseargs`
"""


import os
import sys
import subprocess

import logging
log = logging.getLogger(__name__)

import argparse

import matplotlib.image as mplimg

import props
import fslview_parseargs
import fsl.utils.layout          as fsllayout
import fsl.utils.colourbarbitmap as cbarbitmap
import fsl.utils.textbitmap      as textbitmap
import fsl.fslview.strings       as strings 
import fsl.data.image            as fslimage


if   sys.platform.startswith('linux'): _LD_LIBRARY_PATH = 'LD_LIBRARY_PATH'
elif sys.platform         == 'darwin': _LD_LIBRARY_PATH = 'DYLD_LIBRARY_PATH'


CBAR_SIZE   = 75
LABEL_SIZE  = 20


def buildLabelBitmaps(imageList,
                      displayCtx,
                      canvasAxes, 
                      canvasBmps,
                      bgColour,
                      alpha):
    
    # Default colour is white - if the orientation labels
    # cannot be determined, the foreground colour will be
    # changed to red
    fgColour = 'white'

    image   = imageList[displayCtx.selectedImage]
    display = image.getAttribute('display')

    # The image is being displayed as it is stored on
    # disk - the image.getOrientation method calculates
    # and returns labels for each voxelwise axis.
    if display.transform in ('pixdim', 'id'):
        xorient = image.getVoxelOrientation(0)
        yorient = image.getVoxelOrientation(1)
        zorient = image.getVoxelOrientation(2)

    # The image is being displayed in 'real world' space -
    # the definition of this space may be present in the
    # image meta data
    else:
        xorient = image.getWorldOrientation(0)
        yorient = image.getWorldOrientation(1)
        zorient = image.getWorldOrientation(2)

    if fslimage.ORIENT_UNKNOWN in [xorient, yorient, zorient]:
        fgColour = 'red'

    xlo = strings.imageAxisLowShortLabels[ xorient]
    ylo = strings.imageAxisLowShortLabels[ yorient]
    zlo = strings.imageAxisLowShortLabels[ zorient]
    xhi = strings.imageAxisHighShortLabels[xorient]
    yhi = strings.imageAxisHighShortLabels[yorient]
    zhi = strings.imageAxisHighShortLabels[zorient]

    loLabels = [xlo, ylo, zlo]
    hiLabels = [xhi, yhi, zhi]

    labelBmps = []

    for (xax, yax), canvasBmp in zip(canvasAxes, canvasBmps):

        width        = canvasBmp.shape[1]
        height       = canvasBmp.shape[0]

        allLabels    = {}
        labelKeys    = ['left', 'right', 'top', 'bottom']
        labelTexts   = [loLabels[xax], hiLabels[xax],
                        loLabels[yax], hiLabels[yax]]
        labelWidths  = [LABEL_SIZE, LABEL_SIZE, width,      width]
        labelHeights = [height,     height,     LABEL_SIZE, LABEL_SIZE]


        for key, text, width, height in zip(labelKeys,
                                            labelTexts,
                                            labelWidths,
                                            labelHeights):

            allLabels[key] = textbitmap.textBitmap(
                text=text,
                width=width,
                height=height,
                fontSize=12,
                fgColour=fgColour,
                bgColour=map(lambda c: c / 255.0, bgColour),
                alpha=alpha)

        labelBmps.append(allLabels)
            
    return labelBmps

def buildColourBarBitmap(imageList,
                         displayCtx,
                         width,
                         height,
                         cbarLocation,
                         cbarLabelSide,
                         bgColour):
    
    display = imageList[displayCtx.selectedImage].getAttribute('display')
    
    if   cbarLocation in ('top', 'bottom'): orient = 'horizontal'
    elif cbarLocation in ('left', 'right'): orient = 'vertical'
    
    if   cbarLabelSide == 'top-left':
        if orient == 'horizontal': labelSide = 'top'
        else:                      labelSide = 'left'
    elif cbarLabelSide == 'bottom-right':
        if orient == 'horizontal': labelSide = 'bottom'
        else:                      labelSide = 'right'            
    
    cbarBmp = cbarbitmap.colourBarBitmap(
        display.cmap,
        display.displayRange.xlo,
        display.displayRange.xhi,
        width,
        height,
        display.name,
        orient,
        labelSide,
        bgColour=map(lambda c: c / 255.0, bgColour))
    
    return cbarBmp

 
def buildColourBarLayout(canvasLayout,
                         cbarBmp,
                         cbarLocation,
                         cbarLabelSide):
    """Given a layout object containing the rendered canvas bitmaps,
    creates a new layout which incorporates the given colour bar bitmap.
    """

    cbarBmp = fsllayout.Bitmap(cbarBmp)

    if   cbarLabelSide == 'top-left':     items = [cbarBmp, canvasLayout]
    elif cbarLabelSide == 'bottom-right': items = [canvasLayout, cbarBmp]
        
    if   cbarLocation in ('top', 'bottom'): return fsllayout.VBox(items)
    elif cbarLocation in ('left', 'right'): return fsllayout.HBox(items)


def adjustSizeForColourBar(width, height, showColourBar, colourBarLocation):
    """Calculates the widths and heights of the image display space, and the
    colour bar if it is enabled.

    Returns two tuples - the first tuple contains the (width, height) of the
    available canvas space, and the second contains the (width, height) of
    the colour bar.
    """

    if showColourBar:

        cbarWidth = CBAR_SIZE
        if colourBarLocation in ('top', 'bottom'):
            height     = height - cbarWidth
            cbarHeight = cbarWidth
            cbarWidth  = width
        else:
            width      = width  - cbarWidth
            cbarHeight = height
    else:
        cbarWidth  = 0
        cbarHeight = 0

    return (width, height), (cbarWidth, cbarHeight)


def calculateOrthoCanvasSizes(
        imageList,
        displayCtx,
        width,
        height,
        canvasAxes,
        showLabels,
        layout):

    bounds   = displayCtx.bounds
    axisLens = [bounds.xlen, bounds.ylen, bounds.zlen]

    # Grid layout only makes sense if we're
    # displaying all three canvases
    if layout == 'grid' and len(canvasAxes) <= 2:
        raise ValueError('Grid layout only supports 3 canvases')

    # If we're displaying orientation labels,
    # reduce the available width and height
    # by a fixed amount
    if showLabels:
        if layout == 'horizontal':
            width  -= 2 * LABEL_SIZE * len(canvasAxes)
            height -= 2 * LABEL_SIZE
        elif layout == 'vertical':
            width  -= 2 * LABEL_SIZE
            height -= 2 * LABEL_SIZE * len(canvasAxes)
        elif layout == 'grid':
            width  -= 4 * LABEL_SIZE
            height -= 4 * LABEL_SIZE

    # Distribute the height across canvas heights
    return fsllayout.calcSizes(layout,
                               canvasAxes,
                               axisLens,
                               width,
                               height)


def run(args, context):
    """Creates and renders an OpenGL scene, and saves it to a file, according
    to the specified command line arguments.
    """

    # If this process is not configured for off-screen
    # rendering using osmesa, start a new process
    env = os.environ.copy()

    if env.get('FSL_OSMESA_PATH', None) is None:
        
        log.error('The FSL_OSMESA_PATH environment variable is not set - '
                  'I need to know where the OSMESA libraries are. Set this '
                  'variable and rerun render.')
        sys.exit(1)
    
    if env.get('PYOPENGL_PLATFORM', None) != 'osmesa':

        # Tell PyOpenGL that it should use
        # osmesa for off-screen rendering
        env['PYOPENGL_PLATFORM'] = 'osmesa'
        env[_LD_LIBRARY_PATH]    = env['FSL_OSMESA_PATH']

        log.warning('Restarting render.py with '
                    'off-screen rendering configured...')

        subprocess.call(sys.argv, env=env)
        sys.exit(0)

    import fsl.fslview.gl                      as fslgl
    import fsl.fslview.gl.osmesaslicecanvas    as slicecanvas
    import fsl.fslview.gl.osmesalightboxcanvas as lightboxcanvas

    fslgl.getOSMesaContext()
    fslgl.bootstrap((1, 4))

    imageList, displayCtx = context

    # Calculate canvas and colour bar sizes
    # so that the entire scene will fit in
    # the width/height specified by the user
    width, height = args.size
    (width, height), (cbarWidth, cbarHeight) = \
        adjustSizeForColourBar(width,
                               height,
                               args.showColourBar,
                               args.colourBarLocation)
    
    canvases = []

    # Lightbox view -> only one canvas
    if args.lightbox:
        c = lightboxcanvas.OSMesaLightBoxCanvas(
            imageList,
            zax=args.zax,
            width=width,
            height=height,
            bgColour=args.background)

        props.applyArguments(c, args)
        canvases.append(c)

    # Ortho view -> up to three canvases
    else:
 
        # Build a list containing the horizontal 
        # and vertical axes for each canvas
        canvasAxes = []
        zooms      = []
        centres    = []
        if not args.hidex:
            canvasAxes.append((1, 2))
            zooms     .append(args.xzoom)
            centres   .append(args.xcentre)
        if not args.hidey:
            canvasAxes.append((0, 2))
            zooms     .append(args.yzoom)
            centres   .append(args.ycentre)
        if not args.hidez:
            canvasAxes.append((0, 1))
            zooms     .append(args.zzoom)
            centres   .append(args.zcentre)

        # Grid only makes sense if
        # we're displaying 3 canvases
        if args.layout == 'grid' and len(canvasAxes) <= 2:
            args.layout = 'horizontal'

        if args.layout == 'grid':
            canvasAxes = [canvasAxes[1], canvasAxes[0], canvasAxes[2]]
        
        sizes = calculateOrthoCanvasSizes(imageList,
                                          displayCtx,
                                          width,
                                          height,
                                          canvasAxes,
                                          not args.hideLabels,
                                          args.layout)

        for ((width, height), (xax, yax), zoom, centre) in zip(sizes,
                                                               canvasAxes,
                                                               zooms,
                                                               centres):

            zax = 3 - xax - yax

            if centre is None:
                centre = (displayCtx.location[xax], displayCtx.location[yax])

            c = slicecanvas.OSMesaSliceCanvas(
                imageList,
                displayCtx,
                zax=zax,
                width=int(width),
                height=int(height),
                bgColour=args.background)
            
            if zoom is not None: c.zoom = zoom
            c.centreDisplayAt(*centre)
            canvases.append(c)

    # Configure each of the canvases (with those
    # properties that are common to both ortho and
    # lightbox canvases) and render them one by one
    for i, c in enumerate(canvases):
        
        c.showCursor = not args.hideCursor
        if   c.zax == 0: c.pos.xyz = displayCtx.location.yzx
        elif c.zax == 1: c.pos.xyz = displayCtx.location.xzy
        elif c.zax == 2: c.pos.xyz = displayCtx.location.xyz

        c.draw()

        canvases[i] = c.getBitmap()

    # Disable labels for now
    labelBmps = None
    if not args.hideLabels:
        labelBmps = buildLabelBitmaps(imageList,
                                      displayCtx,
                                      canvasAxes,
                                      canvases,
                                      args.background[:3],
                                      args.background[ 3])

    # layout
    if args.lightbox: layout = fsllayout.Bitmap(canvases[0])
    else:             layout = fsllayout.buildOrthoLayout(canvases,
                                                          labelBmps,
                                                          args.layout,
                                                          not args.hideLabels,
                                                          LABEL_SIZE)

    # Render a colour bar if required
    if args.showColourBar:
        cbarBmp = buildColourBarBitmap(imageList,
                                       displayCtx,
                                       cbarWidth,
                                       cbarHeight,
                                       args.colourBarLocation,
                                       args.colourBarLabelSide,
                                       args.background)
        layout  = buildColourBarLayout(layout,
                                       cbarBmp,
                                       args.colourBarLocation,
                                       args.colourBarLabelSide)

 
    if args.outfile is not None:
        bitmap = fsllayout.layoutToBitmap(layout, args.background)
        mplimg.imsave(args.outfile, bitmap)

    
def parseArgs(argv):
    """Creates an argument parser which accepts options for off-screen
    rendering.
    
    Uses the :mod:`fsl.tools.fslview_parseargs` module to peform the actual
    parsing.
    """

    mainParser = argparse.ArgumentParser(add_help=False)

    mainParser.add_argument('-of', '--outfile',  metavar='FILE',
                            help='Output image file name')
    mainParser.add_argument('-sz', '--size', type=int, nargs=2,
                            metavar=('W', 'H'),
                            help='Size in pixels (width, height)',
                            default=(800, 600))
    mainParser.add_argument('-bg', '--background', type=int, nargs=4,
                            metavar=('R', 'G', 'B', 'A'),
                            help='Background colour', 
                            default=(0, 0, 0, 255)) 
    
    return fslview_parseargs.parseArgs(mainParser,
                                       argv,
                                       'render',
                                       'Scene renderer')
 

FSL_TOOLNAME  = 'Render'
FSL_EXECUTE   = run
FSL_CONTEXT   = fslview_parseargs.handleImageArgs
FSL_PARSEARGS = parseArgs
