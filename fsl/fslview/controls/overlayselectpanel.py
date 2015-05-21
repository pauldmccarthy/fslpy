#!/usr/bin/env python
#
# overlayselectpanel.py - A little panel which allows the currently selected
# overlay to be changed.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Defines the :class:`OverlaySelectPanel` which is a little panel that allows
the currently selected overlay to be changed.

This panel is generally embedded within other control panels.
"""

import logging

import wx

import fsl.fslview.panel as fslpanel

log = logging.getLogger(__name__)


class OverlaySelectPanel(fslpanel.FSLViewPanel):
    """A panel which displays the currently selected overlay,
    and allows it to be changed.
    """

    def __init__(self, parent, overlayList, displayCtx, showName=True):

        fslpanel.FSLViewPanel.__init__(self, parent, overlayList, displayCtx)

        self.showName = showName

        # A button to select the previous image
        self._prevButton = wx.Button(self, label=u'\u25C0',
                                     style=wx.BU_EXACTFIT)
        
        # A button selecting the next image
        self._nextButton = wx.Button(self, label=u'\u25B6',
                                     style=wx.BU_EXACTFIT)

        self._sizer  = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self._sizer)

        self._sizer.Add(self._prevButton, flag=wx.EXPAND)
        self._sizer.Add(self._nextButton, flag=wx.EXPAND)

        # bind callbacks for next/prev buttons
        self._nextButton.Bind(wx.EVT_BUTTON, self._onNextButton)
        self._prevButton.Bind(wx.EVT_BUTTON, self._onPrevButton)

        # A label showing the name of the current overlay
        if not showName:
            self._overlayLabel = None
        else:
            self._overlayLabel = wx.StaticText(self,
                                               style=wx.ALIGN_CENTRE |
                                               wx.ST_ELLIPSIZE_MIDDLE)

            self._sizer.Insert(1,
                               self._overlayLabel,
                               flag=wx.EXPAND,
                               proportion=1)

            # Make the image name label font a bit smaller
            font = self._overlayLabel.GetFont()
            font.SetPointSize(font.GetPointSize() - 2)
            font.SetWeight(wx.FONTWEIGHT_LIGHT)
            self._overlayLabel.SetFont(font)
        
        self._overlayList.addListener(
            'overlays',
            self._name,
            self._overlayListChanged)
        self._displayCtx.addListener(
            'selectedOverlay',
            self._name,
            self._selectedOverlayChanged)

        self._overlayListChanged()

        self.Layout()
        self.SetMinSize(self._sizer.GetMinSize())


    def destroy(self):
        fslpanel.FSLViewPanel.destroy(self)

        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)

        # the _overlayListChanged method registers
        # a listener on the name of each overlay
        for overlay in self._overlayList:
            display = self._displayCtx.getDisplay(overlay)
            display.removeListener('name', self._name)
 
        
    def _onPrevButton(self, ev):
        """Called when the previous button is pushed. Selects the previous
        overlay.
        """
        allOverlays = self._displayCtx.getOrderedOverlays()
        currOverlay = self._displayCtx.getSelectedOverlay()
        currIdx     = allOverlays.index(currOverlay)

        if currIdx == 0:
            return

        self._displayCtx.selectOverlay(allOverlays[currIdx - 1])

        
    def _onNextButton(self, ev):
        """Called when the previous button is pushed. Selects the next
        overlay.
        """
        allOverlays = self._displayCtx.getOrderedOverlays()
        currOverlay = self._displayCtx.getSelectedOverlay()
        currIdx     = allOverlays.index(currOverlay)

        if currIdx == len(allOverlays) - 1:
            return

        self._displayCtx.selectOverlay(allOverlays[currIdx + 1]) 


    def _overlayListChanged(self, *a):
        """Called when the :class:`.OverlayList.overlays` list changes.

        Ensures that the currently selected overlay is displayed on the panel,
        and that listeners are registered on the name property for each
        overlay.
        """

        def nameChanged(value, valid, display, name):

            ovl = display.getOverlay()
            idx = self._overlayList.index(ovl)
            
            # if the name of the currently selected overlay has changed,
            # make sure that this panel updates to reflect the change
            if idx == self._displayCtx.selectedOverlay:
                self._selectedOverlayChanged()

        if self._overlayLabel is not None:
            for overlay in self._overlayList:
                display = self._displayCtx.getDisplay(overlay)
                display.addListener('name',
                                    self._name,
                                    nameChanged,
                                    overwrite=True)

        self._selectedOverlayChanged()

        
    def _selectedOverlayChanged(self, *a):
        """Called when the selected overlay is changed. Updates the overlay
        name label.
        """

        allOverlays = self._displayCtx.getOrderedOverlays()
        overlay     = self._displayCtx.getSelectedOverlay()
        novls       = len(allOverlays)
        
        if novls > 0: idx = allOverlays.index(overlay)
        else:         idx = -1

        self._prevButton.Enable(novls > 0 and idx > 0)
        self._nextButton.Enable(novls > 0 and idx < novls - 1)

        if self._overlayLabel is None:
            return

        if novls == 0:
            self._overlayLabel.SetLabel('')
            return

        display = self._displayCtx.getDisplay(overlay)
        name    = display.name
        
        if name is None: name = ''
        self._overlayLabel.SetLabel('{}'.format(name))

        self.Layout()
        self.Refresh() 
