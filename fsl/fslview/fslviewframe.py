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

import fsl.fslview.views    as views
import fsl.fslview.controls as controls
import fsl.fslview.strings  as strings

class FSLViewFrame(wx.Frame):
    """A frame which implements a 3D image viewer.

    The :class:`wx.aui.AuiManager` is used to lay out various configuration
    panels. In the :attr:`wx.CENTRE` location of the
    :class:`~wx.aui.AuiManager` is a :class:`wx.aui.AuiNotebook` which allows
    multiple image views (e.g.
    :class:`~fsl.fslview.views.orthopanel.OrthoPanel`,
    :class:`~fsl.fslview.views.lightboxpanel.LightBoxPanel`) to be displayed.
    """

    def __init__(self, parent, imageList, displayCtx, default=False):
        """
        """
        
        wx.Frame.__init__(self, parent, title='FSLView')
        
        self._imageList  = imageList
        self._displayCtx = displayCtx
        self._auimgr     = aui.AuiManager(self)

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

        # we can have as many view
        # panels as we like
        self._viewPanels      = []
        self._viewPanelTitles = {}
        self._viewPanelCount  = 0

        # only one of each type of
        # control panel is allowed
        self._controlPanels = set()

        # only one view config panel
        # for each view panel that
        # exists
        self._viewConfigPanels = {}

        self._makeMenuBar()
        self._restoreState(default)

        self.Bind(wx.EVT_CLOSE, self._onClose)


    def _addViewPanel(self, panel, title, configMenuText=None):
        """Adds a view panel to the centre of the frame, and a menu item
        allowing the user to configure the view.
        """

        self._viewPanelCount = self._viewPanelCount + 1
        title = '{} {}'.format(title, self._viewPanelCount)

        self._viewPanelTitles[id(panel)] = title
        self._centrePane.AddPage(panel, title) 
        self._centrePane.SetSelection(self._centrePane.GetPageIndex(panel))

        if configMenuText is not None:
            configMenuText = configMenuText.format(title)
            configAction   = self._viewMenu.Append(wx.ID_ANY, configMenuText)
        
            def onConfig(ev):
                self._addViewConfigPanel(panel, title)        

            def onDestroy(ev):
                ev.Skip()
                try: self._viewMenu.RemoveItem(configAction)
                except wx._core.PyDeadObjectError: pass

            self .Bind(wx.EVT_MENU,           onConfig, configAction)
            panel.Bind(wx.EVT_WINDOW_DESTROY, onDestroy)
            

    def addOrthoPanel(self):
        """Adds an :class:`~fsl.fslview.views.orthopanel.OrthoPanel` display
        to the central :class:`~wx.aui.AuiNotebook` widget.
        """

        panel = views.OrthoPanel(self._centrePane,
                                 self._imageList,
                                 self._displayCtx,
                                 glContext=self._glContext)
            
        if self._glContext is None:
            self._glContext = panel.xcanvas.glContext
        
        self._addViewPanel(panel,
                           strings.orthoTitle,
                           strings.orthoConfigMenu) 


    def addLightBoxPanel(self):
        """Adds a :class:`~fsl.fslview.views.lightboxpanel.LightBoxPanel`
        display to the central :class:`~wx.aui.AuiNotebook` widget.
        """
        panel = views.LightBoxPanel(self._centrePane,
                                    self._imageList,
                                    self._displayCtx,
                                    glContext=self._glContext)
            
        if self._glContext is None:
            self._glContext = panel.canvas.glContext
        
        self._addViewPanel(panel,
                           strings.lightBoxTitle,
                           strings.lightBoxConfigMenu) 
 

    def addTimeSeriesPanel(self):
        """Adds a :class:`~fsl.fslview.views.lightboxpanel.LightBoxPanel`
        display to the central :class:`~wx.aui.AuiNotebook` widget.
        """

        panel = views.TimeSeriesPanel(self._centrePane,
                                      self._imageList,
                                      self._displayCtx)
        self._addViewPanel(panel, strings.timeSeriesTitle) 
 

    def _addViewConfigPanel(self, viewPanel, title):
        """
        """

        if id(viewPanel) in self._viewConfigPanels.keys():
            return
        
        confPanel = props.buildGUI(self, viewPanel)
        paneInfo = (aui.AuiPaneInfo()
                    .Dock()
                    .Top()
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
                    .BestSize(confPanel.GetBestSize())
                    .Name('config {}'.format(title)))
        
        self._auimgr.AddPane(confPanel, paneInfo)
        self._auimgr.Update()

        self._viewConfigPanels[id(viewPanel)] = confPanel

        def onViewPanelDestroy(ev):
            ev.Skip()

            # if the config panel has already been closed, it
            # will have been replaced with a python wrapper
            # around a deleted C++ object. When converted to
            # boolean, this wrapper will evaluate to False.
            if not confPanel:
                return
            
            self._auimgr.DetachPane(confPanel)
            self._auimgr.Update()
            confPanel.Destroy()

        def onConfPanelDestroy(ev):
            ev.Skip()
            self._viewConfigPanels.pop(id(viewPanel))

        viewPanel.Bind(wx.EVT_WINDOW_DESTROY, onViewPanelDestroy)
        confPanel.Bind(wx.EVT_WINDOW_DESTROY, onConfPanelDestroy)
                    

    def _addControlPanel(self, panelCls, title):
        """Adds the given panel to the :class:`~wx.aui.AuiManager`."""

        if panelCls in self._controlPanels:
            return

        panel = panelCls(self, self._imageList, self._displayCtx)
            
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

        self._controlPanels.add(panelCls)

        def onDestroy(ev):
            ev.Skip()
            self._controlPanels.remove(panelCls)

        panel.Bind(wx.EVT_WINDOW_DESTROY, onDestroy)


    def addImageDisplayPanel(self):
        """Adds a
        :class:`~fsl.fslview.controls.imagedisplaypanel.ImageDisplayPanel`
        widget to this panel (defaults to the bottom, according to the
        :class:`wx.aui.AuiManager`).
        """
        self._addControlPanel(
            controls.ImageDisplayPanel,
            strings.imageDisplayTitle)


    def addImageListPanel(self):
        """Adds a
        :class:`~fsl.fslview.controls.imagelistpanel.ImageListPanel`
        widget to this panel (defaults to the bottom, according to the
        :class:`wx.aui.AuiManager`).
        """ 
        self._addControlPanel(
            controls.ImageListPanel,
            strings.imageListTitle)


    def addLocationPanel(self):
        """Adds a :class:`~fsl.fslview.controls.locationpanel.LocationPanel`
        widget to this panel (defaults to the bottom, according to the
        :class:`wx.aui.AuiManager`).
        """ 
        self._addControlPanel(
            controls.LocationPanel,
            strings.locationTitle)


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

        self._fileMenu = fileMenu
        self._viewMenu = viewMenu

        orthoAction        = viewMenu.Append(wx.ID_ANY, strings.orthoTitle)
        lightboxAction     = viewMenu.Append(wx.ID_ANY, strings.lightBoxTitle)
        timeSeriesAction   = viewMenu.Append(wx.ID_ANY,
                                             strings.timeSeriesTitle)
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
                  lambda ev: self.addTimeSeriesPanel(),
                  timeSeriesAction) 
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
