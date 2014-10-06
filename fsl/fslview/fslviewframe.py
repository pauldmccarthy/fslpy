#!/usr/bin/env python
#
# fslviewframe.py - A wx.Frame which implemnents a 3D image viewer.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import wx
import wx.aui as aui

import props

import views
import controls
import actions
import strings


class FSLViewFrame(wx.Frame):
    """A frame which implements a 3D image viewer.

    The :class:`wx.aui.AuiManager` is used to lay out various configuration
    panels. In the :attr:`wx.CENTRE` location of the
    :class:`~wx.aui.AuiManager` is a :class:`wx.aui.AuiNotebook` which allows
    multiple image views (e.g.
    :class:`~fsl.fslview.views.orthopanel.OrthoPanel`,
    :class:`~fsl.fslview.views.lightboxpanel.LightBoxPanel`) to be displayed.
    """

    def __init__(self,
                 parent,
                 imageList,
                 displayCtx,
                 default=False):
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
                    .Name('centre pane'))

        self._auimgr.AddPane(self._centrePane, paneInfo)
        self._auimgr.Update()

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

        
    def getViewPanels(self):
        """Returns a list of all view panels that currently exist, and a list
        of their titles.
        """
        return (self._viewPanels,
                [self._viewPanelTitles[id(vp)] for vp in self._viewPanels])


    def addViewPanel(self, panelCls):
        """Adds a view panel to the centre of the frame, and a menu item
        allowing the user to configure the view.
        """

        title    = strings.viewPanelTitles[        panelCls]
        menuText = strings.viewPanelConfigMenuText[panelCls]

        panel    = panelCls(self._centrePane,
                            self._imageList,
                            self._displayCtx) 

        self._viewPanelCount = self._viewPanelCount + 1
        title = '{} {}'.format(title, self._viewPanelCount)

        self._viewPanels.append(panel)
        self._viewPanelTitles[id(panel)] = title
        self._centrePane.AddPage(panel, title, True)
        self._centrePane.Split(
            self._centrePane.GetPageIndex(panel),
            wx.RIGHT)

        if panel.hasConfigOptions():
            menuText     = menuText.format(title)
            configAction = self._viewMenu.Append(wx.ID_ANY, menuText)
        
            def onConfig(ev):
                self._addViewConfigPanel(panel, title)        

            def onDestroy(ev):
                ev.Skip()
                try: self._viewMenu.RemoveItem(configAction)
                except wx._core.PyDeadObjectError: pass

            self .Bind(wx.EVT_MENU,           onConfig, configAction)
            panel.Bind(wx.EVT_WINDOW_DESTROY, onDestroy)
            

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
                    

    def addControlPanel(self, panelCls):
        """Adds the given panel to the :class:`~wx.aui.AuiManager`."""

        # If the specified control panel is
        # already open, don't open a new one.
        if panelCls in self._controlPanels:
            return

        title = strings.controlPanelTitles[panelCls]
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
                    .Name('control {}'.format(panel.__class__.__name__)))
                    
        self._auimgr.AddPane(panel, paneInfo)
        self._auimgr.Update()

        self._controlPanels.add(panelCls)

        def onDestroy(ev):
            ev.Skip()

            # this method seems to be called when children of the
            # target panel are destroyed, and we don't want that.
            # So we'll just double check to make sure it is *this*
            # panel which is being destroyed.
            if ev.GetEventObject() == panel:
                self._controlPanels.remove(panelCls)

        panel.Bind(wx.EVT_WINDOW_DESTROY, onDestroy)

        
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

                try:    panelType, panelClsName = panel.split()
                except: continue

                if panelType == 'control':
                    panelCls  = getattr(controls, panelClsName)
                    self.addControlPanel(panelCls)

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

        ctrlMenu = wx.Menu()
        menuBar.Append(ctrlMenu, 'Control') 

        self._fileMenu = fileMenu
        self._viewMenu = viewMenu
        self._ctrlMenu = ctrlMenu

        viewPanels = views   .listViewPanels()
        ctrlPanels = controls.listControlPanels()
        actionz    = actions .listActions()

        for action in actionz:
            menuItem = fileMenu.Append(wx.ID_ANY,
                                         strings.actionTitles[action])
            actionObj = action(menuItem, self._imageList, self._displayCtx)
            
            self.Bind(wx.EVT_MENU,
                      lambda ev, ao=actionObj: ao.doAction(),
                      menuItem)

        for viewPanel in viewPanels:
            viewAction = viewMenu.Append(wx.ID_ANY,
                                         strings.viewPanelTitles[viewPanel]) 
            self.Bind(wx.EVT_MENU,
                      lambda ev, vp=viewPanel: self.addViewPanel(vp),
                      viewAction)

        for ctrlPanel in ctrlPanels:
            ctrlAction = ctrlMenu.Append(wx.ID_ANY,
                                         strings.controlPanelTitles[ctrlPanel]) 
            self.Bind(wx.EVT_MENU,
                      lambda ev, cp=ctrlPanel: self.addControlPanel(cp),
                      ctrlAction)
