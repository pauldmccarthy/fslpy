#!/usr/bin/env python
#
# fslview.py - Image viewer.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""A 3D image viewer. See the :mod:`~fsl.fslview.frame` module for more
details. The command line interface is defined (and parsed) by the
:mod:`fslview_parseargs` module.
"""

import logging
import argparse

import fsl.fslview.fslview_parseargs as fslview_parseargs
import fsl.fslview.displaycontext    as displaycontext
import fsl.fslview.overlay           as fsloverlay


log = logging.getLogger(__name__)

    
def interface(parent, args, ctx):

    import                      wx
    import fsl.fslview.frame as fslviewframe
    import fsl.fslview.views as views

    overlayList, displayCtx, splashFrame = ctx

    # If a scene has not been specified, the default
    # behaviour is to restore the previous frame layout
    if args.scene is None: restore = True
    else:                  restore = False
    
    frame = fslviewframe.FSLViewFrame(
        parent, overlayList, displayCtx, restore)

    # Otherwise, we add the scene
    # specified by the user
    if   args.scene == 'ortho':    frame.addViewPanel(views.OrthoPanel)
    elif args.scene == 'lightbox': frame.addViewPanel(views.LightBoxPanel)


    # The viewPanel is assumed to be a CanvasPanel 
    # (i.e. either OrthoPanel or LightBoxPanel)
    viewPanel = frame.getViewPanels()[0]
    viewOpts  = viewPanel.getSceneOptions()

    fslview_parseargs.applySceneArgs(args, overlayList, displayCtx, viewOpts)

    if args.scene == 'ortho':

        xcentre = args.xcentre
        ycentre = args.ycentre
        zcentre = args.zcentre

        if xcentre is None: xcentre = displayCtx.location.yz
        if ycentre is None: ycentre = displayCtx.location.xz
        if zcentre is None: zcentre = displayCtx.location.xy

        viewPanel._xcanvas.centreDisplayAt(*xcentre)
        viewPanel._ycanvas.centreDisplayAt(*ycentre)
        viewPanel._zcanvas.centreDisplayAt(*zcentre)

    # Make sure the new frame is shown
    # before destroying the splash screen
    frame.Show(True)
    frame.Refresh()
    frame.Update()

    # Closing the splash screen immediately
    # can cause a crash under linux/GTK, so
    # we'll do it a bit later.
    def closeSplash():
        splashFrame.Close()

    wx.CallLater(500, closeSplash)
    
    return frame


def parseArgs(argv):
    """
    Parses the given command line arguments. Parameters:
    
      - argv:      command line arguments for fslview.
    """

    parser = argparse.ArgumentParser(add_help=False)

    # FSLView application options
    parser.add_argument('-gl', '--glversion',
                        metavar=('MAJOR', 'MINOR'), type=int, nargs=2,
                        help='Desired (major, minor) OpenGL version')

    # Options for configuring the scene are
    # managed by the fslview_parseargs module
    return fslview_parseargs.parseArgs(parser,
                                       argv,
                                       'fslview',
                                       'Image viewer')

def context(args):

    import wx
    import fsl.fslview.splash as fslsplash

    # Create a splash screen, and use it
    # to initialise the OpenGL context
    
    # The splash screen is used as the parent of the dummy
    # canvas created by the gl.getWXGLContext function; the
    # splash screen frame is returned by this function, and
    # passed through to the interface function above, which
    # takes care of destroying it.
    frame = fslsplash.FSLViewSplash(None)

    frame.CentreOnScreen()
    frame.Show()
    frame.Update()
    wx.Yield()

    import props
    import fsl.fslview.gl   as fslgl
    import fsl.data.strings as strings

    props.initGUI()
    
    # force the creation of a wx.glcanvas.GLContext object,
    # and initialise OpenGL version-specific module loads.
    fslgl.getWXGLContext(frame)
    fslgl.bootstrap(args.glversion)

    def status(overlay):
        frame.SetStatus(strings.messages['fslview.loading'].format(overlay))
        wx.Yield()

    # Create the overlay list (only one of these
    # ever exists) and the master DisplayContext.
    # A new DisplayContext instance will be
    # created for every new view that is opened
    # in the FSLViewFrame (which is created in
    # the interface function, above), but all
    # child DisplayContext instances will be
    # linked to this master one.
    overlayList = fsloverlay.OverlayList()
    displayCtx  = displaycontext.DisplayContext(overlayList)


    # While the DisplayContext may refer to 
    # multiple overlay groups, we are currently
    # using just one, allowing the user to specify
    # a set of overlays for which their display
    # properties are 'locked'.
    lockGroup   = displaycontext.OverlayGroup(displayCtx, overlayList)
    displayCtx.overlayGroups.append(lockGroup)

    log.debug('Created overlay list and master DisplayContext ({})'.format(
        id(displayCtx)))
    
    # Load the images - the splash screen status will 
    # be updated with the currently loading overlay name
    fslview_parseargs.applyOverlayArgs(
        args, overlayList, displayCtx, loadFunc=status)  

    return overlayList, displayCtx, frame


FSL_TOOLNAME  = 'FSLView'
FSL_INTERFACE = interface
FSL_CONTEXT   = context
FSL_PARSEARGS = parseArgs
