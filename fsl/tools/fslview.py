#!/usr/bin/env python
#
# fslview.py - Image viewer.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""A 3D image viewer.

I'm using :mod:`wx.aui` instead of :mod:`wx.lib.agw.aui` because the
:class:`AuiNotebook` implementation in the latter is very unstable on OSX
Mavericks.
"""

import logging
log = logging.getLogger(__name__)

import sys
import os.path as op
import argparse

import fsl.fslview.fslviewframe   as fslviewframe
import fsl.fslview.displaycontext as displaycontext
import fsl.fslview.views          as views
import fsl.data.image             as fslimage

import props

    
def interface(parent, args, ctx):

    imageList, displayCtx = ctx
    
    frame = fslviewframe.FSLViewFrame(
        parent, imageList, displayCtx, args.default, args.glversion)
    
    if args.lightbox: frame.addViewPanel(views.LightBoxPanel)
    else:             frame.addViewPanel(views.OrthoPanel)
    
    return frame


def parseArgs(argv, namespace):
    """
    Parses the given command line arguments. Parameters:
    
      - argv:      command line arguments for fslview.
      - namespace: argparse.Namespace object to store the parsed arguments
    """

    # I hate argparse. By default, it does not support
    # the command line interface that I want to provide,
    # as demonstrated in this usage string:
    usageStr   = 'fslview [options] [image [displayOpts]] '\
                 '[image [displayOpts]] ...'
    epilogStr  = 'Each display option will be applied to the '\
                 'image which is listed before that option.'
    descStr    = 'Image viewer'

    # So I'm using two argument parsers - the
    # mainParser parses application options
    mainParser = argparse.ArgumentParser('fslview',
                                         usage=usageStr,
                                         description=descStr,
                                         epilog=epilogStr,
                                         add_help=False)

    # Application options
    mainParser.add_argument('-h', '--help',      action='store_true')
    mainParser.add_argument('-d', '--default',   action='store_true',
                            help='Default layout')
    mainParser.add_argument('-l', '--lightbox',  action='store_true',
                            help='Lightbox view')
    mainParser.add_argument('-g', '--glversion',
                            metavar=('MAJOR', 'MINOR'), type=int, nargs=2,
                            help='Desired (major, minor) OpenGL version')
    mainParser.add_argument('-o', '--voxelloc', metavar=('X', 'Y', 'Z'),
                            type=int, nargs=3,
                            help='Location to show (voxel coordinates of '
                                 'first image)')
    mainParser.add_argument('-r', '--worldloc', metavar=('X', 'Y', 'Z'),
                            type=float, nargs=3,
                            help='Location to show (world coordinates, '
                                 'takes precedence over --voxelloc)') 
    
    # And the imgParser parses image display options
    # for a single image - below we're going to
    # manually step through the list of arguments,
    # and pass each block of arguments to the imgParser
    # one at a time
    imgParser = argparse.ArgumentParser(add_help=False) 

    # Image display options
    imgOpts = imgParser.add_argument_group('Image display options')
    imgOpts.add_argument('image', help='image file')

    # We don't expose all of the ImageDisplay properties
    imgProps = ['alpha',
                'displayRange',
                'clipLow',
                'clipHigh',
                'worldResolution',
                'voxelResolution',
                'transform',
                'interpolation',
                'imageType',
                'cmap',
                'name',
                'volume']

    # do not use any of the short argument symboles
    # used either by fsl.py, or the mainParser above.
    props.addParserArguments(displaycontext.ImageDisplay,
                             imgOpts,
                             cliProps=imgProps,
                             exclude='lvhdwgor')

    # Parse the application options
    namespace, argv = mainParser.parse_known_args(argv, namespace)

    # If the user asked for help, print some help and exit 
    if namespace.help:
        
        mainParser.print_help()

        # Did I mention that I hate argparse?  Why
        # can't we customise the help text?
        imgHelp = imgParser.format_help()
        print imgHelp[imgHelp.index('Image display options'):]
        sys.exit(0)

    # Otherwise we parse the image options.
    # Figure out where the image files are
    # in the argument list.
    # 
    # NOTE This approach means that we cannot
    # support any image display options which
    # accept file names as arguments.
    imageIdxs = [i for i in range(len(argv)) if op.isfile(argv[i])]
    imageIdxs.append(len(argv))

    # Then parse each block of display options one by one
    namespace.images = []
    for i in range(len(imageIdxs) - 1):

        imgArgv      = argv[imageIdxs[i]:imageIdxs[i + 1]]
        imgNamespace = imgParser.parse_args(imgArgv)

        # We just add a list of argparse.Namespace
        # objects, one for each image, to the
        # parent Namespace object.
        namespace.images.append(imgNamespace)

    return namespace


def handleArgs(args):
    """
    Loads and configures any images which were specified on the command line.
    """
    
    images = []
    
    for i in range(len(args.images)):

        image = fslimage.Image(args.images[i].image)
        images.append(image)
        
    imageList  = fslimage.ImageList(images)
    displayCtx = displaycontext.DisplayContext(imageList)

    # per-image display arguments
    for i in range(len(imageList)):
        props.applyArguments(image.getAttribute('display'), args.images[i])

    # voxel/world location
    if len(imageList) > 0:
        if args.worldloc:
            loc = args.worldloc
        elif args.voxelloc:
            loc = imageList[0].voxToWorld([args.voxelloc])[0]
            
        else:
            loc = [imageList.bounds.xlo + 0.5 * imageList.bounds.xlen,
                   imageList.bounds.ylo + 0.5 * imageList.bounds.ylen,
                   imageList.bounds.zlo + 0.5 * imageList.bounds.zlen]

        displayCtx.location.xyz = loc

    return imageList, displayCtx
    

FSL_TOOLNAME  = 'FSLView'
FSL_INTERFACE = interface
FSL_CONTEXT   = handleArgs
FSL_PARSEARGS = parseArgs
