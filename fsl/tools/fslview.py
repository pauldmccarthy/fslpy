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

import argparse

import fslview_parseargs

    
def interface(parent, args, ctx):

    import fsl.fslview.fslviewframe   as fslviewframe
    import fsl.fslview.views          as views

    imageList, displayCtx = ctx
    
    frame = fslviewframe.FSLViewFrame(
        parent, imageList, displayCtx, args.default, args.glversion)
    
    if args.lightbox: frame.addViewPanel(views.LightBoxPanel)
    else:             frame.addViewPanel(views.OrthoPanel)

    viewPanel = frame.getViewPanels()[0][0]
    
    viewPanel.showCursor = not args.hideCursor
    
    return frame


def parseArgs(argv, namespace):
    """
    Parses the given command line arguments. Parameters:
    
      - argv:      command line arguments for fslview.
      - namespace: argparse.Namespace object to store the parsed arguments
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
                                       namespace,
                                       'fslview',
                                       'Image viewer')



FSL_TOOLNAME  = 'FSLView'
FSL_INTERFACE = interface
FSL_CONTEXT   = fslview_parseargs.handleImageArgs
FSL_PARSEARGS = parseArgs
