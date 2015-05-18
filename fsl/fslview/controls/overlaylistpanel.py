#!/usr/bin/env python
#
# overlaylistpanel.py - A panel which displays a list of overlays in the 
# overlay list.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""A panel which displays a list of overlays in the overlay list (see and
allows the user to add/remove overlays, and to change their order.
"""

import logging

import wx

import props

import pwidgets.elistbox as elistbox

import fsl.fslview.panel as fslpanel
import fsl.data.image    as fslimage


log = logging.getLogger(__name__)


class ListItemWidget(wx.Panel):

    _enabledFG  = '#000000'
    _disabledFG = '#CCCCCC'

    def __init__(self, parent, overlay, display, listBox):
        wx.Panel.__init__(self, parent)

        self.overlay = overlay
        self.display = display
        self.listBox = listBox
        self.name    = '{}_{}'.format(self.__class__.__name__, id(self))

        self.saveButton = wx.Button(self, label='S', style=wx.BU_EXACTFIT)
        self.visibility = props.makeWidget(self, display, 'enabled')

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.SetSizer(self.sizer)

        self.sizer.Add(self.saveButton, flag=wx.EXPAND, proportion=1)
        self.sizer.Add(self.visibility, flag=wx.EXPAND, proportion=1)

        self.display.addListener('enabled', self.name, self._vizChanged)

        if isinstance(overlay, fslimage.Image):
            self.overlay.addListener('saved',
                                     self.name,
                                     self._saveStateChanged)
        else:
            log.warn('No save button support for non-volumetric overlays')
            self.saveButton.Enable(False)

        self.saveButton.Bind(wx.EVT_BUTTON, self._onSaveButton)

        self.Bind(wx.EVT_WINDOW_DESTROY, self._onDestroy)

        self._vizChanged()
        self._saveStateChanged()

        
    def _onSaveButton(self, ev):
        self.overlay.save()

        
    def _onDestroy(self, ev):
        ev.Skip()
        if ev.GetEventObject() is not self:
            return

        self.display.removeListener('enabled', self.name)

        if isinstance(self.overlay, fslimage.Image):
            self.overlay.removeListener('saved', self.name)

        
    def _saveStateChanged(self, *a):

        if not isinstance(self.overlay, fslimage.Image):
            return
        
        idx = self.listBox.IndexOf(self.overlay)
        
        self.saveButton.Enable(not self.overlay.saved)

        if self.overlay.saved:
            self.listBox.SetItemBackgroundColour(idx)
        else:
            self.listBox.SetItemBackgroundColour(idx, '#ffaaaa', '#aa4444') 

            
    def _vizChanged(self, *a):

        idx = self.listBox.IndexOf(self.overlay)

        if self.display.enabled: fgColour = ListItemWidget._enabledFG
        else:                    fgColour = ListItemWidget._disabledFG

        self.listBox.SetItemForegroundColour(idx, fgColour)


class OverlayListPanel(fslpanel.FSLViewPanel):
    """A :class:`.ControlPanel` which contains an :class:`.EditableListBox`
    displaying the list of loaded overlays.
    
    The list box allows the overlay order to be changed, and allows overlays
    to be added and removed from the list.
    """
    
    def __init__(self, parent, overlayList, displayCtx):
        """Create and lay out an :class:`OverlayListPanel`.

        :param parent:      The :mod:`wx` parent object.
        :param overlayList: An :class:`.OverlayList` instance.
        :param displayCtx:  A :class:`.DisplayContext` instance.
        """
        
        fslpanel.FSLViewPanel.__init__(self, parent, overlayList, displayCtx)

        # list box containing the list of overlays - it 
        # is populated in the _overlayListChanged method
        self._listBox = elistbox.EditableListBox(
            self,
            style=(elistbox.ELB_REVERSE    | 
                   elistbox.ELB_TOOLTIP    | 
                   elistbox.ELB_EDITABLE))

        # listeners for when the user does
        # something with the list box
        self._listBox.Bind(elistbox.EVT_ELB_SELECT_EVENT, self._lbSelect)
        self._listBox.Bind(elistbox.EVT_ELB_MOVE_EVENT,   self._lbMove)
        self._listBox.Bind(elistbox.EVT_ELB_REMOVE_EVENT, self._lbRemove)
        self._listBox.Bind(elistbox.EVT_ELB_ADD_EVENT,    self._lbAdd)
        self._listBox.Bind(elistbox.EVT_ELB_EDIT_EVENT,   self._lbEdit)

        self._sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self._sizer)

        self._sizer.Add(self._listBox, flag=wx.EXPAND, proportion=1)

        self._overlayList.addListener(
            'overlays',
            self._name,
            self._overlayListChanged)
        
        self._displayCtx.addListener(
            'overlayOrder',
            self._name,
            self._overlayListChanged) 

        self._displayCtx.addListener(
            'selectedOverlay',
            self._name,
            self._selectedOverlayChanged)

        self._overlayListChanged()
        self._selectedOverlayChanged()

        self.Layout()

        self.SetMinSize(self._sizer.GetMinSize())


    def destroy(self):
        """Deregisters property listeners."""
        
        fslpanel.FSLViewPanel.destroy(self)

        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._displayCtx .removeListener('overlayOrder',    self._name)

        # A listener on name was added 
        # in the _overlayListChanged method
        for overlay in self._overlayList:
            display = self._displayCtx.getDisplay(overlay)
            display.removeListener('name', self._name)

        
    def _selectedOverlayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.selectedOverlay` property
        changes. Updates the selected item in the list box.
        """

        if len(self._overlayList) > 0:
            self._listBox.SetSelection(
                self._displayCtx.getOverlayOrder(
                    self._displayCtx.selectedOverlay))


    def _overlayNameChanged(self, value, valid, overlay, propName):

        idx     = self._displayCtx.getOverlayOrder(overlay)
        display = self._displayCtx.getDisplay(     overlay)
        name    = display.name
        
        if name is None:
            name = ''
            
        self._listBox.SetString(idx, name) 

        
    def _overlayListChanged(self, *a):
        """Called when the :class:`.OverlayList.overlays` list changes.

        If the change was due to user action on the :class:`.EditableListBox`,
        this method does nothing.  Otherwise, this method updates the
        :class:`.EditableListBox`
        """
        
        self._listBox.Clear()

        for i, overlay in enumerate(self._displayCtx.getOrderedOverlays()):

            display  = self._displayCtx.getDisplay(overlay)
            name     = display.name
            if name is None: name = ''

            tooltip = overlay.dataSource
            
            self._listBox.Append(name, overlay, tooltip)

            widget = ListItemWidget(self, overlay, display, self._listBox)

            self._listBox.SetItemWidget(i, widget)

            display.addListener('name',
                                self._name,
                                self._overlayNameChanged,
                                overwrite=True)

        if len(self._overlayList) > 0:
            self._listBox.SetSelection(
                self._displayCtx.getOverlayOrder(
                    self._displayCtx.selectedOverlay))
        
        
    def _lbMove(self, ev):
        """Called when an overlay is moved in the :class:`.EditableListBox`.
        Reorders the :class:`.OverlayList` to reflect the change.
        """
        self._displayCtx.disableListener('overlayOrder', self._name)
        self._displayCtx.overlayOrder.move(ev.oldIdx, ev.newIdx)
        self._displayCtx.enableListener('overlayOrder', self._name)

        
    def _lbSelect(self, ev):
        """Called when an overlay is selected in the
        :class:`.EditableListBox`. Sets the
        :attr:`.DisplayContext.selectedOverlay` property.
        """
        self._displayCtx.disableListener('selectedOverlay', self._name)
        self._displayCtx.selectedOverlay = \
            self._displayCtx.overlayOrder[ev.idx]
        self._displayCtx.enableListener('selectedOverlay', self._name)

        
    def _lbAdd(self, ev):
        """Called when the 'add' button on the list box is pressed.
        
        Calls the :meth:`.OverlayList.addOverlays` method.
        """
        if self._overlayList.addOverlays():
            self._displayCtx.selectedOverlay = len(self._OverlayList) - 1


    def _lbRemove(self, ev):
        """Called when an item is removed from the overlay listbox.

        Removes the corresponding overlay from the :class:`.OverlayList`.
        """
        self._overlayList.pop(self._displayCtx.overlayOrder[ev.idx])


    def _lbEdit(self, ev):
        """Called when an item label is edited on the overlay list box.
        Sets the corresponding overlay name to the new label.
        """
        idx          = self._displayCtx.overlayOrder[ev.idx]
        overlay      = self._overlayList[idx]
        display      = self._displayCtx.getDisplay(overlay)
        display.name = ev.label
