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

import logging

import wx
import wx.lib.newevent as wxevent

log = logging.getLogger(__name__)


# Event emitted when an item is selected. A ListSelectEvent
# has the following attributes (all are set to None if no
# item was selected):
# 
#   - idx:    index of selected item
#   - choice: label of selected item
#   - data:   client data associated with selected item
#
ListSelectEvent, EVT_ELB_SELECT_EVENT = wxevent.NewEvent()

# Event emitted when the 'add item' button is pushed. A
# ListAddEvent has the following attributes (all are set
# to None if no item was selected):
#
#   - idx:    index of selected item
#   - choice: label of selected item
#   - data:   client data associated with selected item
#
ListAddEvent,    EVT_ELB_ADD_EVENT    = wxevent.NewEvent()

# Event emitted when the 'remove item' button is pushed. A
# ListAddEvent has the following attributes:
#
#   - idx:    index of selected item
#   - choice: label of selected item
#   - data:   client data associated with selected item
#
ListRemoveEvent, EVT_ELB_REMOVE_EVENT = wxevent.NewEvent()

# Event emitted when one of the 'move up'/'move down'
# buttons is pushed. A ListAddEvent has the following
# attributes:
#
#   - oldIdx: index of item before move
#   - newIdx: index of item after move
#   - choice: label of moved item
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
      - choices:    list of strings, the items in the list
      - clientData: list of data associated with the list items.
      - style:      Style bitmask - accepts ELB_NO_ADD, ELB_NO_REMOVE,
                    ELB_NO_MOVE, ELB_REVERSE, and ELB_TOOLTIP.
    """

    _selectedBG = '#7777FF'
    _defaultBG  = '#FFFFFF' 
    
    def __init__(
            self,
            parent,
            choices,
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

        if clientData is None: clientData = [None] * len(choices)

        # index of the currently selected item
        self._selection  = wx.NOT_FOUND
        self._clientData = {}

        # the panel containing the list items
        self._listPanel = wx.Panel(self)
        self._listSizer = wx.BoxSizer(wx.VERTICAL)
        self._listPanel.SetSizer(self._listSizer)

        for choice, data in zip(choices, clientData):
            self.Append(choice, data)

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

        self._sizer.Layout()

        
    def _fixIndex(self, idx):
        """
        If the ELB_REVERSE style is active, this method will return
        an inverted version of the given index. Otherwise it returns
        the index value unchanged.
        """

        if idx is None:            return idx
        if idx == wx.NOT_FOUND:    return idx
        if not self._reverseOrder: return idx
        
        idx = self.GetCount() - idx - 1

        if idx < 0: idx = 0
        
        return idx


    def GetCount(self):
        return self._listSizer.GetItemCount()

        
    def SetSelection(self, n):


        if n != wx.NOT_FOUND and (n < 0 or n >= self.GetCount()):
            raise IndexError('Index {} out of bounds'.format(n))

        # deselect the previous selection, if there is one
        if self._selection != wx.NOT_FOUND:
            widget = self._listSizer.GetItem(self._selection).GetWindow()
            widget.SetBackgroundColour(EditableListBox._defaultBG)
            self._selection = wx.NOT_FOUND

        if n == wx.NOT_FOUND: return

        self._selection = self._fixIndex(n)

        widget = self._listSizer.GetItem(self._selection).GetWindow()
        widget.SetBackgroundColour(EditableListBox._selectedBG)
        
        
    def GetSelection(self):
        return self._fixIndex(self._selection)

        
    def Insert(self, item, pos, clientData):

        if pos < 0 or pos > self.GetCount():
            raise IndexError('Index {} out of bounds'.format(pos))

        pos = self._fixIndex(pos)

        widget = wx.StaticText(self._listPanel, label=item)
        widget.SetBackgroundColour(EditableListBox._defaultBG)

        widget.Bind(wx.EVT_LEFT_DOWN, self._itemClicked)

        self._listSizer.Insert(pos,
                               widget,
                               flag=wx.EXPAND)
        
        self._clientData[id(widget)] = clientData
        self._listSizer.Layout()


    def Append(self, item, clientData):
        self.Insert(item, self.GetCount(), clientData)


    def Delete(self, n):

        n = self._fixIndex(n)

        widget = self._listSizer.GetItem(n).GetWindow()
        self._listSizer.Detach(n)
        self._clientData.pop(id(widget))
        widget.Destroy()
        self._listSizer.Layout()

        if self._selection == n: self.SetSelection(wx.NOT_FOUND)

        
    def _getSelection(self):
        """
        Returns a 3-tuple containing the (uncorrected) index, label, and
        associated client data of the currently selected list item, or
        (None, None, None) if no item is selected. 
        """
        
        idx    = self._selection
        choice = None
        data   = None

        if idx == wx.NOT_FOUND:
            idx = None
        else:
            widget = self._listSizer.GetItem(idx).GetWindow()
            choice = widget.GetLabel()
            data   = self._clientData[id(widget)]

        return idx, choice, data
        
        
    def _itemClicked(self, ev):
        """
        Called when an item in the list is clicked. Selects the item and
        posts an EVT_ELB_SELECT_EVENT.
        """

        widget    = ev.GetEventObject()
        choice    = widget.GetLabel()
        data      = self._clientData[id(widget)]

        sizerItem = self._listSizer.GetItem(widget)
        choiceIdx = self._listSizer.GetChildren().index(sizerItem)
        
        self.SetSelection(self._fixIndex(choiceIdx))
        
        idx, choice, data = self._getSelection()

        idx = self._fixIndex(idx)
        
        log.debug('ListSelectEvent (idx: {}; choice: {})'.format(idx, choice))
        
        ev = ListSelectEvent(idx=idx, choice=choice, data=data)
        wx.PostEvent(self, ev)

        
    def _moveItem(self, offset):
        """
        Called when the 'move up' or 'move down' buttons are pushed. Moves
        the selected item by the specified offset and posts an
        EVT_ELB_MOVE_EVENT, unless it doesn't make sense to do the move. 
        """

        oldIdx, choice, data = self._getSelection()
        newIdx = oldIdx + offset

        # nothing is selected, or the selected
        # item is at the top/bottom of the list.
        if oldIdx  is None:                         return
        if oldIdx < 0 or oldIdx >= self.GetCount(): return
        if newIdx < 0 or newIdx >= self.GetCount(): return

        widget = self._listSizer.GetItem(oldIdx).GetWindow()

        self._listSizer.Detach(oldIdx)
        self._listSizer.Insert(newIdx, widget, flag=wx.EXPAND)

        oldIdx = self._fixIndex(oldIdx)
        newIdx = self._fixIndex(newIdx)

        self.SetSelection(newIdx)

        self.Sizer.Layout()

        log.debug('ListMoveEvent (oldIdx: {}; newIdx: {}; choice: {})'.format(
            oldIdx, newIdx, choice))
        
        ev = ListMoveEvent(
            oldIdx=oldIdx, newIdx=newIdx, choice=choice, data=data)
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

        idx, choice, data = self._getSelection()

        idx = self._fixIndex(idx)

        log.debug('ListAddEvent (idx: {}; choice: {})'.format(idx, choice)) 

        ev = ListAddEvent(idx=idx, choice=choice, data=data)
        
        wx.PostEvent(self, ev)

        
    def _removeItem(self, ev):
        """
        Called when the 'remove item' button is pushed. Removes the selected
        item from the list, and posts an EVT_ELB_REMOVE_EVENT.
        """

        idx, choice, data = self._getSelection()

        realIdx = self._fixIndex(idx)

        if idx is None: return

        self.Delete(realIdx)

        if self.GetCount == 0:
            self.SetSelection(wx.NOT_FOUND)
        elif realIdx == self.GetCount():
            self.SetSelection(realIdx-1)
        else:
            self.SetSelection(realIdx)

        log.debug('ListRemoveEvent (idx: {}; choice: {})'.format(
            realIdx, choice)) 

        ev = ListRemoveEvent(idx=realIdx, choice=choice, data=data)
        
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
    listbox = EditableListBox(panel, items) #, style=ELB_REVERSE)

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
