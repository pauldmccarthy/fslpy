#!/usr/bin/env python
#
# overlaydisplaytoolbar.py - A toolbar which shows display control options for
#                            the currently selected overlay.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>

"""A :class:`wx.Panel` which shows display control options for the currently
selected overlay.
"""

import logging
log = logging.getLogger(__name__)


import fsl.fslview.toolbar as fsltoolbar
import overlaydisplaypanel as overlaydisplay


class OverlayDisplayToolBar(fsltoolbar.FSLViewToolBar):
    
    def __init__(self, parent, overlayList, displayCtx, viewPanel):

        actionz = {'more' : self.showMoreSettings}
        
        fsltoolbar.FSLViewToolBar.__init__(
            self, parent, overlayList, displayCtx, actionz)

        self._viewPanel      = viewPanel
        self._overlayTools   = {}
        self._currentOverlay = None

        self._displayCtx.addListener(
            'selectedOverlay',
            self._name,
            self._selectedOverlayChanged)
        self._overlayList.addListener(
            'overlays',
            self._name,
            self._overlayListChanged) 

        self._selectedOverlayChanged()


    def destroy(self):
        """Deregisters property listeners. """

        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)

        for ovl in self._overlayList:
            
            display = self._displayCtx.getDisplay(ovl)
            display.removeListener('overlayType', self._name)
            display.removeListener('enabled',     self._name)
        fsltoolbar.FSLViewToolBar.destroy(self)


    def showMoreSettings(self, *a):
        self._viewPanel.togglePanel(overlaydisplay.OverlayDisplayPanel, True)


    def _overlayListChanged(self, *a):

        for ovl in self._overlayTools.keys():
            if ovl not in self._overlayList:

                dispTools, optsTools = self._overlayTools.pop(ovl)

                log.debug('Destroying all tools for {}'.format(ovl))

                if ovl is self._currentOverlay:
                    self.ClearTools()

                for tool, _ in dispTools: tool.Destroy()
                for tool, _ in optsTools: tool.Destroy()

        self._selectedOverlayChanged()
    

    def _overlayTypeChanged(self, value, valid, display, name, refresh=True):

        overlay = display.getOverlay()

        dispTools, oldOptsTools = self._overlayTools[overlay]

        newOptsTools = self._makeOptsWidgets(overlay, self)

        self._overlayTools[overlay] = (dispTools, newOptsTools)

        if refresh and (overlay is self._displayCtx.getSelectedOverlay()):
            self._refreshTools(overlay)

        log.debug('Destroying opts tools for {}'.format(overlay))

        for tool, _ in oldOptsTools:
            tool.Destroy()

            
    def _toggleEnabled(self, value, valid, ovl, name):
        
        if ovl is not self._displayCtx.getSelectedOverlay():
            return
        
        display = self._displayCtx.getDisplay(ovl)

        self.Enable(display.enabled)
            

    def _selectedOverlayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.selectedOverlay`
        index changes. Ensures that the correct display panel is visible.
        """

        overlay = self._displayCtx.getSelectedOverlay()

        if overlay is None:
            self.ClearTools()
            return

        display = self._displayCtx.getDisplay(overlay)

        # Call _toggleEnabled when
        # the overlay is enabled/disabled
        self.Enable(display.enabled)
        for ovl in self._overlayList:
            
            d = self._displayCtx.getDisplay(ovl)
            
            if ovl == overlay:
                d.addListener('enabled',
                              self._name,
                              self._toggleEnabled,
                              overwrite=True)
            else:
                d.removeListener('enabled', self._name)

        # Build/refresh the toolbar widgets for this overlay
        tools = self._overlayTools.get(overlay, None)
 
        if tools is None:
            displayTools = self._makeDisplayWidgets(overlay, self)
            optsTools    = self._makeOptsWidgets(   overlay, self)
            
            self._overlayTools[overlay] = (displayTools, optsTools)

            display.addListener(
                'overlayType',
                self._name,
                self._overlayTypeChanged,
                overwrite=True)

        self._refreshTools(overlay)


    def _refreshTools(self, overlay):

        self._currentOverlay = overlay

        log.debug('Showing tools for {}'.format(overlay))

        tools = self.GetTools()
        for widget in tools:
            widget.Show(False)
                
        self.ClearTools(postevent=False)

        if overlay is None:
            self.Layout()

        dispTools, optsTools = self._overlayTools[overlay]

        dispTools, dispLabels = zip(*dispTools)
        optsTools, optsLabels = zip(*optsTools)
        
        tools  = list(dispTools)  + list(optsTools)
        labels = list(dispLabels) + list(optsLabels)

        for tool in tools:
            tool.Show(True) 

        self.SetTools(tools, labels)

        
    def _makeDisplayWidgets(self, overlay, parent):
        """Creates and returns panel containing widgets allowing
        the user to edit the display properties of the given
        overlay object. 
        """

        import fsl.fslview.layouts as layouts

        display   = self._displayCtx.getDisplay(overlay)
        toolSpecs = layouts.layouts[self, display]

        log.debug('Creating display tools for {}'.format(overlay))
        
        return self.GenerateTools(toolSpecs, display, add=False)

    
    def _makeOptsWidgets(self, overlay, parent):

        import fsl.fslview.layouts as layouts

        opts      = self._displayCtx.getOpts(overlay)
        toolSpecs = layouts.layouts[self, opts]
        targets   = { s.key : self if s.key == 'more' else opts
                      for s in toolSpecs}
        
        log.debug('Creating options tools for {}'.format(overlay))

        return self.GenerateTools(toolSpecs, targets, add=False) 
