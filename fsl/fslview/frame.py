#!/usr/bin/env python
#
# fslviewframe.py - A wx.Frame which implements a 3D image viewer.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""A 3D image viewer.

This module provides the :class:`FSLViewFrame` which is the top level frame
for the FSLView application, providing functionality to view 3D/4D MR images.

The application logic is spread across several sub-packages:

 - :mod:`actions`   - Global actions (e.g. load file), and abstract base
                      classes for other actions, and entities which provide
                      actions.

 - :mod:`controls`  - GUI panels which provide an interface to control the
                      display of a single view.

 - :mod:`views`     - GUI panels which display image data.

 - :mod:`gl`        - OpenGL visualisation logic.

 - :mod:`profiles`  - Mouse/keyboard interaction profiles.

 - :mod:`editor`    - Image editing functionality.

 - :mod:`widgets`   - General purpose custom :mod:`wx` widgets.


A :class:`FSLViewFrame` is a container for one or more 'views' - all of the
possible views are contained within the :mod:`views` sub-package, and the are
defined by the :func:`views.listViewPanels` function. View panels may contain
one or more 'control' panels (all defined in the :mod:controls` sub-package),
which provide an interface allowing the user to control the view.


All view (and control) panels are derived from the :class:`panel.FSLViewPanel`
which, in turn, is derived from the :class:`actions.ActionProvider` class.
As such, view panels may expose both actions, and properties, which can be
performed or modified by the user.
"""

import logging
log = logging.getLogger(__name__)

import wx
import wx.aui as aui

import views
import actions
import strings
import displaycontext


class FSLViewFrame(wx.Frame):
    """A frame which implements a 3D image viewer."""

    def __init__(self,
                 parent,
                 imageList,
                 displayCtx,
                 default=False):
        """
        :arg parent:
        
        :arg imageList:
        
        :arg displayCtx:
        
        :arg default:
        """
        
        wx.Frame.__init__(self, parent, title='FSLView')
        
        self._imageList  = imageList
        self._displayCtx = displayCtx

        self._centrePane = aui.AuiNotebook(
            self,
            style=aui.AUI_NB_TOP | 
            aui.AUI_NB_TAB_SPLIT | 
            aui.AUI_NB_TAB_MOVE |
            aui.AUI_NB_CLOSE_ON_ALL_TABS)

        # we can have as many view
        # panels as we like
        self._viewPanels      = []
        self._viewPanelTitles = {}
        self._viewPanelCount  = 0

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

        title   = strings.viewPanelTitles[panelCls]
        childDC = displaycontext.DisplayContext(self._imageList,
                                                self._displayCtx)
        panel   = panelCls(self._centrePane,
                           self._imageList,
                           childDC) 

        self._viewPanelCount = self._viewPanelCount + 1

        self._viewPanels.append(panel)
        self._viewPanelTitles[id(panel)] = title
        self._centrePane.AddPage(panel, title, True)
        self._centrePane.Split(
            self._centrePane.GetPageIndex(panel),
            wx.RIGHT)

        
    def _onClose(self, ev):
        """Called on requests to close this :class:`FSLViewFrame`.

        Saves the frame position, size, and layout, so it may be preserved the
        next time it is opened. See the :meth:`_restoreState` method.
        """

        ev.Skip()

        config = wx.Config('FSLView')

        size     = self.GetSize().Get()
        position = self.GetScreenPosition().Get()

        log.debug('Saving size: {}'    .format(str(size)))
        log.debug('Saving position: {}'.format(str(position)))

        config.Write('size',     str(size))
        config.Write('position', str(position))

        
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
        
        size     = None
        position = None

        if not default:
            config   = wx.Config('FSLView')
            size     = self._parseSavedSize(  config.Read('size'))
            position = self._parseSavedPoint( config.Read('position'))

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

        viewPanels = views   .listViewPanels()
        actionz    = actions .listGlobalActions()

        for action in actionz:
            menuItem = fileMenu.Append(wx.ID_ANY,
                                         strings.actionTitles[action])
            
            actionObj = action(self._imageList, self._displayCtx)

            actionObj.bindToWidget(self, wx.EVT_MENU, menuItem)
            

        for viewPanel in viewPanels:
            viewAction = viewMenu.Append(wx.ID_ANY,
                                         strings.viewPanelTitles[viewPanel]) 
            self.Bind(wx.EVT_MENU,
                      lambda ev, vp=viewPanel: self.addViewPanel(vp),
                      viewAction)
