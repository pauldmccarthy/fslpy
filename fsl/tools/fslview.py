#!/usr/bin/env python
#
# fslview.py - Image viewer.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os
import sys
import os.path as op
import argparse

import wx
import wx.aui

import fsl.fslview.orthopanel        as orthopanel
import fsl.fslview.lightboxpanel     as lightboxpanel
import fsl.fslview.locationpanel     as locationpanel
import fsl.fslview.imagelistpanel    as imagelistpanel
import fsl.fslview.imagedisplaypanel as imagedisplaypanel

import fsl.data.fslimage as fslimage

import props


class FslViewPanel(wx.Panel):

    def __init__(self, parent, imageList):
        
        wx.Panel.__init__(self, parent)
        
        self._imageList = imageList
        self._auimgr    = wx.aui.AuiManager(self)

        self._centrePane = wx.aui.AuiNotebook(self)

        self._auimgr.AddPane(self._centrePane, wx.CENTRE)
        self._auimgr.Update()

        self._glContext = None


    def addOrthoPanel(self):

        panel = orthopanel.OrthoPanel(self,
                                      self._imageList,
                                      glContext=self._glContext)
        
        if self._glContext is None:
            self._glContext = panel.xcanvas.glContext
            
        self._centrePane.AddPage(panel, 'Ortho view')


    def addLightBoxPanel(self):

        panel = lightboxpanel.LightBoxPanel(self,
                                            self._imageList,
                                            glContext=self._glContext)
        
        if self._glContext is None:
            self._glContext = panel.canvas.glContext

        self._centrePane.AddPage(panel, 'Lightbox view')


    def addImageDisplayPanel(self):
        panel = imagedisplaypanel.ImageDisplayPanel(self, self._imageList)
        self._auimgr.AddPane(panel, wx.BOTTOM, 'Image display properties')
        self._auimgr.Update()


    def addImageListPanel(self):
        panel = imagelistpanel.ImageListPanel(self, self._imageList)
        self._auimgr.AddPane(panel, wx.BOTTOM, 'Loaded Images')
        self._auimgr.Update()


    def addLocationPanel(self):
        panel = locationpanel.LocationPanel(self, self._imageList)
        self._auimgr.AddPane(panel, wx.BOTTOM, 'Cursor location')
        self._auimgr.Update()
    

        
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
    mainParser.add_argument('-h', '--help',     action='store_true') 
    mainParser.add_argument('-l', '--lightbox', action='store_true',
                            help='Lightbox view')
    
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
                'rangeClip',
                'samplingRate',
                'cmap',
                'volume']

    # do not use l, v, h, or w, as they are used
    # either by fsl.py, or the mainParser above.
    props.addParserArguments(fslimage.ImageDisplay,
                             imgOpts,
                             cliProps=imgProps,
                             exclude='lvhw')

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
        props.applyArguments(image.display, args.images[i])
        images.append(image)
        
    imageList = fslimage.ImageList(images)
    return imageList

    
def interface(parent, args, imageList):
    
    panel = FslViewPanel(parent, imageList)

    menuBar  = wx.MenuBar()
    fileMenu = wx.Menu()
    viewMenu = wx.Menu()

    parent.SetMenuBar(menuBar)
    menuBar.Append(fileMenu, 'File')
    menuBar.Append(viewMenu, 'View')

    orthoAction        = viewMenu.Append(wx.ID_ANY, 'Ortho view')
    lightboxAction     = viewMenu.Append(wx.ID_ANY, 'Lightbox view')
    imageDisplayAction = viewMenu.Append(wx.ID_ANY, 'Image display properties')
    imageListAction    = viewMenu.Append(wx.ID_ANY, 'Loaded images')
    locationAction     = viewMenu.Append(wx.ID_ANY, 'Cursor location')
    openFileAction     = fileMenu.Append(wx.ID_ANY, 'Open file')
    openStandardAction = fileMenu.Append(wx.ID_ANY, 'Open standard')

    parent.Bind(wx.EVT_MENU,
                lambda ev: panel.addOrthoPanel(),
                orthoAction)
    parent.Bind(wx.EVT_MENU,
                lambda ev: panel.addLightBoxPanel(),
                lightboxAction)
    parent.Bind(wx.EVT_MENU,
                lambda ev: panel.addImageDisplayPanel(),
                imageDisplayAction)
    parent.Bind(wx.EVT_MENU,
                lambda ev: panel.addImageListPanel(),
                imageListAction)
    parent.Bind(wx.EVT_MENU,
                lambda ev: panel.addLocationPanel(),
                locationAction)
 
    parent.Bind(wx.EVT_MENU,
                lambda ev: panel._imageList.addImages(),
                openFileAction)

    fsldir = os.environ.get('FSLDIR', None)

    if fsldir is not None:
        stddir = op.join(fsldir, 'data', 'standard')
        parent.Bind(wx.EVT_MENU,
                    lambda ev: panel._imageList.addImages(stddir),
                    openStandardAction)
    else:
        openStandardAction.Enable(False)

    if args.lightbox: panel.addLightBoxPanel()
    else:             panel.addOrthoPanel()
    
    return panel
    

FSL_TOOLNAME  = 'FSLView'
FSL_INTERFACE = interface
FSL_CONTEXT   = handleArgs
FSL_PARSEARGS = parseArgs
