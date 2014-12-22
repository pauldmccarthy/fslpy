#!/usr/bin/env python
#
# fslview.py - Image viewer.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""A 3D image viewer. See the :mod:`~fsl.fslview.fslviewframe` module for more
details. The command line interface is defined (and parsed) by the
:mod:`fslview_parseargs` module.
"""

import logging
log = logging.getLogger(__name__)

import argparse

import fslview_parseargs

    
def interface(parent, args, ctx):

    import fsl.fslview.fslviewframe   as fslviewframe
    import fsl.fslview.views          as views
    import fsl.fslview.gl             as fslgl

    imageList, displayCtx = ctx
    
    frame = fslviewframe.FSLViewFrame(
        parent, imageList, displayCtx, args.default)

    # Some platforms will crash if the GL Canvas is not
    # visible before the GL context is set (which occurs
    # in the fslgl.getWXGLContext call below).
    frame.Show()

    # initialise OpenGL version-specific module loads, and
    # force the creation of a wx.glcanvas.GLContext object
    fslgl.getWXGLContext()
    fslgl.bootstrap(args.glversion)
    
    if args.lightbox: frame.addViewPanel(views.LightBoxPanel)
    else:             frame.addViewPanel(views.OrthoPanel)

    viewPanel = frame.getViewPanels()[0][0]

    # Look in fslview_parseargs to see all
    # of the possible display options 
    viewPanel.showCursor = not args.hideCursor

    if args.lightbox:

        for prop in ['sliceSpacing',
                     'ncols',
                     'nrows',
                     'zrange',
                     'showGridLines',
                     'zax']:
            val = getattr(args, prop, None)

            if val is not None:
                setattr(viewPanel, prop, val)

    else:
        if args.hidex:              viewPanel.showXCanvas = False
        if args.hidey:              viewPanel.showYCanvas = False
        if args.hidez:              viewPanel.showZCanvas = False
        if args.hideLabels:         viewPanel.showLabels  = False
        if args.layout is not None: viewPanel.layout      = args.layout 
        if args.xzoom  is not None: viewPanel.xzoom       = args.xzoom
        if args.yzoom  is not None: viewPanel.yzoom       = args.yzoom
        if args.zzoom  is not None: viewPanel.zzoom       = args.zzoom

        xcentre = args.xcentre
        ycentre = args.ycentre
        zcentre = args.zcentre

        if xcentre is None: xcentre = displayCtx.location.yz
        if ycentre is None: ycentre = displayCtx.location.xz
        if zcentre is None: zcentre = displayCtx.location.xy

        viewPanel._xcanvas.centreDisplayAt(*xcentre)
        viewPanel._ycanvas.centreDisplayAt(*ycentre)
        viewPanel._zcanvas.centreDisplayAt(*zcentre)

    if args.showColourBar:
        viewPanel.showColourBar = True

        if args.colourBarLocation is not None:
            viewPanel.colourBarLocation = args.colourBarLocation
        if args.colourBarLabelSide is not None:
            viewPanel.colourBarLabelSide = args.colourBarLabelSide 
    
    return frame


def parseArgs(argv):
    """
    Parses the given command line arguments. Parameters:
    
      - argv:      command line arguments for fslview.
    """

    parser = argparse.ArgumentParser(add_help=False)

    # FSLView application options
    parser.add_argument('-def', '--default',   action='store_true',
                        help='Default layout')
    parser.add_argument('-gl', '--glversion',
                        metavar=('MAJOR', 'MINOR'), type=int, nargs=2,
                        help='Desired (major, minor) OpenGL version')

    # Options for configuring the scene are
    # managed by the fslview_parseargs module
    return fslview_parseargs.parseArgs(parser,
                                       argv,
                                       'fslview',
                                       'Image viewer')


FSL_TOOLNAME  = 'FSLView'
FSL_INTERFACE = interface
FSL_CONTEXT   = fslview_parseargs.handleImageArgs
FSL_PARSEARGS = parseArgs
