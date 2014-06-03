#!/usr/bin/env python
#
# elistbox.py - A wx EditableListBox implementation. The
# wx.gizmos.EditableListBox is buggy under OS X Mavericks,
# and getting tooltips working with the wx.ListBox is an
# absolute pain in the behind. So I felt the need to
# replicate its functionality.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import math
import logging

import wx
import wx.lib.newevent as wxevent

log = logging.getLogger(__name__)


# Event emitted when an item is selected. A ListSelectEvent
# has the following attributes (all are set to None if no
# item was selected):
# 
#   - idx:    index of selected item
#   - label:  label of selected item
#   - data:   client data associated with selected item
#
ListSelectEvent, EVT_ELB_SELECT_EVENT = wxevent.NewEvent()

# Event emitted when the 'add item' button is pushed. A
# ListAddEvent has the following attributes (all are set
# to None if no item was selected):
#
#   - idx:    index of selected item
#   - label:  label of selected item
#   - data:   client data associated with selected item
#
ListAddEvent,    EVT_ELB_ADD_EVENT    = wxevent.NewEvent()

# Event emitted when the 'remove item' button is pushed. A
# ListAddEvent has the following attributes:
#
#   - idx:    index of selected item
#   - label:  label of selected item
#   - data:   client data associated with selected item
#
ListRemoveEvent, EVT_ELB_REMOVE_EVENT = wxevent.NewEvent()

# Event emitted when one of the 'move up'/'move down'
# buttons is pushed. A ListAddEvent has the following
# attributes:
#
#   - oldIdx: index of item before move
#   - newIdx: index of item after move
#   - label:  label of moved item
#   - data:   client data associated with moved item
# 
ListMoveEvent,   EVT_ELB_MOVE_EVENT   = wxevent.NewEvent()


# Do not allow new items to be added.
ELB_NO_ADD    = 1

# Do not allow items to be removed.
ELB_NO_REMOVE = 2

# Do not allow items to be reordered.
ELB_NO_MOVE   = 4

# The first item in the list (index 0) is shown
# at the botom, and the last item at the top.
ELB_REVERSE   = 8

# Client data is used as a tooltip popup on
# mouse-over.
ELB_TOOLTIP   = 16


class _ListItem(object):
    def __init__(self, label, data, widget):
        self.label  = label
        self.data   = data
        self.widget = widget


class EditableListBox(wx.Panel):
    """
    An EditableListBox contains a ListBox containing some items,
    and a strip of buttons for modifying said items.

    Some rudimentary wrapper methods for modifying the list contents
    are provided by this EditableListBox object, and the underlying
    wx.ListBox is accessible through an attribute called 'listBox'.
    But beware of accessing the listBox object directly if you are
    using ELB_REVERSE, as you will need to manually invert the list
    indices.
    
    Parameters:
    
      - parent:     wx parent object
      - labels:     list of strings, the items in the list
      - clientData: list of data associated with the list items.
      - style:      Style bitmask - accepts ELB_NO_ADD, ELB_NO_REMOVE,
                    ELB_NO_MOVE, ELB_REVERSE, and ELB_TOOLTIP.
    """

    _selectedBG = '#7777FF'
    _defaultBG  = '#FFFFFF'

    
    def __init__(
            self,
            parent,
            labels,
            clientData=None,
            style=0):

        wx.Panel.__init__(self, parent)

        reverseOrder  =      style & ELB_REVERSE
        addSupport    = not (style & ELB_NO_ADD)
        removeSupport = not (style & ELB_NO_REMOVE)
        moveSupport   = not (style & ELB_NO_MOVE)
        showTooltips  =      style & ELB_TOOLTIP
        noButtons     = not any((addSupport, removeSupport, moveSupport))

        self._reverseOrder = reverseOrder
        self._showTooltips = showTooltips

        if clientData is None: clientData = [None] * len(labels)

        # index of the currently selected item
        self._selection  = wx.NOT_FOUND
        self._listItems  = []

        # the panel containing the list items
        self._listPanel = wx.Panel(self)
        self._listSizer = wx.BoxSizer(wx.VERTICAL)
        self._listPanel.SetSizer(self._listSizer)
        self._listPanel.SetBackgroundColour(EditableListBox._defaultBG)

        self._scrollbar = wx.ScrollBar(self, style=wx.SB_VERTICAL)

        # A panel containing buttons for doing stuff with the list
        if not noButtons:
            self._buttonPanel      = wx.Panel(self)
            self._buttonPanelSizer = wx.BoxSizer(wx.VERTICAL)
            self._buttonPanel.SetSizer(self._buttonPanelSizer) 

        # Buttons for moving the selected item up/down
        if moveSupport:
            self._upButton   = wx.Button(self._buttonPanel, label=u'\u25B2',
                                         style=wx.BU_EXACTFIT)
            self._downButton = wx.Button(self._buttonPanel, label=u'\u25BC',
                                         style=wx.BU_EXACTFIT)
            self._upButton  .Bind(wx.EVT_BUTTON, self._moveItemUp)
            self._downButton.Bind(wx.EVT_BUTTON, self._moveItemDown)

            self._buttonPanelSizer.Add(self._upButton,   flag=wx.EXPAND)
            self._buttonPanelSizer.Add(self._downButton, flag=wx.EXPAND) 

        # Button for adding new items
        if addSupport:
            self._addButton = wx.Button(self._buttonPanel, label='+',
                                        style=wx.BU_EXACTFIT)
            self._addButton.Bind(wx.EVT_BUTTON, self._addItem)
            self._buttonPanelSizer.Add(self._addButton, flag=wx.EXPAND) 

        # Button for removing the selected item
        if removeSupport:
            self._removeButton = wx.Button(self._buttonPanel, label='-',
                                           style=wx.BU_EXACTFIT)

            self._removeButton.Bind(wx.EVT_BUTTON, self._removeItem)
            self._buttonPanelSizer.Add(self._removeButton, flag=wx.EXPAND)

        self._sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self._sizer)

        if not noButtons:
            self._sizer.Add(self._buttonPanel, flag=wx.EXPAND)
            
        self._sizer.Add(self._listPanel, flag=wx.EXPAND, proportion=1)
        self._sizer.Add(self._scrollbar, flag=wx.EXPAND)

        def refresh(ev):
            self._updateScrollbar()
            self._drawList()
            ev.Skip()

        self._scrollbar.Bind(wx.EVT_SCROLL, self._drawList)
        self.Bind(wx.EVT_PAINT, refresh)
        self.Bind(wx.EVT_SIZE,  refresh)

        for label, data in zip(labels, clientData):
            self.Append(label, data)

        self._sizer.Layout()

    
    def _drawList(self, ev=None):
        """
        'Draws' the set of items in the list according to the
        current scrollbar thumb position.
        """

        nitems       = len(self._listItems)
        thumbPos     = self._scrollbar.GetThumbPosition()
        itemsPerPage = self._scrollbar.GetPageSize()

        if itemsPerPage >= nitems:
            start = 0
            end   = nitems
        else:
            start = thumbPos
            end   = thumbPos + itemsPerPage

        if end > nitems:

            start = start - (end - nitems)
            end   = nitems

        for i in range(len(self._listItems)):

            if (i < start) or (i >= end):
                self._listSizer.Show(i, False)
            else:
                self._listSizer.Show(i, True)

        self._listSizer.Layout()

        if ev is not None:
            ev.Skip()


    def _updateScrollbar(self, ev=None):
        """
        Updates the scrollbar parameters according to the
        number of items in the list, and the screen size
        of the list panel. If there is enough room to display
        all items in the list, the scroll bar is hidden.
        """

        nitems     = len(self._listItems)
        pageHeight = self._listPanel.GetClientSize().GetHeight()
        
        # Yep, I'm assuming that all
        # items are the same size
        if nitems > 0:
            itemHeight = self._listItems[0].widget.GetSize().GetHeight()
        else:
            itemHeight = 0 
        
        if pageHeight == 0 or itemHeight == 0:
            itemsPerPage = nitems
        else:
            itemsPerPage = math.floor(pageHeight / float(itemHeight))

        thumbPos     = self._scrollbar.GetThumbPosition()
        itemsPerPage = min(itemsPerPage, nitems)

        # Hide the scrollbar if there is enough
        # room to display the entire list (but
        # configure the scrollbar correctly)
        if nitems == 0 or itemsPerPage >= nitems:
            self._scrollbar.SetScrollbar(0,
                                         nitems,
                                         nitems,
                                         nitems,
                                         True)
            self._sizer.Show(self._scrollbar, False)
        else:
            self._sizer.Show(self._scrollbar, True) 
            self._scrollbar.SetScrollbar(thumbPos,
                                         itemsPerPage,
                                         nitems,
                                         itemsPerPage,
                                         True)
        self._sizer.Layout()

        
    def _fixIndex(self, idx):
        """
        If the ELB_REVERSE style is active, this method will return
        an inverted version of the given index. Otherwise it returns
        the index value unchanged.
        """

        if idx is None:               return idx
        if idx == wx.NOT_FOUND:       return idx
        if not self._reverseOrder:    return idx

        fixIdx = len(self._listItems) - idx - 1

        # if len(self_listItems) is passed to Insert
        # (i.e. an item is to be appended to the list)
        # the above formula will produce -1
        if (idx == len(self._listItems)) and (fixIdx == -1):
            fixIdx = 0

        return fixIdx


    def GetCount(self):
        return len(self._listItems)


    def ClearSelection(self):
        for item in self._listItems:
            item.widget.SetBackgroundColour(EditableListBox._defaultBG)
        self._selection = wx.NOT_FOUND

        
    def SetSelection(self, n):

        if n != wx.NOT_FOUND and (n < 0 or n >= len(self._listItems)):
            raise IndexError('Index {} out of bounds'.format(n))

        self.ClearSelection()

        if n == wx.NOT_FOUND: return

        self._selection = self._fixIndex(n)

        widget = self._listItems[self._selection].widget
        widget.SetBackgroundColour(EditableListBox._selectedBG)
        
        
    def GetSelection(self):
        return self._fixIndex(self._selection)

        
    def Insert(self, label, pos, clientData):

        if pos < 0 or pos > self.GetCount():
            raise IndexError('Index {} out of bounds'.format(pos))

        pos = self._fixIndex(pos)

        widget = wx.StaticText(self._listPanel, label=label)
        widget.SetBackgroundColour(EditableListBox._defaultBG)
        
        widget.Bind(wx.EVT_LEFT_DOWN, self._itemClicked)

        item = _ListItem(label, clientData, widget)

        log.debug('Inserting item ({}) at index {}'.format(label, pos))

        self._listItems.insert(pos, item)
        self._listSizer.Insert(pos, widget, flag=wx.EXPAND)
        self._listSizer.Layout()

        # if an item was inserted before the currently
        # selected item, the _selection index will no
        # longer be valid - fix it.
        if self._selection != wx.NOT_FOUND and pos < self._selection:
            self._selection = self._selection + 1

        self._updateScrollbar()
        self.Refresh()

            
    def Append(self, label, clientData):
        self.Insert(label, len(self._listItems), clientData)


    def Delete(self, n):

        n = self._fixIndex(n)

        if n < 0 or n >= len(self._listItems):
            raise IndexError('Index {} out of bounds'.format(n))

        item = self._listItems.pop(n)

        self._listSizer.Remove(n)

        item.widget.Destroy()
        
        self._listSizer.Layout()

        # if the deleted item was selected, clear the selection
        if self._selection == n:
            self.ClearSelection()

        # or if the deleted item was before the
        # selection, fix the selection index
        elif self._selection > n:
            self._selection = self._selection - 1

        self._updateScrollbar()
        self.Refresh()

            
    def _getSelection(self, fix=False):
        """
        Returns a 3-tuple containing the (uncorrected) index, label, and
        associated client data of the currently selected list item, or
        (None, None, None) if no item is selected. 
        """
        
        idx   = self._selection
        label = None
        data  = None

        if idx == wx.NOT_FOUND:
            idx = None
        else:
            label = self._listItems[idx].label
            data  = self._listItems[idx].data

        if fix:
            idx = self._fixIndex(idx)

        return idx, label, data
        
        
    def _itemClicked(self, ev):
        """
        Called when an item in the list is clicked. Selects the item and
        posts an EVT_ELB_SELECT_EVENT.
        """

        widget  = ev.GetEventObject()
        itemIdx = -1

        for i, listItem in enumerate(self._listItems):
            if listItem.widget == widget:
                itemIdx = i
                break

        if itemIdx == -1:
            return

        self.SetSelection(self._fixIndex(itemIdx))
        
        idx, label, data = self._getSelection(True)
        
        log.debug('ListSelectEvent (idx: {}; label: {})'.format(idx, label))
        
        ev = ListSelectEvent(idx=idx, label=label, data=data)
        wx.PostEvent(self, ev)

        
    def _moveItem(self, offset):
        """
        Called when the 'move up' or 'move down' buttons are pushed. Moves
        the selected item by the specified offset and posts an
        EVT_ELB_MOVE_EVENT, unless it doesn't make sense to do the move. 
        """

        oldIdx, label, data = self._getSelection()
        
        if oldIdx is None: return
        
        newIdx = oldIdx + offset

        # the selected item is at the top/bottom of the list.
        if oldIdx < 0 or oldIdx >= self.GetCount(): return
        if newIdx < 0 or newIdx >= self.GetCount(): return

        widget = self._listSizer.GetItem(oldIdx).GetWindow()

        self._listItems.insert(newIdx, self._listItems.pop(oldIdx))

        self._listSizer.Detach(oldIdx) 
        self._listSizer.Insert(newIdx, widget, flag=wx.EXPAND)

        oldIdx = self._fixIndex(oldIdx)
        newIdx = self._fixIndex(newIdx)

        self.SetSelection(newIdx)

        self._listSizer.Layout()

        log.debug('ListMoveEvent (oldIdx: {}; newIdx: {}; label: {})'.format(
            oldIdx, newIdx, label))
        
        ev = ListMoveEvent(
            oldIdx=oldIdx, newIdx=newIdx, label=label, data=data)
        wx.PostEvent(self, ev)

        
    def _moveItemDown(self, ev):
        """
        Called when the 'move down' button is pushed. Calls the _moveItem
        method.
        """
        self._moveItem(1)

        
    def _moveItemUp(self, ev):
        """
        Called when the 'move up' button is pushed. Calls the _moveItem
        method.
        """ 
        self._moveItem(-1) 

        
    def _addItem(self, ev):
        """
        Called when the 'add item' button is pushed. Does nothing but post an
        EVT_ELB_ADD_EVENT - it is up to a registered handler to implement the
        functionality of adding an item to the list.
        """

        idx, label, data = self._getSelection(True)

        log.debug('ListAddEvent (idx: {}; label: {})'.format(idx, label)) 

        ev = ListAddEvent(idx=idx, label=label, data=data)
        
        wx.PostEvent(self, ev)

        
    def _removeItem(self, ev):
        """
        Called when the 'remove item' button is pushed. Removes the selected
        item from the list, and posts an EVT_ELB_REMOVE_EVENT.
        """

        idx, label, data = self._getSelection(True)

        if idx is None: return

        self.Delete(idx)

        if self.GetCount() > 0:
            if idx == self.GetCount():
                self.SetSelection(idx - 1)
            else:
                self.SetSelection(idx)

        log.debug('ListRemoveEvent (idx: {}; label: {})'.format(idx, label)) 

        ev = ListRemoveEvent(idx=idx, label=label, data=data)
        
        wx.PostEvent(self, ev)


def main():
    """
    Little testing application.
    """

    import random

    logging.basicConfig(
        format='%(levelname)8s '
               '%(filename)20s '
               '%(lineno)4d: '
               '%(funcName)s - '
               '%(message)s',
        level=logging.DEBUG)

    items   = map(str, range(5))

    app     = wx.App()
    frame   = wx.Frame(None)
    panel   = wx.Panel(frame)
    listbox = EditableListBox(panel, items, style=ELB_REVERSE)

    panelSizer = wx.BoxSizer(wx.HORIZONTAL)
    panel.SetSizer(panelSizer)
    panelSizer.Add(listbox, flag=wx.EXPAND, proportion=1)

    frameSizer = wx.BoxSizer(wx.HORIZONTAL)
    frame.SetSizer(frameSizer)
    frameSizer.Add(panel, flag=wx.EXPAND, proportion=1) 

    frame.Show()


    def addItem(ev):
        listbox.Append(str(random.randint(100, 200)), None)

    listbox.Bind(EVT_ELB_ADD_EVENT, addItem)
    
    
    app.MainLoop()

    
if __name__ == '__main__':
    main()
