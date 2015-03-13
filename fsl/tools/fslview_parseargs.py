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

import sys
import os.path as op
import argparse

import props

import fsl.utils.typedict         as td
import fsl.data.image             as fslimage
import fsl.data.imageio           as iio
import fsl.utils.transform        as transform 
import fsl.fslview.displaycontext as displaycontext


# Names of all of the property which are 
# customisable via command line arguments.
_OPTIONS_ = td.TypeDict({
    'OrthoPanel'    : ['xzoom',
                       'yzoom',
                       'zzoom',
                       'layout',
                       'showXCanvas',
                       'showYCanvas',
                       'showZCanvas'],
    'LightBoxPanel' : ['sliceSpacing',
                       'ncols',
                       'nrows',
                       'zrange',
                       'showGridLines',
                       'highlightSlice',
                       'zax'],
    'Display'       : ['name',
                       'interpolation',
                       'resolution',
                       'transform',
                       'imageType',
                       'volume',
                       'alpha',
                       'brightness',
                       'contrast'],
    'VolumeOpts'    : ['displayRange',
                       'clipLow',
                       'clipHigh',
                       'cmap'],
    'MaskOpts'      : ['colour',
                       'invert',
                       'threshold'],
    'VectorOpts'    : ['displayMode',
                       'xColour',
                       'yColour',
                       'zColour',
                       'suppressX',
                       'suppressY',
                       'suppressZ',
                       'modulate'],
})

# Short/long arguments for all of those options
# 
# We can't use -w or -v, as they are used by the
# top level argument parser (in fsl/__init__.py).
#
# There cannot be any collisions between the scene
# options. 
#
# There can't be any collisions between the 
# Display options and the *Opts options.
_ARGUMENTS_ = td.TypeDict({
    'OrthoPanel.xzoom'       : ('xz', 'xzoom'),
    'OrthoPanel.yzoom'       : ('yz', 'yzoom'),
    'OrthoPanel.zzoom'       : ('zz', 'zzoom'),
    'OrthoPanel.layout'      : ('lo', 'layout'),
    'OrthoPanel.showXCanvas' : ('xh', 'hidex'),
    'OrthoPanel.showYCanvas' : ('yh', 'hidey'),
    'OrthoPanel.showZCanvas' : ('zh', 'hidez'),
    'OrthoPanel.showLabels'  : ('lh', 'hideLabels'),

    'LightBoxPanel.sliceSpacing'   : ('ss', 'sliceSpacing'),
    'LightBoxPanel.ncols'          : ('nc', 'ncols'),
    'LightBoxPanel.nrows'          : ('nr', 'nrows'),
    'LightBoxPanel.zrange'         : ('zr', 'zrange'),
    'LightBoxPanel.showGridLines'  : ('sg', 'showGridLines'),
    'LightBoxPanel.highlightSlice' : ('hs', 'highlightSlice'),
    'LightBoxPanel.zax'            : ('zx', 'zaxis'),

    'Display.name'          : ('n',  'name'),
    'Display.interpolation' : ('in', 'interp'),
    'Display.resolution'    : ('r',  'resolution'),
    'Display.transform'     : ('tf', 'transform'),
    'Display.imageType'     : ('it', 'imageType'),
    'Display.volume'        : ('vl', 'volume'),
    'Display.alpha'         : ('a',  'alpha'),
    'Display.brightness'    : ('b',  'brightness'),
    'Display.contrast'      : ('c',  'contrast'),

    'VolumeOpts.displayRange' : ('dr', 'displayRange'),
    'VolumeOpts.clipLow'      : ('cl', 'clipLow'),
    'VolumeOpts.clipHigh'     : ('ch', 'clipHigh'),
    'VolumeOpts.cmap'         : ('cm', 'cmap'),

    'MaskOpts.colour'    : ('c', 'colour'),
    'MaskOpts.invert'    : ('i', 'invert'),
    'MaskOpts.threshold' : ('t', 'threshold'),

    'VectorOpts.displayMode' : ('d',  'displayMode'),
    'VectorOpts.xColour'     : ('xc', 'xColour'),
    'VectorOpts.yColour'     : ('yc', 'yColour'),
    'VectorOpts.zColour'     : ('zc', 'zColour'),
    'VectorOpts.suppressX'   : ('xs', 'suppressX'),
    'VectorOpts.suppressY'   : ('ys', 'suppressY'),
    'VectorOpts.suppressX'   : ('zs', 'suppressZ'),
    'VectorOpts.modulate'    : ('m',  'modulate'),
})

# Help text for all of the options
_HELP_ = td.TypeDict({
    'OrthoPanel.xzoom'       : 'X canvas zoom',
    'OrthoPanel.yzoom'       : 'Y canvas zoom',
    'OrthoPanel.zzoom'       : 'Z canvas zoom',
    'OrthoPanel.layout'      : 'Canvas layout',
    'OrthoPanel.showXCanvas' : 'Hide the X canvas',
    'OrthoPanel.showYCanvas' : 'Hide the Y canvas',
    'OrthoPanel.showZCanvas' : 'Hide the Z canvas',
    'OrthoPanel.showLabels'  : 'Hide orientation labels',

    'LightBoxPanel.sliceSpacing'   : 'Slice spacing',
    'LightBoxPanel.ncols'          : 'Number of columns',
    'LightBoxPanel.nrows'          : 'Number of rows',
    'LightBoxPanel.zrange'         : 'Slice range',
    'LightBoxPanel.showGridLines'  : 'Show grid lines',
    'LightBoxPanel.highlightSlice' : 'Highlight current slice',
    'LightBoxPanel.zax'            : 'Z axis',

    'Display.name'          : 'Image name',
    'Display.interpolation' : 'Interpolation',
    'Display.resolution'    : 'Resolution',
    'Display.transform'     : 'Transformation',
    'Display.imageType'     : 'Image type',
    'Display.volume'        : 'Volume',
    'Display.alpha'         : 'Opacity',
    'Display.brightness'    : 'Brightness',
    'Display.contrast'      : 'Contrast',

    'VolumeOpts.displayRange' : 'Display range',
    'VolumeOpts.clipLow'      : 'Low clipping',
    'VolumeOpts.clipHigh'     : 'High clipping',
    'VolumeOpts.cmap'         : 'Colour map',

    'MaskOpts.colour'    : 'Colour',
    'MaskOpts.invert'    : 'Invert',
    'MaskOpts.threshold' : 'Threshold',

    'VectorOpts.displayMode' : 'Display mode',
    'VectorOpts.xColour'     : 'X colour',
    'VectorOpts.yColour'     : 'Y colour',
    'VectorOpts.zColour'     : 'Z colour',
    'VectorOpts.suppressX'   : 'Suppress X magnitude',
    'VectorOpts.suppressY'   : 'Suppress Y magnitude',
    'VectorOpts.suppressX'   : 'Suppress Z magnitude',
    'VectorOpts.modulate'    : 'Modulate vector colours',
})

# Transform functions for properties where the
# value passed in on the command line needs to
# be manipulated before the property value is
# set
_TRANSFORMS_ = td.TypeDict({
    'OrthoPanel.showXCanvas' : lambda b: not b,
    'OrthoPanel.showYCanvas' : lambda b: not b,
    'OrthoPanel.showZCanvas' : lambda b: not b,
    'OrthoPanel.showLabels'  : lambda b: not b,
    'VectorOpts.modulate'    : lambda f: None,
})


def _configMainParser(mainParser):

    # We're assuming that the fsl tool (e.g. render.py or fslview.py)
    # has not added/used up any of these short or long arguments
    mainParser.add_argument('-h',  '--help',    action='store_true',
                            help='Display this help and exit')

    # Options defining the overall scene
    sceneParser = mainParser.add_argument_group('Scene options')

    sceneParser.add_argument('-s', '--scene', choices=('ortho', 'lightbox'),
                             help='Scene to show. If not provided, the '
                             'previous scene layout is restored.')
    
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


def _configOrthoParser(orthoParser):
    pass


def _configLightBoxParser(orthoParser):
    pass 


def _configImageParser(imgParser):

    imgOpts = ['alpha',
               'name',
               'interpolation',
               'resolution',
               'transform',
               'imageType',
               'volume']
    imgArgs = ['a', 'n',  'int',
               'vr', 'tf', 'it', 'vol']

    # As above - labels and help text are embedded in the
    # ImageDisplay class
    props.addParserArguments(displaycontext.Display,
                             imgParser,
                             cliProps=imgOpts,
                             shortArgs=dict(zip(imgOpts, imgArgs))) 


def parseArgs(mainParser, argv, name, desc, toolOptsDesc='[options]'):
    """
    Parses the given command line arguments. Parameters:

      - mainParser: 
      - argv:         command line arguments for fslview.
      - name:
      - desc:
      - toolOptsDesc:
    """

    # I hate argparse. By default, it does not support
    # the command line interface that I want to provide,
    # as demonstrated in this usage string. 
    usageStr   = '{} {} [imagefile [displayOpts]] '\
                 '[imagefile [displayOpts]] ...'.format(
                     name,
                     toolOptsDesc)
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
    #
    # This approach currently means that
    # we cannot have any other options
    # which accept file names as arguments.
    # A future change will be to allow
    # this, but to add an explciit check
    # here, for each of the options which
    # require a file argument.
    imageIdxs = [i for i in range(len(argv)) if op.isfile(argv[i])]
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
    namespace.images = []
    for i in range(len(imageIdxs) - 1):

        imgArgv = argv[imageIdxs[i]:imageIdxs[i + 1]]

        imgFile = op.expanduser(imgArgv[0])
        imgArgv = imgArgv[1:]

        # an -i with something that is
        # not a file following it
        if not op.isfile(iio.addExt(imgFile, True)):
            print_help()
            sys.argv(1)            

        imgNamespace       = imgParser.parse_args(imgArgv)
        imgNamespace.image = imgFile

        # We just add a list of argparse.Namespace
        # objects, one for each image, to the
        # parent Namespace object.
        namespace.images.append(imgNamespace)

    return namespace


def handleImageArgs(args, **kwargs):
    """Loads and configures any images which were specified on the
    command line.

    The ``a`` and ``kwa`` arguments are passed through to the
    :func:`fsl.data.imageio.loadImages` function.
    """

    paths      = [i.image for i in args.images]
    images     = iio.loadImages(paths, **kwargs)
        
    imageList  = fslimage.ImageList(images)
    displayCtx = displaycontext.DisplayContext(imageList)

    # per-image display arguments
    for i in range(len(imageList)):
        props.applyArguments(displayCtx.getDisplayProperties(imageList[i]),
                             args.images[i])

    # voxel/world location
    if len(imageList) > 0:
        if args.worldloc:
            loc = args.worldloc
        elif args.voxelloc:
            display = displayCtx.getDisplayProperties(imageList[0])
            xform   = display.getTransform('voxel', 'display')
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
