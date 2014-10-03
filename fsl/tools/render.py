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

import fslview_parseargs
import props

if  sys.platform.startswith('linux'): _LD_LIBRARY_PATH = 'LD_LIBRARY_PATH'
elif sys.platform == 'darwin':        _LD_LIBRARY_PATH = 'DYLD_LIBRARY_PATH'

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

    import fsl.fslview.gl.osmesaslicecanvas    as slicecanvas
    import fsl.fslview.gl.osmesalightboxcanvas as lightboxcanvas

    imageList, displayCtx = context

    axis = ['X', 'Y', 'Z'].index(args.axis)

    width, height = args.size

    if args.lightbox:
        canvas = lightboxcanvas.OSMesaLightBoxCanvas(
            imageList,
            zax=axis,
            glVersion=(1, 4),
            width=width,
            height=height)

        props.applyArguments(canvas, args)
    else:

        canvas = slicecanvas.OSMesaSliceCanvas(
            imageList,
            zax=axis,
            glVersion=(1, 4),
            width=width,
            height=height)

    canvas.showCursor = not args.hideCursor

    if   axis == 0: canvas.pos.xyz = displayCtx.location.yzx
    elif axis == 1: canvas.pos.xyz = displayCtx.location.xzy
    elif axis == 2: canvas.pos.xyz = displayCtx.location.xyz

    canvas.draw()

    if args.outfile is not None:
        canvas.saveToFile(args.outfile)

    
def parseArgs(argv, namespace):
    """
    """

    mainParser = argparse.ArgumentParser(add_help=False)

    mainParser.add_argument('-f', '--outfile',  metavar='FILE',
                            help='Output image file name')
    mainParser.add_argument('-a', '--axis', 
                            help='Display axis',
                            choices=('X', 'Y', 'Z'), default='X')
    mainParser.add_argument('-s', '--size', type=int, nargs=2,
                            metavar=('W', 'H'),
                            help='Size in pixels (width, height)',
                            default=(800, 600))

    return fslview_parseargs.parseArgs(mainParser,
                                       argv,
                                       namespace,
                                       'render',
                                       'Scene renderer')
 

FSL_TOOLNAME  = 'Render'
FSL_EXECUTE   = run
FSL_CONTEXT   = fslview_parseargs.handleImageArgs
FSL_PARSEARGS = parseArgs
