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
import logging

import props

import fsl.utils.typedict  as td
import fsl.data.imageio    as iio
import fsl.data.image      as fslimage
import fsl.utils.transform as transform


# The colour maps module needs to be imported
# before the displaycontext.opts modules are
# imported, as some of their class definitions
# rely on the colourmaps being initialised
import fsl.fslview.colourmaps as colourmaps
colourmaps.initColourMaps()


import fsl.fslview.displaycontext.display      as fsldisplay
import fsl.fslview.displaycontext.volumeopts   as volumeopts
import fsl.fslview.displaycontext.vectoropts   as vectoropts
import fsl.fslview.displaycontext.maskopts     as maskopts

import fsl.fslview.displaycontext.sceneopts    as sceneopts
import fsl.fslview.displaycontext.orthoopts    as orthoopts
import fsl.fslview.displaycontext.lightboxopts as lightboxopts


log = logging.getLogger(__name__)


# Names of all of the property which are 
# customisable via command line arguments.
OPTIONS = td.TypeDict({

    'Main'          : ['scene',
                       'voxelLoc',
                       'worldLoc',
                       'selectedImage'],
    
    'SceneOpts'     : ['showCursor',
                       'showColourBar',
                       'colourBarLocation',
                       'colourBarLabelSide',
                       'twoStageRender'],

    # From here on, all of the keys are
    # the names of HasProperties classes,
    # and all of the values are the 
    # names of properties on them.
    'OrthoOpts'     : ['xzoom',
                       'yzoom',
                       'zzoom',
                       'showLabels',
                       'layout',
                       'showXCanvas',
                       'showYCanvas',
                       'showZCanvas'],
    'LightBoxOpts'  : ['sliceSpacing',
                       'ncols',
                       'nrows',
                       'zrange',
                       'showGridLines',
                       'highlightSlice',
                       'zax'],

    # The order in which properties are listed
    # here is the order in which they are applied
    # - so make sure transform is listed before
    # interpolation!
    'Display'       : ['name',
                       'transform',
                       'imageType',
                       'interpolation',
                       'resolution',
                       'volume',
                       'alpha',
                       'brightness',
                       'contrast'],
    'VolumeOpts'    : ['displayRange',
                       'clippingRange',
                       'invert',
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
                       'modulate',
                       'modThreshold'],
})

# Headings for each of the option groups
GROUPNAMES = td.TypeDict({
    'SceneOpts'    : 'Scene options',
    'OrthoOpts'    : 'Ortho display options',
    'LightBoxOpts' : 'LightBox display options',
    
    'Display'      : 'Image display options',
    'VolumeOpts'   : 'Volume options',
    'VectorOpts'   : 'Vector options',
    'MaskOpts'     : 'Mask options',

})

# Short/long arguments for all of those options
# 
# There cannot be any collisions between the main
# options, the scene options, and the colour bar
# options.
#
# There can't be any collisions between the 
# Display options and the *Opts options.
ARGUMENTS = td.TypeDict({

    'Main.scene'         : ('s',  'scene'),
    'Main.voxelLoc'      : ('v',  'voxelloc'),
    'Main.worldLoc'      : ('w',  'worldloc'),
    'Main.selectedImage' : ('i',  'selectedImage'),
    
    'SceneOpts.showColourBar'      : ('cb',  'showColourBar'),
    'SceneOpts.colourBarLocation'  : ('cbl', 'colourBarLocation'),
    'SceneOpts.colourBarLabelSide' : ('cbs', 'colourBarLabelSide'),
    'SceneOpts.showCursor'         : ('hc',  'hideCursor'),
    'SceneOpts.twoStageRender'     : ('tr',  'twoStageRendering'),
    
    'OrthoOpts.xzoom'       : ('xz', 'xzoom'),
    'OrthoOpts.yzoom'       : ('yz', 'yzoom'),
    'OrthoOpts.zzoom'       : ('zz', 'zzoom'),
    'OrthoOpts.layout'      : ('lo', 'layout'),
    'OrthoOpts.showXCanvas' : ('xh', 'hidex'),
    'OrthoOpts.showYCanvas' : ('yh', 'hidey'),
    'OrthoOpts.showZCanvas' : ('zh', 'hidez'),
    'OrthoOpts.showLabels'  : ('lh', 'hideLabels'),

    'OrthoOpts.xcentre'     : ('xc', 'xcentre'),
    'OrthoOpts.ycentre'     : ('yc', 'ycentre'),
    'OrthoOpts.zcentre'     : ('zc', 'zcentre'),

    'LightBoxOpts.sliceSpacing'   : ('ss', 'sliceSpacing'),
    'LightBoxOpts.ncols'          : ('nc', 'ncols'),
    'LightBoxOpts.nrows'          : ('nr', 'nrows'),
    'LightBoxOpts.zrange'         : ('zr', 'zrange'),
    'LightBoxOpts.showGridLines'  : ('sg', 'showGridLines'),
    'LightBoxOpts.highlightSlice' : ('hs', 'highlightSlice'),
    'LightBoxOpts.zax'            : ('zx', 'zaxis'),

    'Display.name'          : ('n',  'name'),
    'Display.interpolation' : ('in', 'interp'),
    'Display.resolution'    : ('r',  'resolution'),
    'Display.transform'     : ('tf', 'transform'),
    'Display.imageType'     : ('it', 'imageType'),
    'Display.volume'        : ('vl', 'volume'),
    'Display.alpha'         : ('a',  'alpha'),
    'Display.brightness'    : ('b',  'brightness'),
    'Display.contrast'      : ('c',  'contrast'),

    'VolumeOpts.displayRange'  : ('dr', 'displayRange'),
    'VolumeOpts.clippingRange' : ('cr', 'clippingRange'),
    'VolumeOpts.cmap'          : ('cm', 'cmap'),
    'VolumeOpts.invert'        : ('ci', 'cmapInvert'),

    'MaskOpts.colour'    : ('co', 'colour'),
    'MaskOpts.invert'    : ('mi', 'maskInvert'),
    'MaskOpts.threshold' : ('t',  'threshold'),

    'VectorOpts.displayMode' : ('d',  'displayMode'),
    'VectorOpts.xColour'     : ('xc', 'xColour'),
    'VectorOpts.yColour'     : ('yc', 'yColour'),
    'VectorOpts.zColour'     : ('zc', 'zColour'),
    'VectorOpts.suppressX'   : ('xs', 'suppressX'),
    'VectorOpts.suppressY'   : ('ys', 'suppressY'),
    'VectorOpts.suppressZ'   : ('zs', 'suppressZ'),
    'VectorOpts.modulate'    : ('m',  'modulate'),
    'VectorOpts.modThreshold': ('mt', 'modThreshold'),

})

# Help text for all of the options
HELP = td.TypeDict({

    'Main.scene'         : 'Scene to show. If not provided, the '
                           'previous scene layout is restored.',
    'Main.voxelLoc'      : 'Location to show (voxel coordinates of '
                           'first image)',
    'Main.worldLoc'      : 'Location to show (world coordinates, '
                           'takes precedence over --voxelloc)',
    'Main.selectedImage' : 'Selected image (default: last)',

    'SceneOpts.showCursor'         : 'Do not display the green cursor '
                                     'highlighting the current location',
    'SceneOpts.showColourBar'      : 'Show colour bar',
    'SceneOpts.colourBarLocation'  : 'Colour bar location',
    'SceneOpts.colourBarLabelSide' : 'Colour bar label orientation',
    'SceneOpts.twoStageRender'     : 'Enable two-stage rendering',
    
    'OrthoOpts.xzoom'       : 'X canvas zoom',
    'OrthoOpts.yzoom'       : 'Y canvas zoom',
    'OrthoOpts.zzoom'       : 'Z canvas zoom',
    'OrthoOpts.layout'      : 'Canvas layout',
    'OrthoOpts.showXCanvas' : 'Hide the X canvas',
    'OrthoOpts.showYCanvas' : 'Hide the Y canvas',
    'OrthoOpts.showZCanvas' : 'Hide the Z canvas',
    'OrthoOpts.showLabels'  : 'Hide orientation labels',

    'OrthoOpts.xcentre'     : 'X canvas display centre (world coordinates)',
    'OrthoOpts.ycentre'     : 'Y canvas display centre (world coordinates)',
    'OrthoOpts.zcentre'     : 'Z canvas display centre (world coordinates)',

    'LightBoxOpts.sliceSpacing'   : 'Slice spacing',
    'LightBoxOpts.ncols'          : 'Number of columns',
    'LightBoxOpts.nrows'          : 'Number of rows',
    'LightBoxOpts.zrange'         : 'Slice range',
    'LightBoxOpts.showGridLines'  : 'Show grid lines',
    'LightBoxOpts.highlightSlice' : 'Highlight current slice',
    'LightBoxOpts.zax'            : 'Z axis',

    'Display.name'          : 'Image name',
    'Display.interpolation' : 'Interpolation',
    'Display.resolution'    : 'Resolution',
    'Display.transform'     : 'Transformation',
    'Display.imageType'     : 'Image type',
    'Display.volume'        : 'Volume',
    'Display.alpha'         : 'Opacity',
    'Display.brightness'    : 'Brightness',
    'Display.contrast'      : 'Contrast',

    'VolumeOpts.displayRange'  : 'Display range',
    'VolumeOpts.clippingRange' : 'Clipping range',
    'VolumeOpts.cmap'          : 'Colour map',
    'VolumeOpts.invert'        : 'Invert colour map',

    'MaskOpts.colour'    : 'Colour',
    'MaskOpts.invert'    : 'Invert',
    'MaskOpts.threshold' : 'Threshold',

    'VectorOpts.displayMode'  : 'Display mode',
    'VectorOpts.xColour'      : 'X colour',
    'VectorOpts.yColour'      : 'Y colour',
    'VectorOpts.zColour'      : 'Z colour',
    'VectorOpts.suppressX'    : 'Suppress X magnitude',
    'VectorOpts.suppressY'    : 'Suppress Y magnitude',
    'VectorOpts.suppressZ'    : 'Suppress Z magnitude',
    'VectorOpts.modulate'     : 'Modulate vector colours',
    'VectorOpts.modThreshold' : 'Hide voxels where modulation '
                                'value is below this threshold '
                                '(expressed as a percentage)',
})

# Transform functions for properties where the
# value passed in on the command line needs to
# be manipulated before the property value is
# set
#
# TODO If/when you have a need for more
# complicated property transformations (i.e.
# non-reversible ones), you'll need to have
# an inverse transforms dictionary
TRANSFORMS = td.TypeDict({
    'SceneOpts.showCursor'  : lambda b: not b,
    'OrthoOpts.showXCanvas' : lambda b: not b,
    'OrthoOpts.showYCanvas' : lambda b: not b,
    'OrthoOpts.showZCanvas' : lambda b: not b,
    'OrthoOpts.showLabels'  : lambda b: not b,

    # The modulate property is handled specially
    # when reading in command line arguments -
    # this transform function is only used when
    # generating arguments
    'VectorOpts.modulate'   : lambda i: i.imageFile,
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

    mainArgs = {name: ARGUMENTS['Main', name] for name in OPTIONS['Main']}
    mainHelp = {name: HELP[     'Main', name] for name in OPTIONS['Main']}

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
                             type=float,
                             nargs=3,
                             help=mainHelp['worldLoc'])
    sceneParser.add_argument(*mainArgs['selectedImage'],
                             type=int,
                             help=mainHelp['selectedImage'])

    # Separate parser groups for ortho/lightbox, and for colour bar options
    sceneParser =  mainParser.add_argument_group(GROUPNAMES['SceneOpts']) 
    orthoParser =  mainParser.add_argument_group(GROUPNAMES['OrthoOpts'])
    lbParser    =  mainParser.add_argument_group(GROUPNAMES['LightBoxOpts'])

    _configSceneParser(    sceneParser)
    _configOrthoParser(    orthoParser)
    _configLightBoxParser( lbParser)


def _configParser(target, parser, propNames=None):

    if propNames is None:
        propNames = OPTIONS[target]
    shortArgs = {}
    longArgs  = {}
    helpTexts = {}

    for propName in propNames:

        shortArg, longArg = ARGUMENTS[target, propName]
        helpText          = HELP[     target, propName]

        shortArgs[propName] = shortArg
        longArgs[ propName] = longArg
        helpTexts[propName] = helpText

    props.addParserArguments(target,
                             parser,
                             cliProps=propNames,
                             shortArgs=shortArgs,
                             longArgs=longArgs,
                             propHelp=helpTexts)


def _configSceneParser(sceneParser):
    """Adds options to the given argument parser which allow
    the user to specify colour bar properties.
    """
    _configParser(sceneopts.SceneOpts, sceneParser)
   

def _configOrthoParser(orthoParser):
    """Adds options to the given parser allowing the user to
    configure an orthographic display.
    """

    OrthoOpts = orthoopts.OrthoOpts
    _configParser(OrthoOpts, orthoParser)
                             
    # Extra configuration options that are
    # not OrthoPanel properties, so can't
    # be automatically set up
    for opt, metavar in zip(['xcentre',  'ycentre',  'zcentre'],
                            [('Y', 'Z'), ('X', 'Z'), ('X', 'Y')]):
        
        shortArg, longArg = ARGUMENTS[OrthoOpts, opt]
        helpText          = HELP[     OrthoOpts, opt]

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
    _configParser(lightboxopts.LightBoxOpts, lbParser)


def _configImageParser(imgParser):
    """Adds options to the given image allowing the user to
    configure the display of a single image.
    """

    Display    = fsldisplay.Display
    VolumeOpts = volumeopts.VolumeOpts
    VectorOpts = vectoropts.VectorOpts
    MaskOpts   = maskopts  .MaskOpts
    
    dispDesc = 'Each display option will be applied to the '\
               'image which is listed before that option.'

    dispParser = imgParser.add_argument_group(GROUPNAMES[Display],
                                              dispDesc)
    volParser  = imgParser.add_argument_group(GROUPNAMES[VolumeOpts])
    vecParser  = imgParser.add_argument_group(GROUPNAMES[VectorOpts])
    maskParser = imgParser.add_argument_group(GROUPNAMES[MaskOpts])

    for target, parser in zip(
            [Display,    VolumeOpts, VectorOpts, MaskOpts],
            [dispParser, volParser,  vecParser,  maskParser]):

        propNames = list(OPTIONS[target])

        # The VectorOpts.modulate option needs
        # special treatment - see below
        addModulate = False
        if target == VectorOpts and 'modulate' in propNames:
            addModulate = True
            propNames.remove('modulate')

        _configParser(target, parser, propNames)

        # We need to process the modulate option
        # manually, rather than using the props.cli
        # module - see the handleImageArgs function.
        if addModulate:
            shortArg, longArg = ARGUMENTS[target, 'modulate']
            helpText          = HELP[     target, 'modulate']

            shortArg =  '-{}'.format(shortArg)
            longArg  = '--{}'.format(longArg)
            parser.add_argument(
                shortArg,
                longArg,
                metavar='FILE',
                help=helpText)

            
def parseArgs(mainParser, argv, name, desc, toolOptsDesc='[options]'):
    """Parses the given command line arguments, returning an
    :class:`argparse.Namespace` object containing all the arguments.

    The display options for individual images are parsed separately. The
    :class:`~argparse.Namespace` objects for each image are returned in a
    list, stored as an attribute, called ``images``, of the returned
    top-level ``Namespace`` instance. Each of the image ``Namespace``
    instances also has an attribute, called ``image``, which contains the
    full path of the image file that was speciied.

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

    log.debug('Parsing arguments for {}: {}'.format(name, argv))

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

    # Because I'm splitting the argument parsing across two
    # parsers, I'm using a custom print_help function 
    def printHelp(shortHelp=False):

        # Print help for the main parser first,
        # and then separately for the image parser
        if shortHelp: mainParser.print_usage()
        else:         mainParser.print_help()

        # Did I mention that I hate argparse?  Why
        # can't we customise the help text? 
        dispGroup = GROUPNAMES[fsldisplay.Display]
        if shortHelp:
            imgHelp    = imgParser.format_usage()
            imgHelp    = imgHelp.split('\n')

            # Argparse usage text starts with 'usage [toolname]:',
            # and then proceeds to give short help for all the
            # possible arguments. Here, we're removing this
            # 'usage [toolname]:' section, and replacing it with
            # spaces. We're also adding the image display argument
            # group title to the beginning of the usage text
            start      = ' '.join(imgHelp[0].split()[:2])
            imgHelp[0] = imgHelp[0].replace(start, ' ' * len(start))
            
            imgHelp.insert(0, dispGroup)

            imgHelp = '\n'.join(imgHelp)
        else:

            # Here we're skipping over the first section of
            # the image parser help text,  everything before
            # where the help text contains the image display
            # options (which were identifying by searching
            # through the text for the argument group title)
            imgHelp = imgParser.format_help()
            imgHelp = imgHelp[imgHelp.index(dispGroup):]
            
        print 
        print imgHelp

    # And I want to handle image argument errors,
    # rather than having the image parser force
    # the program to exit
    def imageArgError(message):
        raise RuntimeError(message)
    
    imgParser.error = imageArgError

    _configImageParser(imgParser)

    # Figure out where the image files
    # are in the argument list, accounting
    # for any options which accept image
    # files as arguments.
    # 
    # Make a list of all the options which
    # accept filenames, and which we need
    # to account for when we're searching
    # for image files, flattening the
    # short/long arguments into a 1D list.
    fileOpts = []

    # The VectorOpts.modulate option allows
    # the user to specify another image file
    # by which the vector image colours are
    # to be modulated
    fileOpts.append(ARGUMENTS[vectoropts.VectorOpts, 'modulate'])

    # There is a possibility that the user
    # may specify an image name which is the
    # same as the image file - so we make
    # sure that such situations don't result
    # in an image file match.
    fileOpts.append(ARGUMENTS[fsldisplay.Display, 'name'])

    fileOpts = reduce(lambda a, b: list(a) + list(b), fileOpts, [])

    imageIdxs = []
    for i in range(len(argv)):
        try:
            # imageio.addExt will raise an error if
            # the argument is not a valid image file
            argv[i] = iio.addExt(op.expanduser(argv[i]), mustExist=True)

            # Check that this image file was not a
            # parameter to a file option
            if i > 0 and argv[i - 1].strip('-') in fileOpts:
                continue

            # Otherwise, it's an image
            # file that needs to be loaded
            imageIdxs.append(i)
        except:
            continue
        
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
        dispGroup = GROUPNAMES[fsldisplay.Display]
        print 
        print imgHelp[imgHelp.index(dispGroup):]
        sys.exit(0)

    if namespace.help:
        printHelp()
        sys.exit(0)
 
    # Then parse each block of
    # display options one by one.
    namespace.images = []
    for i in range(len(imageIdxs) - 1):

        imgArgv = argv[imageIdxs[i]:imageIdxs[i + 1]]
        imgFile = imgArgv[0]
        imgArgv = imgArgv[1:]

        try:
            imgNamespace       = imgParser.parse_args(imgArgv)
            imgNamespace.image = imgFile
            
        except Exception as e:
            printHelp(shortHelp=True)
            print e.message
            sys.exit(1)

        # We just add a list of argparse.Namespace
        # objects, one for each image, to the
        # parent Namespace object.
        namespace.images.append(imgNamespace)

    return namespace


def _applyArgs(args, target, propNames=None):
    """Applies the given command line arguments to the given target object."""

    if propNames is None:
        propNames = OPTIONS[target]
        
    longArgs  = {name : ARGUMENTS[target, name][1] for name in propNames}
    xforms    = {}
    
    for name in propNames:
        xform = TRANSFORMS.get((target, name), None)
        if xform is not None:
            xforms[name] = xform

    props.applyArguments(target,
                         args,
                         propNames=propNames,
                         xformFuncs=xforms,
                         longArgs=longArgs)


def _generateArgs(source, propNames=None):
    """Does the opposite of :func:`_applyArgs` - generates command line
    arguments which can be used to configure another ``source`` instance
    in the same way as the provided one.
    """

    if propNames is None:
        propNames = OPTIONS[source]
        
    longArgs  = {name : ARGUMENTS[source, name][1] for name in propNames}
    xforms    = {}
    
    for name in propNames:
        xform = TRANSFORMS.get((source, name), None)
        if xform is not None:
            xforms[name] = xform

    return props.generateArguments(source,
                                   xformFuncs=xforms,
                                   cliProps=propNames,
                                   longArgs=longArgs)


def applySceneArgs(args, imageList, displayCtx, sceneOpts):
    """Configures the scene displayed by the given
    :class:`~fsl.fslview.displaycontext.DisplayContext` instance according
    to the arguments that were passed in on the command line.

    :arg args:       :class:`argparse.Namespace` object containing the parsed
                     command line arguments.

    :arg imageList:  A :class:`~fsl.data.image.ImageList` instance.

    :arg displayCtx: A :class:`~fsl.fslview.displaycontext.DisplayContext`
                     instance.

    :arg sceneOpts: 
    """
    
    # First apply all command line options
    # related to the display context 
    if args.selectedImage is not None:
        if args.selectedImage < len(imageList):
            displayCtx.selectedImage = args.selectedImage
    else:
        if len(imageList) > 0:
            displayCtx.selectedImage = len(imageList) - 1

    # voxel/world location
    if len(imageList) > 0:
        if args.worldloc:
            loc = args.worldloc
        elif args.voxelloc:
            display = displayCtx.getDisplayProperties(imageList[0])
            xform   = display.getTransform('voxel', 'display')
            loc     = transform.transform([args.voxelloc], xform)[0]
          
        else:
            loc = [displayCtx.bounds.xlo + 0.5 * displayCtx.bounds.xlen,
                   displayCtx.bounds.ylo + 0.5 * displayCtx.bounds.ylen,
                   displayCtx.bounds.zlo + 0.5 * displayCtx.bounds.zlen]

        displayCtx.location.xyz = loc

    # It is assuemd that the given sceneOpts 
    # object is a subclass of SceneOpts
    sceneProps  = OPTIONS['SceneOpts'] + OPTIONS[sceneOpts]
    _applyArgs(args, sceneOpts, sceneProps)


def generateSceneArgs(imageList, displayCtx, sceneOpts):
    """Generates command line arguments which describe the current state of
    the provided ``displayCtx`` and ``sceneOpts`` instances.
    """

    args = []


    args += ['--{}'.format(ARGUMENTS['Main.scene'][1])]
    if   isinstance(sceneOpts, orthoopts   .OrthoOpts):    args += ['ortho']
    elif isinstance(sceneOpts, lightboxopts.LightBoxOpts): args += ['lightbox']
    else: raise ValueError('Unrecognised SceneOpts '
                           'type: {}'.format(type(sceneOpts).__name__))

    # main options
    if len(imageList) > 0:
        args += ['--{}'.format(ARGUMENTS['Main.worldLoc'][1])]
        args += ['{}'.format(c) for c in displayCtx.location.xyz]

    if displayCtx.selectedImage is not None:
        args += ['--{}'.format(ARGUMENTS['Main.selectedImage'][1])]
        args += ['{}'.format(displayCtx.selectedImage)]

    args += _generateArgs(sceneOpts, OPTIONS['SceneOpts'])
    args += _generateArgs(sceneOpts, OPTIONS[ sceneOpts])

    return args


def generateImageArgs(image, displayCtx):
    """
    """
    display = displayCtx.getDisplayProperties(image)
    opts    = display   .getDisplayOpts()
    args    = _generateArgs(display) + _generateArgs(opts)

    return args


def applyImageArgs(args, imageList, displayCtx, **kwargs):
    """Loads and configures any images which were specified on the
    command line.

    :arg args:       A :class:`~argparse.Namespace` instance, as returned
                     by the :func:`parseArgs` function.
    
    :arg imageList:  An :class:`~fsl.data.image.ImageList` instance, to
                     which the images should be added.
    
    :arg displayCtx: A :class:`~fsl.fslview.displaycontext.DisplayContext`
                     instance, which manages the scene and image display.
    
    :arg kwargs:     Passed through to the
                     :func:`fsl.data.imageio.loadImages` function.
    """

    paths  = [i.image for i in args.images]
    images = iio.loadImages(paths, **kwargs)
        
    imageList.extend(images)

    # per-image display arguments
    for i, image in enumerate(imageList):

        display = displayCtx.getDisplayProperties(imageList[i])
        _applyArgs(args.images[i], display)

        # Retrieve the DisplayOpts instance
        # after applying arguments to the
        # Display instance - if the image type
        # is set on the command line, the
        # DisplayOpts instance will be replaced
        opts = display.getDisplayOpts()

        # VectorOpts.modulate is a Choice property,
        # where the valid choices are defined by
        # the current contents of the image list.
        # So when the user specifies a modulation
        # image, we need to do an explicit check
        # to see if the specified image is vaid
        # 
        # Here, I'm loading the image, and checking
        # to see if it can be used to modulate the
        # vector image (just with a dimension check).
        # If it can, I add it to the image list - the
        # applyArguments function will apply the
        # value. If the modulate file is not valid,
        # I print a warning, and clear the modulate
        # option.
        if isinstance(opts, vectoropts.VectorOpts) and \
           args.images[i].modulate is not None:

            try:
                modImage = fslimage.Image(args.images[i].modulate)
                
                if modImage.shape  != image.shape[ :3] or \
                   modImage.pixdim != image.pixdim[:3]:
                    raise RuntimeError(
                        'Image {} cannot be used to modulate {} - '
                        'dimensions don\'t match'.format(modImage, image))

                imageList.insert(0, modImage)
                opts.modulate = modImage
                args.images[i].modulate = None

                log.debug('Set {} to be modulated by {}'.format(
                    image, modImage))
                
            except Exception as e:
                log.warn(e) 

        # After handling the special cases above, we can
        # apply the CLI options to the Opts instance
        _applyArgs(args.images[i], opts)
