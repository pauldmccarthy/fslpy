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
import fsl.utils.transform        as transform 
import fsl.fslview.displaycontext as displaycontext


def _configMainParser(mainParser):

    # We're assuming that the fsl tool (e.g. render.py or fslview.py)
    # has not added/used up any of these short or long arguments
    mainParser.add_argument('-h',  '--help',    action='store_true',
                            help='Display this help and exit')

    mainParser.add_argument('-i', '--image', metavar='IMAGE',
                            help='Image file to display')

    # Options defining the overall scene
    sceneParser = mainParser.add_argument_group('Scene options')
 
    sceneParser.add_argument('-l', '--lightbox',  action='store_true',
                             help='Display lightbox view '
                             'instead of ortho view')
    sceneParser.add_argument('-v', '--voxelloc', metavar=('X', 'Y', 'Z'),
                             type=int, nargs=3,
                             help='Location to show (voxel coordinates of '
                             'first image)')
    sceneParser.add_argument('-w', '--worldloc', metavar=('X', 'Y', 'Z'),
                             type=float, nargs=3,
                             help='Location to show (world coordinates, '
                             'takes precedence over --voxelloc)')
    sceneParser.add_argument('-si', '--selectedImage', type=int,
                             help='Selected image (default: last)')
    sceneParser.add_argument('-hc', '--hideCursor', action='store_true',
                             help='Do not display the green cursor '
                             'highlighting the current location')


    # Separate parser groups for ortho/lightbox options
    orthoParser =  mainParser.add_argument_group('Ortho options')
    lbParser    =  mainParser.add_argument_group('Lightbox options')
    cbarParser  =  mainParser.add_argument_group('Colour bar options')

    # Ortho options
    orthoParser.add_argument('-xz', '--xzoom', type=float,
                             help='X axis zoom')
    orthoParser.add_argument('-yz', '--yzoom', type=float,
                             help='Y axis zoom')
    orthoParser.add_argument('-zz', '--zzoom', type=float,
                             help='Z axis zoom')
    orthoParser.add_argument('-xc', '--xcentre', metavar=('Y', 'Z'),
                             type=float, nargs=2,
                             help='X canvas display centre '
                                  '(world coordinates)') 
    orthoParser.add_argument('-yc', '--ycentre', metavar=('X', 'Z'),
                             type=float, nargs=2,
                             help='Y canvas display centre '
                                  '(world coordinates)')     
    orthoParser.add_argument('-zc', '--zcentre', metavar=('X', 'Y'),
                             type=float, nargs=2,
                             help='Z canvas display centre '
                                  '(world coordinates)') 
    orthoParser.add_argument('-xh', '--hidex', action='store_true',
                             help='Hide the X axis')
    orthoParser.add_argument('-yh', '--hidey', action='store_true',
                             help='Hide the Y axis')
    orthoParser.add_argument('-zh', '--hidez', action='store_true',
                             help='Hide the Z axis')
    orthoParser.add_argument('-lh', '--hideLabels', action='store_true',
                             help='Hide orientation labels')
    orthoParser.add_argument('-lo', '--layout', 
                             choices=('horizontal', 'vertical', 'grid'),
                             default='horizontal',
                             help='Canvas layout') 
    
    # Lightbox display options
    lbOpts = ['sliceSpacing',
              'ncols',
              'nrows',
              'zrange',
              'showGridLines',
              'zax']
    lbArgs = ['ss', 'nc', 'nr', 'zr', 'sg', 'ax']

    # Use the properties module to automatically generate
    # arguments - property labels and help strings are
    # embedded inside the LightBoxCanvas class.
    import fsl.fslview.gl.lightboxcanvas as lightboxcanvas
    props.addParserArguments(lightboxcanvas.LightBoxCanvas,
                             lbParser,
                             cliProps=lbOpts,
                             shortArgs=dict(zip(lbOpts, lbArgs)))

    # Colour bar
    cbarParser.add_argument('-bs', '--showColourBar', action='store_true',
                            help='Show colour bar')
    cbarParser.add_argument('-bl', '--colourBarLocation',
                            choices=('top', 'bottom', 'left', 'right'),
                            help='Colour bar location',
                            default='top')
    cbarParser.add_argument('-bt', '--colourBarLabelSide',
                            choices=('top-left', 'bottom-right'),
                            help='Colour bar label orientation',
                            default='top-left') 


def _configImageParser(imgParser):

    imgOpts = ['alpha',
               'clipLow',
               'clipHigh',
               'name',
               'displayRange',
               'interpolation',
               'resolution',
               'transform',
               'imageType',
               'cmap',
               'volume']
    imgArgs = ['a', 'cl', 'ch', 'n', 'dr', 'int',
               'vr', 'tf', 'it', 'cm', 'vol']

    # As above - labels and help text are embedded in the
    # ImageDisplay class
    props.addParserArguments(displaycontext.ImageDisplay,
                             imgParser,
                             cliProps=imgOpts,
                             shortArgs=dict(zip(imgOpts, imgArgs))) 


def parseArgs(mainParser, argv, name, desc):
    """
    Parses the given command line arguments. Parameters:

      - mainParser: 
      - argv:       command line arguments for fslview.
      - name:
      - desc:
    """

    # I hate argparse. By default, it does not support
    # the command line interface that I want to provide,
    # as demonstrated in this usage string. I also hate
    # the fact that I have to delimit image files with '-i':
    usageStr   = '{} [options] [-i image [displayOpts]] '\
                 '[-i image [displayOpts]] ...'.format(name)
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

    _configImageParser(imgParser.add_argument_group(
        'Image display options', imgOptDesc))

    # Figure out where the image files
    # are in the argument list.
    imageIdxs = [i for i in range(len(argv)) if argv[i] in ('-i', '--image')]
    imageIdxs.append(len(argv))

    # Separate the program arguments 
    # from the image display arguments
    progArgv = argv[:imageIdxs[0]]
    imgArgv  = argv[ imageIdxs[0]:]

    # Parse the application options with the mainParser
    namespace = mainParser.parse_args(progArgv)

    # If the user asked for help, print some help and exit
    def print_help():
        mainParser.print_help()

        # Did I mention that I hate argparse?  Why
        # can't we customise the help text?
        imgHelp = imgParser.format_help()
        print 
        print imgHelp[imgHelp.index('Image display options'):]
        sys.exit(0)

    if namespace.help:
        print_help()
        sys.exit(0)
 
    # Then parse each block of
    # display options one by one.
    # This will probably explode
    # if the user forgets to add
    # an image file name after '-i'
    namespace.images = []
    for i in range(len(imageIdxs) - 1):

        imgArgv = argv[imageIdxs[i] + 1:imageIdxs[i + 1]]

        # an '-i' with nothing following it
        if len(imgArgv) == 0:
            print_help()
            sys.argv(1)

        imgFile = op.expanduser(imgArgv[0])
        imgArgv = imgArgv[1:]

        # an -i with something that is
        # not a file following it
        if not op.isfile(imgFile):
            print_help()
            sys.argv(1)            

        imgNamespace       = imgParser.parse_args(imgArgv)
        imgNamespace.image = imgFile

        # We just add a list of argparse.Namespace
        # objects, one for each image, to the
        # parent Namespace object.
        namespace.images.append(imgNamespace)

    return namespace


def handleImageArgs(args):
    """Loads and configures any images which were specified on the
    command line.
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
            display = imageList[0].getAttribute('display')
            xform   = display.voxToDisplayMat
            loc     = transform.transform([[args.voxelloc]], xform)[0]
            
        else:
            loc = [displayCtx.bounds.xlo + 0.5 * displayCtx.bounds.xlen,
                   displayCtx.bounds.ylo + 0.5 * displayCtx.bounds.ylen,
                   displayCtx.bounds.zlo + 0.5 * displayCtx.bounds.zlen]

        displayCtx.location.xyz = loc

    if args.selectedImage is not None:
        if args.selectedImage < len(imageList):
            displayCtx.selectedImage = args.selectedImage
    else:
        if len(imageList) > 0:
            displayCtx.selectedImage = len(imageList) - 1

    return imageList, displayCtx
