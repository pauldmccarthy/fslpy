#!/usr/bin/env python
#
# fslviewframe.py - A wx.Frame which implements a 3D image viewer.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""A 3D image viewer.

This module provides the :class:`FSLViewFrame` which is the top level frame
for the FSLView application, providing functionality to view 3D/4D images,
and other types of data.

The application logic is spread across several sub-packages:

 - :mod:`actions`        - Global actions (e.g. load file), and abstract base
                           classes for other actions, and entities which 
                           provide actions.

 - :mod:`controls`       - GUI panels which provide an interface to control 
                           the display of a single view.

 - :mod:`displaycontext` - Classes which define options controlling the
                           display.

 - :mod:`editor`         - Image editing functionality.

 - :mod:`gl`             - OpenGL visualisation logic.

 - :mod:`profiles`       - Mouse/keyboard interaction profiles.

 - :mod:`views`          - GUI panels which display image data.

 - :mod:`widgets`        - General purpose custom :mod:`wx` widgets.


A :class:`FSLViewFrame` is a container for one or more 'views' - all of the
possible views are contained within the :mod:`.views` sub-package, and the
views which may be opened by the user are defined by the
:func:`.views.listViewPanels` function. View panels may contain one or more
'control' panels (all defined in the :mod:`.controls` sub-package), which
provide an interface allowing the user to control the view.


All view (and control) panels are derived from the :class:`.FSLViewPanel`
which, in turn, is derived from the :class:`.ActionProvider` class.
As such, view panels may expose both actions, and properties, which can be
performed or modified by the user.
"""


import logging

import wx
import wx.aui as aui

import fsl.data.strings   as strings
import fsl.utils.settings as fslsettings

import views
import actions
import displaycontext


log = logging.getLogger(__name__)


class FSLViewFrame(wx.Frame):
    """A frame which implements a 3D image viewer."""

    def __init__(self,
                 parent,
                 overlayList,
                 displayCtx,
                 restore=True):
        """
        :arg parent:
        
        :arg overlayList:
        
        :arg displayCtx:
        
        :arg restore:    Restores previous saved layout (not currently
                         implemented). If ``False``, no view panels will
                         be displayed.
        """
        
        wx.Frame.__init__(self, parent, title='FSLView')

        # Default application font - this is
        # inherited by all child controls.
        font = self.GetFont()

        if wx.Platform == '__WXGTK__': font.SetPointSize(8)
        else:                          font.SetPointSize(10)
        font.SetWeight(wx.FONTWEIGHT_LIGHT)
        self.SetFont(font)
        
        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx

        self.__centrePane = aui.AuiNotebook(
            self,
            style=aui.AUI_NB_TOP | 
            aui.AUI_NB_TAB_SPLIT | 
            aui.AUI_NB_TAB_MOVE |
            aui.AUI_NB_CLOSE_ON_ALL_TABS)

        # Keeping track of all
        # open view panels
        self.__viewPanels      = []
        self.__viewPanelDCs    = {}
        self.__viewPanelTitles = {}
        self.__viewPanelMenus  = {}
        self.__viewPanelCount  = 0

        self.__makeMenuBar()
        self.__restoreState(restore)

        self.__centrePane.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSE,
                               self.__onViewPanelClose)

        self.Bind(wx.EVT_CLOSE, self.__onClose)

        
    def getViewPanels(self):
        """Returns a list of all view panels that currently exist, and a list
        of their titles.
        """
        return (self.__viewPanels,
                [self.__viewPanelTitles[vp] for vp in self.__viewPanels])


    def addViewPanel(self, panelCls):
        """Adds a view panel to the centre of the frame, and a menu item
        allowing the user to configure the view.
        """

        title = '{} {}'.format(
            strings.titles[panelCls],
            self.__viewPanelCount + 1)
        
        childDC = displaycontext.DisplayContext(
            self.__overlayList,
            self.__displayCtx)
        
        panel = panelCls(
            self.__centrePane,
            self.__overlayList,
            childDC)

        log.debug('Created new {} ({}) with DisplayContext {}'.format(
            panelCls.__name__,
            id(panel),
            id(childDC)))

        self.__viewPanelCount = self.__viewPanelCount + 1

        self.__viewPanels.append(panel)
        self.__viewPanelTitles[panel] = title
        self.__viewPanelDCs[   panel] = childDC
        
        self.__centrePane.AddPage(panel, title, True)
        self.__centrePane.Split(
            self.__centrePane.GetPageIndex(panel),
            wx.RIGHT)

        self.__addViewPanelMenu(panel, title)


    def __addViewPanelMenu(self, panel, title):

        actionz = panel.getActions()

        if len(actionz) == 0:
            return

        menuBar = self.GetMenuBar()
        menu    = wx.Menu()
        menuBar.Append(menu, title)

        self.__viewPanelMenus[panel] = menu

        for actionName, actionObj in actionz.items():
            
            menuItem = menu.Append(
                wx.ID_ANY,
                strings.actions[panel, actionName])
            actionObj.bindToWidget(self, wx.EVT_MENU, menuItem)
    

    def __onViewPanelClose(self, ev):

        ev.Skip()
        
        pageIdx = ev.GetSelection()
        panel   = self.__centrePane.GetPage(pageIdx)

        if panel not in self.__viewPanels:
            return

        self.__viewPanels             .remove(panel)
        self.__viewPanelMenus         .pop(   panel, None)
        title = self.__viewPanelTitles.pop(   panel)
        dctx  = self.__viewPanelDCs   .pop(   panel)

        log.debug('Destroying {} (title {}, id {}) and '
                  'associated DisplayContext ({})'.format(
                      type(panel).__name__,
                      title,
                      id(panel),
                      id(dctx)))

        # Unbind view panel menu
        # items, and remove the menu
        for actionName, actionObj in panel.getActions().items():
            actionObj.unbindAllWidgets()

        menuBar = self.GetMenuBar()
        menuIdx = menuBar.FindMenu(title)
        if menuIdx != wx.NOT_FOUND:
            menuBar.Remove(menuIdx)

        # Calling fslpanel.FSLViewPanel.destroy()
        # and DisplayContext.destroy() - the
        # AUINotebook should do the
        # wx.Window.Destroy side of things ...
        panel.destroy()
        dctx .destroy()

        
    def __onClose(self, ev):
        """Called on requests to close this :class:`FSLViewFrame`.

        Saves the frame position, size, and layout, so it may be preserved the
        next time it is opened. See the :meth:`_restoreState` method.
        """

        ev.Skip()

        size     = self.GetSize().Get()
        position = self.GetScreenPosition().Get()

        fslsettings.write('framesize',     str(size))
        fslsettings.write('frameposition', str(position))

        # It's nice to explicitly clean
        # up our FSLViewPanels, otherwise
        # they'll probably complain
        for panel in self.__viewPanels:
            panel.destroy()

        
    def __parseSavedSize(self, size):
        """Parses the given string, which is assumed to contain a size tuple.
        """
        
        try:    return tuple(map(int, size[1:-1].split(',')))
        except: return None

        
    __parseSavedPoint = __parseSavedSize
    """A proxy for the :meth:`__parseSavedSize` method.
    """ 

            
    def __parseSavedLayout(self, layout):
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

        
    def __restoreState(self, restore=True):
        """Called on :meth:`__init__`. If any frame size/layout properties
        have previously been saved, they are applied to this frame.

        :arg bool default: If ``True``, any saved state is ignored.
        """

        from operator import itemgetter as iget

        # Restore the saved frame size/position
        size     = self.__parseSavedSize(
            fslsettings.read('framesize'))
        position = self.__parseSavedPoint(
            fslsettings.read('frameposition'))        

        if (size is not None) and (position is not None):

            # Turn the saved size/pos into
            # a (tlx, tly, brx, bry) tuple
            frameRect = [position[0],
                         position[1],
                         position[0] + size[0],
                         position[1] + size[1]]

            # Now make a bounding box containing the
            # space made up of all available displays.
            # Get the bounding rectangles of each 
            # display, and change them from
            # (x, y, w, h) into (tlx, tly, brx, bry).
            displays  = [wx.Display(i)   for i in range(wx.Display.GetCount())]
            dispRects = [d.GetGeometry() for d in displays]
            dispRects = [[d.GetTopLeft()[    0],
                          d.GetTopLeft()[    1],
                          d.GetBottomRight()[0],
                          d.GetBottomRight()[1]] for d in dispRects]

            # get the union of these display
            # rectangles (tlx, tly, brx, bry)
            dispRect = [min(dispRects, key=iget(0))[0],
                        min(dispRects, key=iget(1))[1],
                        max(dispRects, key=iget(2))[2],
                        max(dispRects, key=iget(3))[3]]

            # Now we have our two rectangles - the
            # rectangle of our saved frame position,
            # and the rectangle of the available
            # display space.

            # Calculate the area of intersection
            # betwen the two rectangles, and the
            # area of our saved frame position
            xOverlap  = max(0, min(frameRect[2], dispRect[2]) -
                               max(frameRect[0], dispRect[0]))
            yOverlap  = max(0, min(frameRect[3], dispRect[3]) -
                               max(frameRect[1], dispRect[1]))

            intArea   = xOverlap * yOverlap
            frameArea = ((frameRect[2] - frameRect[0]) *
                         (frameRect[3] - frameRect[1]))

            # If the ratio of (frame-display intersection) to
            # (saved frame position) is 'not decent', then 
            # forget it, and use a default frame position/size
            ratio = intArea / float(frameArea)
            if ratio < 0.5:

                log.debug('Intersection of saved frame area with available '
                          'display area is too small ({}) - reverting to '
                          'default frame size/position'.format(ratio))
                
                size     = None
                position = None

        if size is not None:
            log.debug('Restoring previous size: {}'.format(size))
            self.SetSize(size)
            
        else:
            
            # Default size is 90% of
            # the first display size
            size     = list(wx.Display(0).GetGeometry().GetSize())
            size[0] *= 0.9
            size[1] *= 0.9
            log.debug('Setting default frame size: {}'.format(size))
            self.SetSize(size)

        if position is not None:
            log.debug('Restoring previous position: {}'.format(position))
            self.SetPosition(position)
        else:
            self.Centre()

        # TODO Restore the previous view panel layout
        if restore:

            self.addViewPanel(views.OrthoPanel)

            viewPanel = self.getViewPanels()[0][0]

            # Set up a default for ortho views
            # layout (this will hopefully eventually
            # be restored from a saved state)
            import fsl.fslview.controls.overlaylistpanel      as olp
            import fsl.fslview.controls.locationpanel         as lop
            import fsl.fslview.controls.overlaydisplaytoolbar as odt
            import fsl.fslview.controls.orthotoolbar          as ot

            viewPanel.togglePanel(olp.OverlayListPanel)
            viewPanel.togglePanel(lop.LocationPanel)
            viewPanel.togglePanel(odt.OverlayDisplayToolBar, False, viewPanel)
            viewPanel.togglePanel(ot .OrthoToolBar,          False, viewPanel) 

            
    def __makeMenuBar(self):
        """Constructs a bunch of menu items for this :class:`FSLViewFrame`."""

        menuBar = wx.MenuBar()
        self.SetMenuBar(menuBar)

        fileMenu = wx.Menu()
        menuBar.Append(fileMenu, 'File')

        viewMenu = wx.Menu()
        menuBar.Append(viewMenu, 'View')

        self.__fileMenu = fileMenu
        self.__viewMenu = viewMenu

        viewPanels = views   .listViewPanels()
        actionz    = actions .listGlobalActions()

        for action in actionz:
            menuItem = fileMenu.Append(wx.ID_ANY, strings.actions[action])
            
            actionObj = action(self.__overlayList, self.__displayCtx)

            actionObj.bindToWidget(self, wx.EVT_MENU, menuItem)

        for viewPanel in viewPanels:
            viewAction = viewMenu.Append(wx.ID_ANY, strings.titles[viewPanel]) 
            self.Bind(wx.EVT_MENU,
                      lambda ev, vp=viewPanel: self.addViewPanel(vp),
                      viewAction)
