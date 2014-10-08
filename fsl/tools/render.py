#!/usr/bin/env python
#
# render.py - Generate screenshots of images.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os
import sys
import subprocess

import logging
log = logging.getLogger(__name__)

import argparse

import numpy            as np
import matplotlib.image as mplimg

import fslview_parseargs
import props

if  sys.platform.startswith('linux'): _LD_LIBRARY_PATH = 'LD_LIBRARY_PATH'
elif sys.platform == 'darwin':        _LD_LIBRARY_PATH = 'DYLD_LIBRARY_PATH'


def saveRender(canvases, filename):

    bitmaps  = map(lambda c: c.getBitmap(), canvases)
    combined = np.hstack(bitmaps)
    print combined.shape
    
    mplimg.imsave(filename, combined)


def run(args, context):

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

    width, height = args.size
    
    canvases = []

    if args.lightbox:
        c = lightboxcanvas.OSMesaLightBoxCanvas(
            imageList,
            zax=args.zax,
            width=width,
            height=height,
            bgColour=args.background)

        props.applyArguments(c, args)
        canvases.append(c)
        
    else:
        hides = [args.hidex, args.hidey, args.hidez]
        zooms = [args.xzoom, args.yzoom, args.zzoom]

        
        count  = sum([not h for h in hides])
        cwidth = width / count

        for i, (hide, zoom) in enumerate(zip(hides, zooms)):
            if hide: continue
            
            c = slicecanvas.OSMesaSliceCanvas(
                imageList,
                zax=i,
                width=cwidth,
                height=height,
                bgColour=args.background)
            if zoom is not None: c.zoom = zoom
            canvases.append(c)

    for c in canvases:
        
        c.showCursor = not args.hideCursor
        if   c.zax == 0: c.pos.xyz = displayCtx.location.yzx
        elif c.zax == 1: c.pos.xyz = displayCtx.location.xzy
        elif c.zax == 2: c.pos.xyz = displayCtx.location.xyz

        c.draw()

    if args.outfile is not None:
        saveRender(canvases, args.outfile)

    
def parseArgs(argv):
    """
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
