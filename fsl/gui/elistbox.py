#!/usr/bin/env python
#
# elistbox.py - A wx EditableListBox implementation. The
# wx.gizmos.EditableListBox is buggy under OS X Mavericks,
# so I felt the need to replicate its functionality.
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
                    ELB_NO_MOVE, and ELB_REVERSE.
    """

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
        noButtons     = not any((addSupport, removeSupport, moveSupport))

        self.reverseOrder = reverseOrder

        if clientData is None: clientData = [None] * len(choices)

        # The list box containing the list of items
        self.listBox = wx.ListBox(self, style=wx.LB_SINGLE | wx.LB_NEEDED_SB)
        self.listBox.Bind(wx.EVT_LISTBOX, self._itemSelected)

        items = zip(choices, clientData)
        if reverseOrder:
            items.reverse()

        for choice, data in items:
            self.listBox.Append(choice, data)

        # A panel containing buttons for doing stuff with the list
        if not noButtons:
            self.buttonPanel      = wx.Panel(self)
            self.buttonPanelSizer = wx.BoxSizer(wx.VERTICAL)
            self.buttonPanel.SetSizer(self.buttonPanelSizer) 

        # Buttons for moving the selected item up/down
        if moveSupport:
            self.upButton   = wx.Button(self.buttonPanel, label=u'\u25B2',
                                        style=wx.BU_EXACTFIT)
            self.downButton = wx.Button(self.buttonPanel, label=u'\u25BC',
                                        style=wx.BU_EXACTFIT)
            self.upButton  .Bind(wx.EVT_BUTTON, self._moveItemUp)
            self.downButton.Bind(wx.EVT_BUTTON, self._moveItemDown)

            self.buttonPanelSizer.Add(self.upButton,   flag=wx.EXPAND)
            self.buttonPanelSizer.Add(self.downButton, flag=wx.EXPAND) 

        # Button for adding new items
        if addSupport:
            self.addButton = wx.Button(self.buttonPanel, label='+',
                                       style=wx.BU_EXACTFIT)
            self.addButton.Bind(wx.EVT_BUTTON, self._addItem)
            self.buttonPanelSizer.Add(self.addButton, flag=wx.EXPAND) 

        # Button for removing the selected item
        if removeSupport:
            self.removeButton = wx.Button(self.buttonPanel, label='-',
                                          style=wx.BU_EXACTFIT)

            self.removeButton.Bind(wx.EVT_BUTTON, self._removeItem)
            self.buttonPanelSizer.Add(self.removeButton, flag=wx.EXPAND)

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)

        if not noButtons:
            self.sizer.Add(self.buttonPanel, flag=wx.EXPAND)
            
        self.sizer.Add(self.listBox, flag=wx.EXPAND, proportion=1)

        self.sizer.Layout()

        
    def _fixIndex(self, idx):
        """
        If the ELB_REVERSE style is active, this method will return
        an inverted version of the given index. Otherwise it returns
        the index value unchanged.
        """

        if idx is None:           return idx
        if idx == wx.NOT_FOUND:   return idx
        if not self.reverseOrder: return idx
        
        idx = self.listBox.GetCount() - idx - 1
        
        return idx

    #
    # These methods simply wrap the same-named wx.ListBox methods,
    # while supporting the ELB_REVERSE style.
    #

    def GetCount(self): return self.listBox.GetCount()
    
    def SetSelection(self, n):
        self.listBox.SetSelection(self._fixIndex(n))
        
    def GetSelection(self):
        return self._fixIndex(self.listBox.GetSelection())

    def Insert(self, item, pos, clientData):
        return self.listBox.Insert(item, self._fixIndex(pos), clientData)

    def Append(self, item, clientData):
        if not self.reverseOrder:
            return self.listBox.Append(item, clientData)
        else:
            return self.listBox.Insert(item, 0, clientData)

    def Delete(self, n):
        return self.listBox.Delete(self._fixIndex(n))

        
    def _getSelection(self):
        """
        Returns a 3-tuple containing the index, label, and associated client
        data of the currently selected list item, or (None, None, None) if
        no item is selected. 
        """
        
        idx    = self.listBox.GetSelection()
        choice = None
        data   = None

        if idx == wx.NOT_FOUND:
            idx = None
        else:
            choice = self.listBox.GetString(    idx)
            data   = self.listBox.GetClientData(idx)

        return idx, choice, data
        
        
    def _itemSelected(self, ev):
        """
        Called when an item in the list is selected. Posts an
        EVT_ELB_SELECT_EVENT.
        """
        
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
        if oldIdx  is None:                                 return
        if oldIdx < 0 or oldIdx >= self.listBox.GetCount(): return
        if newIdx < 0 or newIdx >= self.listBox.GetCount(): return 

        self.listBox.Delete(oldIdx)
        self.listBox.Insert(choice, newIdx, data)
        self.listBox.SetSelection(newIdx)

        oldIdx = self._fixIndex(oldIdx)
        newIdx = self._fixIndex(newIdx)

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

        self.listBox.Delete(idx)
        self.listBox.SetSelection(wx.NOT_FOUND)

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
