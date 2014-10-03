#!/usr/bin/env python
#
# fslview_parseargs.py - Parsing FSLView command line arguments.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module encapsulates the logic for parsing command line arguments
which specify a scene to be displayed in FSLView.  This logic is shared
between fslview.py and render.py.
"""

import logging
log = logging.getLogger(__name__)

import sys
import os.path as op
import argparse

import props
import fsl.data.image             as fslimage
import fsl.fslview.displaycontext as displaycontext


def _configMainParser(mainParser):
    mainParser.add_argument('-h',  '--help',    action='store_true')

    mainParser.add_argument('-lb', '--lightbox',  action='store_true',
                            help='Display lightbox view '
                                 'instead of ortho view')
    mainParser.add_argument('-vl', '--voxelloc', metavar=('X', 'Y', 'Z'),
                            type=int, nargs=3,
                            help='Location to show (voxel coordinates of '
                                 'first image)')
    mainParser.add_argument('-wl', '--worldloc', metavar=('X', 'Y', 'Z'),
                            type=float, nargs=3,
                            help='Location to show (world coordinates, '
                                 'takes precedence over --voxelloc)')

    # show/hide cursor (common to both ortho and lightbox)
    mainParser.add_argument('-hc', '--hideCursor', action='store_true',
                            help='Do not display the green cursor '
                                 'highlighting the current location')

#    mainParser.add_argument('-z', '--zoom', type=float,
#                            help='Zoom (ortho view only)')

    # TODO colour bar
    
    # Lightbox display options
    lbOpts = ['sliceSpacing',
              'ncols',
              'nrows',
              'topRow',
              'zrange']
    lbArgs = ['ss', 'nc', 'nr', 'tr', 'zr']

    # Use the properties module to automatically generate
    # arguments - property labels and help strings are
    # embedded inside the LightBoxCanvas class.
    import fsl.fslview.gl.lightboxcanvas as lightboxcanvas
    props.addParserArguments(lightboxcanvas.LightBoxCanvas,
                             mainParser.add_argument_group('Lightbox options'),
                             cliProps=lbOpts,
                             shortArgs=dict(zip(lbOpts, lbArgs))) 


def _configImageParser(imgParser):

    # The image file name is a positional
    # argument which must come first
    imgParser.add_argument('image', help='image file')

    imgOpts = ['alpha',
               'clipLow',
               'clipHigh',
               'name',
               'displayRange',
               'interpolation',
               'worldResolution',
               'voxelResolution',
               'transform',
               'imageType',
               'cmap']
    imgArgs = ['a', 'cl', 'ch', 'n', 'dr', 'int', 'wr', 'vr', 'tf', 'it', 'cm']

    # As above - labels and help text are embedded in the
    # ImageDisplay class
    props.addParserArguments(displaycontext.ImageDisplay,
                             imgParser,
                             cliProps=imgOpts,
                             shortArgs=dict(zip(imgOpts, imgArgs))) 


def parseArgs(mainParser, argv, namespace, name, desc):
    """
    Parses the given command line arguments. Parameters:

      - mainParser: 
      - argv:       command line arguments for fslview.
      - namespace:  argparse.Namespace object to store the parsed arguments
      - name:
      - desc:
    """

    # I hate argparse. By default, it does not support
    # the command line interface that I want to provide,
    # as demonstrated in this usage string:
    usageStr   = '{} [options] [image [displayOpts]] '\
                 '[image [displayOpts]] ...'.format(name)
    imgOptDesc = 'Each display option will be applied to the '\
                 'image which is listed before that option.'

    # So I'm using two argument parsers - the
    # mainParser parses application options
    mainParser.usage       = usageStr
    mainParser.prog        = name
    mainParser.description = desc

    _configMainParser(mainParser)

    # And the imgParser parses image display options
    # for a single image - below we're going to
    # manually step through the list of arguments,
    # and pass each block of arguments to the imgParser
    # one at a time
    imgParser = argparse.ArgumentParser(add_help=False) 

    # Image display options
    _configImageParser(imgParser.add_argument_group(
        'Image display options', imgOptDesc))

    # Parse the application options with the mainParser
    namespace, argv = mainParser.parse_known_args(argv, namespace)

    # If the user asked for help, print some help and exit 
    if namespace.help:
        
        mainParser.print_help()

        # Did I mention that I hate argparse?  Why
        # can't we customise the help text?
        imgHelp = imgParser.format_help()
        print 
        print imgHelp[imgHelp.index('Image display options'):]
        sys.exit(0)

    # Otherwise we parse the image options.
    # Figure out where the image files are
    # in the argument list.
    # 
    # NOTE This approach means that we cannot
    # support any image display options which
    # accept file names as arguments.
    imageIdxs = [i for i in range(len(argv))
                 if op.isfile(op.expanduser(argv[i]))]
    imageIdxs.append(len(argv))

    # Then parse each block of display options one by one
    namespace.images = []
    for i in range(len(imageIdxs) - 1):

        imgArgv      = argv[imageIdxs[i]:imageIdxs[i + 1]]
        imgArgv[0]   = op.expanduser(imgArgv[0])
        imgNamespace = imgParser.parse_args(imgArgv)

        # We just add a list of argparse.Namespace
        # objects, one for each image, to the
        # parent Namespace object.
        namespace.images.append(imgNamespace)

    return namespace


def handleImageArgs(args):
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
        props.applyArguments(imageList[i].getAttribute('display'),
                             args.images[i])

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
