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

import fslview

def run(args, context):

    env = os.environ.copy()

    # If this process is not configured for off-screen
    # rendering using osmesa, start a new process 
    if env.get('PYOPENGL_PLATFORM', None) != 'osmesa':

        # Tell PyOpenGL that it should use
        # osmesa for off-screen rendering
        env['PYOPENGL_PLATFORM'] = 'osmesa'

        # I need to figure out a better method
        # of linking to the mesa libraries
        env['DYLD_LIBRARY_PATH'] = '/Users/paulmc/mesa/build/Mesa-6.5.3/lib'

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
    else:

        canvas = slicecanvas.OSMesaSliceCanvas(
            imageList,
            zax=axis,
            glVersion=(1, 4),
            width=width,
            height=height)

    if   axis == 0: canvas.pos.xyz = displayCtx.location.yzx
    elif axis == 1: canvas.pos.xyz = displayCtx.location.xzy
    elif axis == 2: canvas.pos.xyz = displayCtx.location.xyz

    canvas.draw()

    if args.outfile is not None:
        canvas.saveToFile(args.outfile)

    
def parseArgs(argv, namespace):
    """
    """

    usageStr   = 'render [options] [image [displayOpts]] '\
                 '[image [displayOpts]] ...'
    epilogStr  = 'Each display option will be applied to the '\
                 'image which is listed before that option.'
    descStr    = 'Scene renderer'

    mainParser = argparse.ArgumentParser('render',
                                         usage=usageStr,
                                         description=descStr,
                                         epilog=epilogStr,
                                         add_help=False)

    mainParser.add_argument('-f', '--outfile',  metavar='FILE',
                            help='Output image file name')
    mainParser.add_argument('-h', '--help',     action='store_true')
    mainParser.add_argument('-o', '--voxelloc', metavar=('X', 'Y', 'Z'),
                            type=int, nargs=3,
                            help='Location to show (voxel coordinates of '
                                 'first image)')
    mainParser.add_argument('-r', '--worldloc', metavar=('X', 'Y', 'Z'),
                            type=float, nargs=3,
                            help='Location to show (world coordinates, '
                                 'takes precedence over --voxelloc)')
    
    mainParser.add_argument('-l', '--lightbox',  action='store_true',
                            help='Lightbox view')

    mainParser.add_argument('-a', '--axis', 
                            help='Display axis',
                            choices=('X', 'Y', 'Z'), default='X')

    mainParser.add_argument('-s', '--size', type=int, nargs=2,
                            metavar=('W', 'H'),
                            help='Size in pixels (width, height)',
                            default=(800, 600))

    # TODO
    # lightbox display options
    # ortho (slice canvas) display options
    # Show colour bar

    exclude = 'vwfhorlas'

    return fslview.parseArgs(argv, namespace, mainParser, exclude)
 

def handleArgs(args):
    return fslview.handleArgs(args)
    

FSL_TOOLNAME  = 'Render'
FSL_EXECUTE   = run
FSL_CONTEXT   = handleArgs
FSL_PARSEARGS = parseArgs
