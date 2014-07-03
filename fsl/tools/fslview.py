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

import os
import sys
import os.path as op
import argparse

import wx
import wx.aui as aui

import fsl.fslview.orthopanel        as orthopanel
import fsl.fslview.lightboxpanel     as lightboxpanel
import fsl.fslview.locationpanel     as locationpanel
import fsl.fslview.imagelistpanel    as imagelistpanel
import fsl.fslview.imagedisplaypanel as imagedisplaypanel
import fsl.fslview.strings           as strings

import fsl.data.fslimage as fslimage

import props


class FslViewFrame(wx.Frame):
    """A frame which implements a 3D image viewer.

    The :class:`wx.aui.AuiManager` is used to lay out various configuration
    panels. In the :attr:`wx.CENTRE` location of the
    :class:`~wx.aui.AuiManager` is a :class:`wx.aui.AuiNotebook` which allows
    multiple image perspectives (e.g.
    :class:`~fsl.fslview.orthopanel.OrthoPanel`,
    :class:`~fsl.fslview.orthopanel.LightBoxPanel`) to be displayed.
    """

    def __init__(self, parent, imageList, default=False):
        """
        """
        
        wx.Frame.__init__(self, parent, title='FSLView')
        
        self._imageList = imageList
        self._auimgr    = aui.AuiManager(self)

        self._auimgr.SetDockSizeConstraint(50, 50)

        self._centrePane = aui.AuiNotebook(
            self,
            style=aui.AUI_NB_TOP | 
            aui.AUI_NB_TAB_SPLIT | 
            aui.AUI_NB_TAB_MOVE |
            aui.AUI_NB_CLOSE_ON_ALL_TABS)

        paneInfo = (aui.AuiPaneInfo()
                    .CentrePane()
                    .Name('centre'))

        self._auimgr.AddPane(self._centrePane, paneInfo)
        self._auimgr.Update()

        # This attribute is set when a view panel (e.g.
        # ortho or lightbox) is added to the panel
        self._glContext = None

        self._restoreState(default)

        self.Bind(wx.EVT_CLOSE, self._onClose)



    def _onClose(self, ev):
        """Called on requests to close this :class:`FSLViewFrame`.

        Saves the frame position, size, and layout, so it may be preserved the
        next time it is opened. See the :meth:`_restoreState` method.
        """

        ev.Skip()

        config = wx.Config('FSLView')

        size     = self.GetSize().Get()
        position = self.GetScreenPosition().Get()
        layout   = self._auimgr.SavePerspective()

        log.debug('Saving size: {}'    .format(str(size)))
        log.debug('Saving position: {}'.format(str(position)))
        log.debug('Saving layout: {}'  .format(str(layout)))

        config.Write('size',     str(size))
        config.Write('position', str(position))
        config.Write('layout',   layout)

        
    def _parseSavedSize(self, size):
        """Parses the given string, which is assumed to contain a size tuple.
        """
        
        try:    return tuple(map(int, size[1:-1].split(',')))
        except: return None

        
    _parseSavedPoint = _parseSavedSize
    """A proxy for the :meth:`_parseSavedSize` method.
    """ 

            
    def _parseSavedLayout(self, layout):
        """Parses the given string, which is assumed to contain an encoded
        :class:`wx.aui.AuiManager` perspective (see
        :meth:`~wx.aui.AuiManager.SavePerspective`).

        Returns a list of class names, specifying the control panels
        (e.g. :class:`~fsl.fslview.imagelistpanel.ImageListPanel`) which were
        previously open, and need to be created.
        """

        try:

            names    = [] 
            sections = layout.split('|')[1:]

            for section in sections:
                
                if section.strip() == '': continue
                
                attrs = section.split(';')
                attrs = dict([tuple(nvpair.split('=')) for nvpair in attrs])

                if 'name' in attrs:
                    names.append(attrs['name'])

            return names
        except:
            return []

        
    def _restoreState(self, default=False):
        """Called on :meth:`__init__`. If any frame size/layout properties
        have previously been saved, they are applied to this frame.

        :arg bool default: If ``True``, any saved state is ignored.
        """
        
        config = wx.Config('FSLView')

        size     = None
        position = None
        layout   = None
        panels   = []

        if not default:
            size     = self._parseSavedSize(  config.Read('size'))
            position = self._parseSavedPoint( config.Read('position'))
            layout   = config.Read('layout')
            panels   = self._parseSavedLayout(layout)

        if size is not None:
            log.debug('Restoring previous size: {}'.format(size))
            self.SetSize(size)
        else:
            self.SetSize((800, 600))

        if position is not None:
            log.debug('Restoring previous position: {}'.format(position))
            self.SetPosition(position)
        else:
            self.Centre()

        if layout is not None:
            log.debug('Restoring previous layout: {}'.format(layout))

            for panel in panels:
                panelMeth = getattr(self, 'add{}'.format(panel), None)

                if panelMeth is not None:
                    panelMeth()

            self._auimgr.LoadPerspective(layout)


    def addOrthoPanel(self):
        """Adds an :class:`~fsl.fslview.orthopanel.OrthoPanel` display
        to the central :class:`~wx.aui.AuiNotebook` widget.
        """

        panel = orthopanel.OrthoPanel(self._centrePane,
                                      self._imageList,
                                      glContext=self._glContext)

        if self._glContext is None:
            self._glContext = panel.xcanvas.glContext

        self._centrePane.AddPage(panel, strings.orthoTitle) 


    def addLightBoxPanel(self):
        """Adds a :class:`~fsl.fslview.lightboxpanel.LightBoxPanel` display
        to the central :class:`~wx.aui.AuiNotebook` widget.
        """ 

        panel = lightboxpanel.LightBoxPanel(self._centrePane,
                                            self._imageList,
                                            glContext=self._glContext)
        
        if self._glContext is None:
            self._glContext = panel.canvas.glContext

        self._centrePane.AddPage(panel, strings.lightBoxTitle)


    def _addControlPanel(self, panel, title):
        """Adds the given panel to the :class:`~wx.aui.AuiManager`."""
        paneInfo = (aui.AuiPaneInfo()
                    .Dock()
                    .Bottom()
                    .Dockable(True)
                    .Floatable(True)
                    .Movable(True)
                    .CloseButton(True)
                    .DestroyOnClose(True)
                    .Gripper(False)
                    .MaximizeButton(False)
                    .MinimizeButton(False)
                    .PinButton(False)
                    .Caption(title)
                    .CaptionVisible(True)
                    .BestSize(panel.GetBestSize())
                    .Name(panel.__class__.__name__))
                    
        self._auimgr.AddPane(panel, paneInfo)
        self._auimgr.Update()


    def addImageDisplayPanel(self):
        """Adds a :class:`~fsl.fslview.imagedisplaypanel.ImageDisplayPanel`
        widget to this panel (defaults to the bottom, according to the
        :class:`wx.aui.AuiManager`).
        """
        panel = imagedisplaypanel.ImageDisplayPanel(self, self._imageList)
        self._addControlPanel(panel, strings.imageDisplayTitle)


    def addImageListPanel(self):
        """Adds a :class:`~fsl.fslview.imagelistpanel.ImageListPanel`
        widget to this panel (defaults to the bottom, according to the
        :class:`wx.aui.AuiManager`).
        """ 
        panel = imagelistpanel.ImageListPanel(self, self._imageList)
        self._addControlPanel(panel, strings.imageListTitle)


    def addLocationPanel(self):
        """Adds a :class:`~fsl.fslview.locationpanel.LocationPanel`
        widget to this panel (defaults to the bottom, according to the
        :class:`wx.aui.AuiManager`).
        """ 
        panel = locationpanel.LocationPanel(self, self._imageList)
        self._addControlPanel(panel, strings.locationTitle)
    

def _makeMenuBar(frame):
    """Constructs a bunch of menu items for working with the given
    :class:`~fsl.tools.fslview.FslViewFrame`.
    """

    menuBar = frame.GetMenuBar()

    if menuBar is None:
        menuBar = wx.MenuBar()
        frame.SetMenuBar(menuBar)

    try:
        fileMenu = menuBar.GetMenu(menuBar.FindMenu('File'))
    except:
        fileMenu = wx.Menu()
        menuBar.Append(fileMenu, 'File')
        
    viewMenu = wx.Menu()
    menuBar.Append(viewMenu, 'View')

    orthoAction        = viewMenu.Append(wx.ID_ANY, strings.orthoTitle)
    lightboxAction     = viewMenu.Append(wx.ID_ANY, strings.lightBoxTitle)
    imageDisplayAction = viewMenu.Append(wx.ID_ANY, strings.imageDisplayTitle)
    imageListAction    = viewMenu.Append(wx.ID_ANY, strings.imageListTitle)
    locationAction     = viewMenu.Append(wx.ID_ANY, strings.locationTitle)
    openFileAction     = fileMenu.Append(wx.ID_ANY, strings.openFile)
    openStandardAction = fileMenu.Append(wx.ID_ANY, strings.openStd)

    frame.Bind(wx.EVT_MENU,
               lambda ev: frame.addOrthoPanel(),
               orthoAction)
    frame.Bind(wx.EVT_MENU,
               lambda ev: frame.addLightBoxPanel(),
               lightboxAction)
    frame.Bind(wx.EVT_MENU,
               lambda ev: frame.addImageDisplayPanel(),
               imageDisplayAction)
    frame.Bind(wx.EVT_MENU,
               lambda ev: frame.addImageListPanel(),
               imageListAction)
    frame.Bind(wx.EVT_MENU,
               lambda ev: frame.addLocationPanel(),
               locationAction)
 
    frame.Bind(wx.EVT_MENU,
                lambda ev: frame._imageList.addImages(),
                openFileAction)

    # disable the 'add standard' menu
    # item if $FSLDIR is not set
    fsldir = os.environ.get('FSLDIR', None)

    if fsldir is not None:
        stddir = op.join(fsldir, 'data', 'standard')
        frame.Bind(wx.EVT_MENU,
                   lambda ev: frame._imageList.addImages(stddir),
                   openStandardAction)
    else:
        openStandardAction.Enable(False)

    
def interface(parent, args, imageList):
    
    frame = FslViewFrame(parent, imageList, args.default)
    
    _makeMenuBar(frame)
    
    if args.lightbox: frame.addLightBoxPanel()
    else:             frame.addOrthoPanel()
    
    return frame


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
    mainParser.add_argument('-d', '--default',  action='store_true',
                            help='Default layout') 
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

    # do not use l, v, h, d, or w, as they are used
    # either by fsl.py, or the mainParser above.
    props.addParserArguments(fslimage.ImageDisplay,
                             imgOpts,
                             cliProps=imgProps,
                             exclude='lvhdw')

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
    

FSL_TOOLNAME  = 'FSLView'
FSL_INTERFACE = interface
FSL_CONTEXT   = handleArgs
FSL_PARSEARGS = parseArgs
