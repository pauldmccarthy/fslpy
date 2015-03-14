#!/usr/bin/env python
#
# fslview_parseargs.py - Parsing FSLView command line arguments.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module encapsulates the logic for parsing command line arguments
which specify a scene to be displayed in FSLView.  This logic is shared
between fslview.py and render.py.

The functions in this module make use of the command line generation
featuresd of the :mod:`props` package.

There are a lot of command line arguments made available to the user,
broadly split into the following groups:

 - *Main* arguments control the overall scene display, such as the
   display type (orthographic or lightbox), the displayed location,
   and whether to show a colour bar.

 - *Display* arguments control the display for a single image file,
   such as interpolation, colour map, etc.

The main entry points of this module are:

  - :func:`parseArgs`:

    Parses command line arguments, and returns an :class:`argparse.Namespace`
    object.

  - :func:`handleSceneArgs`:

    Configures :class:`~fsl.fslview.frame.FSLViewFrame` and
    :class:`~fsl.fslview.displaycontext.DisplayContext` instances according to
    the arguments contained in a given :class:`~argparse.Namespace` object.

  - :func:`handleImageArgs`:

    Loads and configures the display of any image files specified by a given
    :class:`~argparse.Namespace` object.
"""

import sys
import os.path as op
import argparse

import props

import fsl.utils.typedict         as td
import fsl.data.image             as fslimage
import fsl.data.imageio           as iio
import fsl.utils.transform        as transform

import fsl.fslview.displaycontext.displaycontext as displaycontext
import fsl.fslview.displaycontext.display        as display
import fsl.fslview.displaycontext.volumeopts     as volumeopts
import fsl.fslview.displaycontext.vectoropts     as vectoropts
import fsl.fslview.displaycontext.maskopts       as maskopts

import fsl.fslview.views.orthopanel    as orthopanel
import fsl.fslview.views.lightboxpanel as lightboxpanel


# Names of all of the property which are 
# customisable via command line arguments.
_OPTIONS_ = td.TypeDict({

    'Main'          : ['scene',
                       'voxelLoc',
                       'worldLoc',
                       'selectedImage',
                       'hideCursor'],
    'ColourBar'     : ['showColourBar',
                       'colourBarLocation',
                       'colourBarLabelSide'],

    # From here on, all of the keys are
    # the names of HasProperties classes,
    # and all of the values are the 
    # names of properties on them.
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

# Headings for each of the option groups
_GROUPNAMES_ = td.TypeDict({
    'OrthoPanel'    : 'Ortho display options',
    'LightBoxPanel' : 'LightBox display options',
    'Display'       : 'Image display options',
    
    'VolumeOpts'    : 'Volume options',
    'VectorOpts'    : 'Vector options',
    'MaskOpts'      : 'Mask options',

    'ColourBar'     : 'Colour bar options',
})

# Short/long arguments for all of those options
# 
# There cannot be any collisions between the main
# options, the scene options, and the colour bar
# options.
#
# There can't be any collisions between the 
# Display options and the *Opts options.
_ARGUMENTS_ = td.TypeDict({

    'Main.scene'         : ('s',  'scene'),
    'Main.voxelLoc'      : ('v',  'voxelloc'),
    'Main.worldLoc'      : ('w',  'worldloc'),
    'Main.selectedImage' : ('i',  'selectedImage'),
    'Main.hideCursor'    : ('hc', 'hideCursor'),
    
    'ColourBar.showColourBar'      : ('cb',  'showColourBar'),
    'ColourBar.colourBarLocation'  : ('cbl', 'colourBarLocation'),
    'ColourBar.colourBarLabelSide' : ('cbs', 'colourBarLabelSide'),
    
    'OrthoPanel.xzoom'       : ('xz', 'xzoom'),
    'OrthoPanel.yzoom'       : ('yz', 'yzoom'),
    'OrthoPanel.zzoom'       : ('zz', 'zzoom'),
    'OrthoPanel.layout'      : ('lo', 'layout'),
    'OrthoPanel.showXCanvas' : ('xh', 'hidex'),
    'OrthoPanel.showYCanvas' : ('yh', 'hidey'),
    'OrthoPanel.showZCanvas' : ('zh', 'hidez'),
    'OrthoPanel.showLabels'  : ('lh', 'hideLabels'),

    'OrthoPanel.xcentre'     : ('xc', 'xcentre'),
    'OrthoPanel.ycentre'     : ('yc', 'ycentre'),
    'OrthoPanel.zcentre'     : ('zc', 'zcentre'),

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

    'MaskOpts.colour'    : ('co', 'colour'),
    'MaskOpts.invert'    : ('i',  'invert'),
    'MaskOpts.threshold' : ('t',  'threshold'),

    'VectorOpts.displayMode' : ('d',  'displayMode'),
    'VectorOpts.xColour'     : ('xc', 'xColour'),
    'VectorOpts.yColour'     : ('yc', 'yColour'),
    'VectorOpts.zColour'     : ('zc', 'zColour'),
    'VectorOpts.suppressX'   : ('xs', 'suppressX'),
    'VectorOpts.suppressY'   : ('ys', 'suppressY'),
    'VectorOpts.suppressZ'   : ('zs', 'suppressZ'),
    'VectorOpts.modulate'    : ('m',  'modulate'),

})

# Help text for all of the options
_HELP_ = td.TypeDict({

    'Main.scene'         : 'Scene to show. If not provided, the '
                           'previous scene layout is restored.',
    'Main.voxelLoc'      : 'Location to show (voxel coordinates of '
                           'first image)',
    'Main.worldLoc'      : 'Location to show (world coordinates, '
                           'takes precedence over --voxelloc)',
    'Main.selectedImage' : 'Selected image (default: last)',
    'Main.hideCursor'    : 'Do not display the green cursor '
                           'highlighting the current location',
    
    'ColourBar.showColourBar'      : 'Show colour bar',
    'ColourBar.colourBarLocation'  : 'Colour bar location',
    'ColourBar.colourBarLabelSide' : 'Colour bar label orientation', 
    
    'OrthoPanel.xzoom'       : 'X canvas zoom',
    'OrthoPanel.yzoom'       : 'Y canvas zoom',
    'OrthoPanel.zzoom'       : 'Z canvas zoom',
    'OrthoPanel.layout'      : 'Canvas layout',
    'OrthoPanel.showXCanvas' : 'Hide the X canvas',
    'OrthoPanel.showYCanvas' : 'Hide the Y canvas',
    'OrthoPanel.showZCanvas' : 'Hide the Z canvas',
    'OrthoPanel.showLabels'  : 'Hide orientation labels',

    'OrthoPanel.xcentre'     : 'X canvas display centre (world coordinates)',
    'OrthoPanel.ycentre'     : 'Y canvas display centre (world coordinates)',
    'OrthoPanel.zcentre'     : 'Z canvas display centre (world coordinates)',

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
    'VectorOpts.suppressZ'   : 'Suppress Z magnitude',
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
    """Sets up an argument parser which handles options related
    to the scene. This function configures the following argument
    groups:
    
      - *Main*:          Top level optoins
      - *ColourBar*:     Colour bar related options
      - *OrthoPanel*:    Options related to setting up a orthographic display
      - *LightBoxPanel*: Options related to setting up a lightbox display
    """

    mainParser.add_argument('-h',  '--help',
                            action='store_true',
                            help='Display this help and exit')

    # Options defining the overall scene
    sceneParser = mainParser.add_argument_group('Scene options')

    mainArgs = {name: _ARGUMENTS_['Main', name] for name in _OPTIONS_['Main']}
    mainHelp = {name: _HELP_[     'Main', name] for name in _OPTIONS_['Main']}

    for name, (shortArg, longArg) in mainArgs.items():
        mainArgs[name] = ('-{}'.format(shortArg), '--{}'.format(longArg))

    sceneParser.add_argument(*mainArgs['scene'],
                             choices=('ortho', 'lightbox'),
                             help=mainHelp['scene'])
    sceneParser.add_argument(*mainArgs['voxelLoc'],
                             metavar=('X', 'Y', 'Z'),
                             type=int,
                             nargs=3,
                             help=mainHelp['voxelLoc'])
    sceneParser.add_argument(*mainArgs['worldLoc'],
                             metavar=('X', 'Y', 'Z'),
                             type=int,
                             nargs=3,
                             help=mainHelp['worldLoc'])
    sceneParser.add_argument(*mainArgs['selectedImage'],
                             type=int,
                             help=mainHelp['selectedImage'])
    sceneParser.add_argument(*mainArgs['hideCursor'],
                             action='store_true',
                             help=mainHelp['hideCursor'])

    # Separate parser groups for ortho/lightbox, and for colour bar options
    cbarParser  =  mainParser.add_argument_group(_GROUPNAMES_['ColourBar'])    
    orthoParser =  mainParser.add_argument_group(_GROUPNAMES_['OrthoPanel'])
    lbParser    =  mainParser.add_argument_group(_GROUPNAMES_['LightBoxPanel'])

    _configColourBarParser(cbarParser)
    _configOrthoParser(    orthoParser)
    _configLightBoxParser( lbParser)


def _configColourBarParser(cbarParser):
    """Adds options to the given argument parser which allow
    the user to specify colour bar properties.
    """
    
    cbarArgs = {name: _ARGUMENTS_['ColourBar', name]
                for name in _OPTIONS_['ColourBar']}
    cbarHelp = {name: _HELP_['ColourBar', name]
                for name in _OPTIONS_['ColourBar']}

    for name, (shortArg, longArg) in cbarArgs.items():
        cbarArgs[name] = ('-{}'.format(shortArg), '--{}'.format(longArg))
    
    # Colour bar
    cbarParser.add_argument(*cbarArgs['showColourBar'],
                            action='store_true',
                            help=cbarHelp['showColourBar'])
    cbarParser.add_argument(*cbarArgs['colourBarLocation'],
                            choices=('top', 'bottom', 'left', 'right'),
                            help=cbarHelp['colourBarLocation'],
                            default='top')
    cbarParser.add_argument(*cbarArgs['colourBarLabelSide'],
                            choices=('top-left', 'bottom-right'),
                            help=cbarHelp['colourBarLabelSide'],
                            default='top-left') 
   

def _configOrthoParser(orthoParser):
    """Adds options to the given parser allowing the user to
    configure an orthographic display.
    """

    OrthoPanel = orthopanel.OrthoPanel

    propNames = _OPTIONS_[OrthoPanel]

    shortArgs = {}
    longArgs  = {}
    helpTexts = {}

    for propName in propNames:

        shortArg, longArg = _ARGUMENTS_[OrthoPanel, propName]
        helpText          = _HELP_[     OrthoPanel, propName]

        shortArgs[propName] = shortArg
        longArgs[ propName] = longArg
        helpTexts[propName] = helpText

    props.addParserArguments(OrthoPanel,
                             orthoParser,
                             cliProps=propNames,
                             shortArgs=shortArgs,
                             longArgs=longArgs,
                             propHelp=helpTexts)
                             
    # Extra configuration options that are
    # not OrthoPanel properties, so can't
    # be automatically set up
    for opt, metavar in zip(['xcentre',  'ycentre',  'zcentre'],
                            [('Y', 'Z'), ('X', 'Z'), ('X', 'Y')]):
        
        shortArg, longArg = _ARGUMENTS_[OrthoPanel, opt]
        helpText          = _HELP_[     OrthoPanel, opt]

        shortArg =  '-{}'.format(shortArg)
        longArg  = '--{}'.format(longArg)

        orthoParser.add_argument(shortArg,
                                 longArg,
                                 metavar=metavar,
                                 type=float,
                                 nargs=2,
                                 help=helpText)


def _configLightBoxParser(lbParser):
    """Adds options to the given parser allowing the user to
    configure a lightbox display.
    """    
    LightBoxPanel = lightboxpanel.LightBoxPanel

    propNames = _OPTIONS_[LightBoxPanel]
    shortArgs = {}
    longArgs  = {}
    helpTexts = {}

    for propName in propNames:

        shortArg, longArg = _ARGUMENTS_[LightBoxPanel, propName]
        helpText          = _HELP_[     LightBoxPanel, propName]

        shortArgs[propName] = shortArg
        longArgs[ propName] = longArg
        helpTexts[propName] = helpText

    props.addParserArguments(LightBoxPanel,
                             lbParser,
                             cliProps=propNames,
                             shortArgs=shortArgs,
                             longArgs=longArgs,
                             propHelp=helpTexts)


def _configImageParser(imgParser):
    """Adds options to the given image allowing the user to
    configure the display of a single image.
    """

    Display    = display.Display
    VolumeOpts = volumeopts.VolumeOpts
    VectorOpts = vectoropts.VectorOpts
    MaskOpts   = maskopts  .MaskOpts
    
    dispDesc = 'Each display option will be applied to the '\
               'image which is listed before that option.'

    dispParser = imgParser.add_argument_group(_GROUPNAMES_[Display],
                                              dispDesc)
    volParser  = imgParser.add_argument_group(_GROUPNAMES_[VolumeOpts])
    vecParser  = imgParser.add_argument_group(_GROUPNAMES_[VectorOpts])
    maskParser = imgParser.add_argument_group(_GROUPNAMES_[MaskOpts])

    for target, parser in zip(
            [Display,    VolumeOpts, VectorOpts, MaskOpts],
            [dispParser, volParser,  vecParser,  maskParser]):

        propNames = _OPTIONS_[target]
        shortArgs = {}
        longArgs  = {}
        helpTexts = {}

        for propName in propNames:

            shortArg, longArg = _ARGUMENTS_[target, propName]
            helpText          = _HELP_[     target, propName]

            shortArgs[propName] = shortArg
            longArgs[ propName] = longArg
            helpTexts[propName] = helpText

        props.addParserArguments(target,
                                 parser,
                                 cliProps=propNames,
                                 shortArgs=shortArgs,
                                 longArgs=longArgs,
                                 propHelp=helpTexts)


def parseArgs(mainParser, argv, name, desc, toolOptsDesc='[options]'):
    """Parses the given command line arguments, returning an
    :class:`argparse.Namespace` object containing all the arguments.

      - mainParser:   A :class:`argparse.ArgumentParser` which should be
                      used as the top level parser.
    
      - argv:         The arguments as passed in on the command line.
    
      - name:         The name of the tool - this function might be called by
                      either the ``fslview`` tool or the ``render`` tool.
    
      - desc:         A description of the tool.
    
      - toolOptsDesc: A string describing the tool-specific options (those
                      options which are handled by the tool, not by this
                      module).
    """

    # I hate argparse. By default, it does not support
    # the command line interface that I want to provide,
    # as demonstrated in this usage string. 
    usageStr   = '{} {} [imagefile [displayOpts]] '\
                 '[imagefile [displayOpts]] ...'.format(
                     name,
                     toolOptsDesc)

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

    _configImageParser(imgParser)

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
    #
    # TODO Handle vector opts modulate option
    # 
    # TODO Could do a more rigorous test
    # here - check for supported image files 
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
        # can't we customise the help text? Here
        # we're skipping over the top section of
        # the image parser help text
        imgHelp   = imgParser.format_help()
        dispGroup = _GROUPNAMES_[display.Display]
        print 
        print imgHelp[imgHelp.index(dispGroup):]
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

        # an  with something that is
        # not a file following it
        if not op.isfile(iio.addExt(imgFile, True)):
            print_help()
            sys.exit(1)            

        imgNamespace       = imgParser.parse_args(imgArgv)
        imgNamespace.image = imgFile

        # We just add a list of argparse.Namespace
        # objects, one for each image, to the
        # parent Namespace object.
        namespace.images.append(imgNamespace)

    return namespace


def handleSceneArgs(args, frame, displayCtx):
    pass


def handleImageArgs(args, **kwargs):
    """Loads and configures any images which were specified on the
    command line.

    The ``kwargs`` arguments are passed through to the
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
