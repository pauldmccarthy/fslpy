#!/usr/bin/env python
#
# fslviewframe.py - A wx.Frame which implemnents a 3D image viewer.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import os
import os.path as op

import wx
import wx.aui as aui

import props

import fsl.fslview.views.orthopanel           as orthopanel
import fsl.fslview.views.lightboxpanel        as lightboxpanel
import fsl.fslview.controls.locationpanel     as locationpanel
import fsl.fslview.controls.imagelistpanel    as imagelistpanel
import fsl.fslview.controls.imagedisplaypanel as imagedisplaypanel 
import fsl.fslview.strings                    as strings

class FSLViewFrame(wx.Frame):
    """A frame which implements a 3D image viewer.

    The :class:`wx.aui.AuiManager` is used to lay out various configuration
    panels. In the :attr:`wx.CENTRE` location of the
    :class:`~wx.aui.AuiManager` is a :class:`wx.aui.AuiNotebook` which allows
    multiple image perspectives (e.g.
    :class:`~fsl.fslview.views.orthopanel.OrthoPanel`,
    :class:`~fsl.fslview.views.lightboxpanel.LightBoxPanel`) to be displayed.
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

        self._makeMenuBar()
        self._configContextMenu()
        self._restoreState(default)

        self.Bind(wx.EVT_CLOSE, self._onClose)


    def _configContextMenu(self):

        def showMenu(ev):

            idx      = ev.GetSelection()
            tabCtrl  = ev.GetEventObject()
            mousePos = wx.GetMousePosition()

            if idx == wx.NOT_FOUND: return

            panel = tabCtrl.GetPage(idx).window
            
        
            def showConfigDialog(ev):
                dlg = props.buildDialog(self, panel)
                dlg.SetPosition(mousePos)
                dlg.Show()

            def closePanel(ev):
                self._centrePane.RemovePage(idx)
                panel.Destroy()

            menu       = wx.Menu()
            configItem = wx.MenuItem(menu, wx.ID_ANY, 'Configure')
            closeItem  = wx.MenuItem(menu, wx.ID_ANY, 'Close')

            menu.AppendItem(configItem)
            menu.AppendItem(closeItem)

            menu.Bind(wx.EVT_MENU, showConfigDialog, configItem)
            menu.Bind(wx.EVT_MENU, closePanel,       closeItem)

            self.PopupMenu(menu, self.ScreenToClient(mousePos))

        self._centrePane.Bind(aui.EVT__AUINOTEBOOK_TAB_RIGHT_DOWN, showMenu)
 

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
        (e.g. :class:`~fsl.fslview.controls.imagelistpanel.ImageListPanel`)
        which were previously open, and need to be created.
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
        """Adds an :class:`~fsl.fslview.views.orthopanel.OrthoPanel` display
        to the central :class:`~wx.aui.AuiNotebook` widget.
        """

        panel = orthopanel.OrthoPanel(self._centrePane,
                                      self._imageList,
                                      glContext=self._glContext)

        if self._glContext is None:
            self._glContext = panel.xcanvas.glContext

        self._centrePane.AddPage(panel, strings.orthoTitle) 
        self._centrePane.SetSelection(self._centrePane.GetPageIndex(panel))


    def addLightBoxPanel(self):
        """Adds a :class:`~fsl.fslview.views.lightboxpanel.LightBoxPanel`
        display to the central :class:`~wx.aui.AuiNotebook` widget.
        """ 

        panel = lightboxpanel.LightBoxPanel(self._centrePane,
                                            self._imageList,
                                            glContext=self._glContext)
        
        if self._glContext is None:
            self._glContext = panel.canvas.glContext

        self._centrePane.AddPage(panel, strings.lightBoxTitle)
        self._centrePane.SetSelection(self._centrePane.GetPageIndex(panel))


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
        """Adds a
        :class:`~fsl.fslview.controls.imagedisplaypanel.ImageDisplayPanel`
        widget to this panel (defaults to the bottom, according to the
        :class:`wx.aui.AuiManager`).
        """
        panel = imagedisplaypanel.ImageDisplayPanel(self, self._imageList)
        self._addControlPanel(panel, strings.imageDisplayTitle)


    def addImageListPanel(self):
        """Adds a
        :class:`~fsl.fslview.controls.imagelistpanel.ImageListPanel`
        widget to this panel (defaults to the bottom, according to the
        :class:`wx.aui.AuiManager`).
        """ 
        panel = imagelistpanel.ImageListPanel(self, self._imageList)
        self._addControlPanel(panel, strings.imageListTitle)


    def addLocationPanel(self):
        """Adds a :class:`~fsl.fslview.controls.locationpanel.LocationPanel`
        widget to this panel (defaults to the bottom, according to the
        :class:`wx.aui.AuiManager`).
        """ 
        panel = locationpanel.LocationPanel(self, self._imageList)
        self._addControlPanel(panel, strings.locationTitle)
    

    def _makeMenuBar(self):
        """Constructs a bunch of menu items for working with the given
        :class:`~fsl.fslview.fslviewframe.FslViewFrame`.
        """

        menuBar = wx.MenuBar()
        self.SetMenuBar(menuBar)

        fileMenu = wx.Menu()
        menuBar.Append(fileMenu, 'File')

        viewMenu = wx.Menu()
        menuBar.Append(viewMenu, 'View')

        orthoAction        = viewMenu.Append(wx.ID_ANY, strings.orthoTitle)
        lightboxAction     = viewMenu.Append(wx.ID_ANY, strings.lightBoxTitle)
        imageDisplayAction = viewMenu.Append(wx.ID_ANY,
                                             strings.imageDisplayTitle)
        imageListAction    = viewMenu.Append(wx.ID_ANY, strings.imageListTitle)
        locationAction     = viewMenu.Append(wx.ID_ANY, strings.locationTitle)
        openFileAction     = fileMenu.Append(wx.ID_ANY, strings.openFile)
        openStandardAction = fileMenu.Append(wx.ID_ANY, strings.openStd)

        self.Bind(wx.EVT_MENU,
                  lambda ev: self.addOrthoPanel(),
                  orthoAction)
        self.Bind(wx.EVT_MENU,
                  lambda ev: self.addLightBoxPanel(),
                  lightboxAction)
        self.Bind(wx.EVT_MENU,
                  lambda ev: self.addImageDisplayPanel(),
                  imageDisplayAction)
        self.Bind(wx.EVT_MENU,
                  lambda ev: self.addImageListPanel(),
                  imageListAction)
        self.Bind(wx.EVT_MENU,
                  lambda ev: self.addLocationPanel(),
                  locationAction)

        self.Bind(wx.EVT_MENU,
                  lambda ev: self._imageList.addImages(),
                  openFileAction)

        # disable the 'add standard' menu
        # item if $FSLDIR is not set
        fsldir = os.environ.get('FSLDIR', None)

        if fsldir is not None:
            stddir = op.join(fsldir, 'data', 'standard')
            self.Bind(wx.EVT_MENU,
                       lambda ev: self._imageList.addImages(stddir),
                       openStandardAction)
        else:
            openStandardAction.Enable(False)
