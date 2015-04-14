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


import time
import logging
import argparse

import fslview_parseargs

import fsl.fslview.displaycontext as displaycontext
import fsl.data.image             as fslimage


log = logging.getLogger(__name__)

    
def interface(parent, args, ctx):

    import fsl.fslview.frame as fslviewframe
    import fsl.fslview.views as views

    imageList, displayCtx, splashFrame = ctx

    # If a scene has not been specified, the default
    # behaviour is to restore the previous frame layout
    if args.scene is None: restore = True
    else:                  restore = False
    
    frame = fslviewframe.FSLViewFrame(
        parent, imageList, displayCtx, restore)

    # Otherwise, we add the scene
    # specified by the user
    if   args.scene == 'ortho':    frame.addViewPanel(views.OrthoPanel)
    elif args.scene == 'lightbox': frame.addViewPanel(views.LightBoxPanel)


    # The viewPanel is assumed to be a CanvasPanel 
    # (i.e. either OrthoPanel or LightBoxPanel)
    viewPanel = frame.getViewPanels()[0][0]
    viewOpts  = viewPanel.getSceneOptions()

    fslview_parseargs.applySceneArgs(args, imageList, displayCtx, viewOpts)

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

        # Set up a default for ortho views
        # layout (this will hopefully eventually
        # be done by the FSLViewFrame instance)
        import fsl.fslview.controls.imagelistpanel      as ilp
        import fsl.fslview.controls.locationpanel       as lop
        import fsl.fslview.controls.imagedisplaytoolbar as idt
        import fsl.fslview.controls.orthotoolbar        as ot
        
        viewPanel.togglePanel(ilp.ImageListPanel)
        viewPanel.togglePanel(lop.LocationPanel)
        viewPanel.togglePanel(idt.ImageDisplayToolBar, False, viewPanel)
        viewPanel.togglePanel(ot .OrthoToolBar,        False, viewPanel)

    # Make sure the new frame is shown
    # before destroying the splash screen
    frame.Show(True)
    frame.Refresh()
    frame.Update()

    splashFrame.Close()
    
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
    import fsl.fslview.gl     as fslgl
    import fsl.data.strings   as strings
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
    time.sleep(0.5)
    
    # force the creation of a wx.glcanvas.GLContext object,
    # and initialise OpenGL version-specific module loads.
    fslgl.getWXGLContext(frame)
    fslgl.bootstrap(args.glversion)

    def status(image):
        frame.SetStatus(strings.messages['fslview.loading'].format(image))
        wx.Yield()

    # Create the image list - only one of these
    # ever exists; and the master DisplayContext.
    # A new DisplayContext instance will be
    # created for every new view that is opened
    # in the FSLViewFrame (which is created in
    # the interface function, above), but all
    # child DisplayContext instances will be
    # linked to this master one.
    imageList  = fslimage.ImageList()
    displayCtx = displaycontext.DisplayContext(imageList)
    
    # Load the images - the splash screen status will 
    # be updated with the currently loading image name
    fslview_parseargs.applyImageArgs(
        args, imageList, displayCtx, loadFunc=status)  

    return imageList, displayCtx, frame


FSL_TOOLNAME  = 'FSLView'
FSL_INTERFACE = interface
FSL_CONTEXT   = context
FSL_PARSEARGS = parseArgs
