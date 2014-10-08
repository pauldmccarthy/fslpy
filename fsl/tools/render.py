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

import numpy            as np
import matplotlib.image as mplimg

import props
import fslview_parseargs
import fsl.utils.colourbarbitmap as cbarbitmap

if  sys.platform.startswith('linux'): _LD_LIBRARY_PATH = 'LD_LIBRARY_PATH'
elif sys.platform == 'darwin':        _LD_LIBRARY_PATH = 'DYLD_LIBRARY_PATH'


def saveRender(args, canvases, cbarbmp):
    """Saves the scene to the file specified by `args.outfile`.
    
    :arg args:     The :mod:`argparse` namespace containing all the command
                   line arguments.
    
    :arg canvases: A list of all the canvases which have been rendered.
    
    :arg cbarbmp:  An rgba bitmap (W*H*4) containing a rendering of a colour
                   bar, if it was specified.
    """

    canvasbmps = map(lambda c: c.getBitmap(), canvases)
    bmp        = np.hstack(canvasbmps)

    if args.showColourBar:

        if   args.colourBarLocation == 'top':
            bmp = np.vstack((cbarbmp, bmp))
        elif args.colourBarLocation == 'bottom':
            bmp = np.vstack((bmp, cbarbmp))
        elif args.colourBarLocation == 'left':
            bmp = np.hstack((bmp, cbarbmp))
        elif args.colourBarLocation == 'right':
            bmp = np.hstack((cbarbmp, bmp))
    
    mplimg.imsave(args.outfile, bmp)


def calcSizes(args):
    """Calculates the widths and heights of the image display canvases, and the
    colour bar if it is enabled.

    Returns two tuples - the first tuple contains the (width, height) of one
    canvas, and the second contains the (width, height) of the colour bar.
    """

    width, height = args.size

    if args.showColourBar:

        cbarWidth = 75
        if args.colourBarLocation in ('top', 'bottom'):
            height     = height - cbarWidth
            cbarHeight = cbarWidth
            cbarWidth  = width
        else:
            width      = width  - cbarWidth
            cbarHeight = height
    else:
        cbarWidth  = 0
        cbarHeight = 0

    if not args.lightbox:
        
        hides = [args.hidex, args.hidey, args.hidez]
        count = sum([not h for h in hides])
        width = width / count

    return (width, height), (cbarWidth, cbarHeight)


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
    (width, height), (cbarWidth, cbarHeight) = calcSizes(args)
    
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
        hides = [args.hidex, args.hidey, args.hidez]
        zooms = [args.xzoom, args.yzoom, args.zzoom]

        for i, (hide, zoom) in enumerate(zip(hides, zooms)):
            if hide: continue
            
            c = slicecanvas.OSMesaSliceCanvas(
                imageList,
                zax=i,
                width=width,
                height=height,
                bgColour=args.background)
            if zoom is not None: c.zoom = zoom
            canvases.append(c)

    # Configure each of the canvases (with those
    # properties that are common to both ortho and
    # lightbox canvases) and render them one by one
    for c in canvases:
        
        c.showCursor = not args.hideCursor
        if   c.zax == 0: c.pos.xyz = displayCtx.location.yzx
        elif c.zax == 1: c.pos.xyz = displayCtx.location.xzy
        elif c.zax == 2: c.pos.xyz = displayCtx.location.xyz

        c.draw()

    # Render a colour bar if requested
    if args.showColourBar:
        display = imageList[-1].getAttribute('display')
        if   args.colourBarLocation in ('top', 'bottom'):
            orient = 'horizontal'
        elif args.colourBarLocation in ('left', 'right'):
            orient = 'vertical'
        
        if   args.colourBarLabelSide == 'top-left':
            if orient == 'horizontal': labelSide = 'top'
            else:                      labelSide = 'left'
        elif args.colourBarLabelSide == 'bottom-right':
            if orient == 'horizontal': labelSide = 'bottom'
            else:                      labelSide = 'right'            
        
        cbarbmp = cbarbitmap.colourBarBitmap(
            display.cmap,
            display.displayRange.xlo,
            display.displayRange.xhi,
            cbarWidth,
            cbarHeight,
            display.name,
            orient,
            labelSide,
            bgColour=map(lambda c: c / 255.0, args.background))
    else:
        cbarbmp = None

    if args.outfile is not None:
        saveRender(args, canvases, cbarbmp)

    
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
