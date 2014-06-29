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

import fsl.fslview.orthopanel     as orthopanel
import fsl.fslview.lightboxpanel  as lightboxpanel
import fsl.fslview.locationpanel  as locationpanel
import fsl.fslview.imagelistpanel as imagelistpanel

import fsl.data.fslimage as fslimage

import props


class FslViewPanel(wx.Panel):

    def __init__(self, parent, imageList):
        
        wx.Panel.__init__(self, parent)
        self.imageList = imageList

        self.glContext = None

        self.topPanel = wx.Panel(self)

        self.topSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.topPanel.SetSizer(self.topSizer)

        self.locPanel  = locationpanel .LocationPanel( self, imageList)

        self.topSizer.Add(self.locPanel, flag=wx.EXPAND)
        self.topSizer.Add((1, 1),        flag=wx.EXPAND, proportion=1)

        self.ctrlPanel = None
        self.mainPanel = None
        self.listPanel = imagelistpanel.ImageListPanel(self, imageList)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        self.sizer.Add(self.topPanel, flag=wx.EXPAND)
        self.sizer.Add((1, 1), flag=wx.EXPAND, proportion=1)
        
        self.sizer.Add(self.listPanel, flag=wx.EXPAND)

        self.SetAutoLayout(1)

        self.showOrtho()
        self.Fit()


    def _replace(self, mainPanel, ctrlPanel):

        self.topSizer.Remove(1)
        self.sizer.Remove(1)

        self.topSizer.Insert(1, ctrlPanel, flag=wx.EXPAND)
        self.sizer.Insert(1, mainPanel, flag=wx.EXPAND, proportion=1)

        if self.mainPanel is not None: self.mainPanel.Destroy()
        if self.ctrlPanel is not None: self.ctrlPanel.Destroy()

        self.mainPanel = mainPanel
        self.ctrlPanel = ctrlPanel
        
        self.Layout()


    def showOrtho(self):

        if isinstance(self.mainPanel, orthopanel.OrthoPanel):
            return

        mainPanel = orthopanel.OrthoPanel(self, self.imageList,
                                          glContext=self.glContext)
        
        ctrlPanel = props.buildGUI(self, mainPanel)

        if self.glContext is None:
            self.glContext = mainPanel.xcanvas.glContext

        self._replace(mainPanel, ctrlPanel)


    def showLightBox(self):

        if isinstance(self.mainPanel, lightboxpanel.LightBoxPanel):
            return

        mainPanel = lightboxpanel.LightBoxPanel(self, self.imageList,
                                                glContext=self.glContext)
        
        ctrlPanel = props.buildGUI(self, mainPanel.canvas)

        if self.glContext is None:
            self.glContext = mainPanel.canvas.glContext 

        self._replace(mainPanel, ctrlPanel) 
        

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

    menubar  = parent.GetMenuBar()
    fileMenu = menubar.GetMenu(menubar.FindMenu('File'))
    viewMenu = wx.Menu()
    menubar.Append(viewMenu, 'View')

    orthoAction    = viewMenu.Append(wx.ID_ANY, 'Ortho view')
    lightboxAction = viewMenu.Append(wx.ID_ANY, 'Lightbox view')

    parent.Bind(wx.EVT_MENU, lambda ev: panel.showOrtho(),    orthoAction)
    parent.Bind(wx.EVT_MENU, lambda ev: panel.showLightBox(), lightboxAction)

    openFileAction     = fileMenu.Append(wx.ID_ANY, 'Open file')
    openStandardAction = fileMenu.Append(wx.ID_ANY, 'Open standard')

    parent.Bind(wx.EVT_MENU,
                lambda ev: panel.listPanel._addImage(ev),
                openFileAction)

    fsldir = os.environ.get('FSLDIR', None)

    if fsldir is not None:
        stddir = op.join(fsldir, 'data', 'standard')
        parent.Bind(wx.EVT_MENU,
                    lambda ev: panel.listPanel._addImage(ev, stddir),
                    openStandardAction)
    else:
        openStandardAction.Enable(False)

    if args.lightbox:
        panel.showLightBox()
    
    return panel
    

FSL_TOOLNAME  = 'FSLView'
FSL_INTERFACE = interface
FSL_CONTEXT   = handleArgs
FSL_PARSEARGS = parseArgs
