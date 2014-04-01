#!/usr/bin/env python
#
# widgets_list.py - A widget for editing a props.List property.
#
# The code in this file really belongs in widgets.py, but it is
# large and complex enough to warrent its own module.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import sys
import os

import wx

import widgets


def _pasteDataDialog(parent, hasProps, propObj):
    """
    Displays a dialog containing an editable text field, allowing the
    user to type/paste bulk data which will be used to populate the list
    (one line per item).
    
    Parameters:
      - parent:   parent GUI object 
      - hasProps: The props.HasProperties object which owns propObj. 
      - propObj:  The props.List property object
    """

    listObj  = getattr(hasProps, propObj.label)
    initText = '\n'.join([str(l).strip() for l in listObj])
 
    frame = wx.Frame(parent)
    panel = wx.Panel(frame)
    text  = wx.TextCtrl(panel, value=text,
                        style=wx.MULTILINE | wx.VSCROLL | wx.HSCROLL)

    # ok/cancel buttons
    okButton     = wx.Button(panel, label="Ok")
    cancelButton = wx.Button(panel, label="Cancel")

    sizer = wx.GridBagSizer()

    panel.SetSizer(sizer)

    sizer.Add(text,         pos=(0,0), span=(1,2), flag=wx.EXPAND)
    sizer.Add(okButton,     pos=(1,0), span=(1,1), flag=wx.EXPAND)
    sizer.Add(cancelButton, pos=(1,1), span=(1,1), flag=wx.EXPAND)

    sizer.AddGrowableRow(0)

    def pasteIntoList():
        """
        Called when the user pushes 'Ok'. Copies whatever the
        user typed/pasted into the text area into the list, and
        closes the dialog window.
        """

        listData = text.GetValue().strip()
        listData = listData.split('\n')
        listData = [s.strip() for s in listData]

        setattr(hasProps, propObj.label, listData)
        frame.Close()

    okButton    .Bind(wx.EVT_BUTTON, lambda e: pasteIntoList())
    cancelButton.Bind(wx.EVT_BUTTON, lambda e: frame.Close())

    frame.ShowModal()


def _editListDialog(parent, hasProps, propObj):
    """
    A dialog which displays a widget for every item in the list, and
    which allows the user to adjust the number of items in the list.
    """

    # listObj is a properties.ListWrapper object
    listObj  = getattr(hasProps, propObj.label)
    listType = propObj.listType

    # Get a reference to a function in the widgets module,
    # which can make individual widgets for each list item
    makeFunc = getattr(
        widgets, '_{}'.format(listType.__class__.__name__), None)

    if makeFunc is None:
        raise TypeError(
            'Unknown property type: {}'.format(propObj.__class__.__name__))

    # min/max values for a spin box which allows the
    # user to select the number of items in the list
    minval = propObj.minlen if (propObj.minlen is not None) else 1
    maxval = propObj.maxlen if (propObj.maxlen is not None) else sys.maxint

    frame       = wx.Frame(parent)
    panel       = wx.ScrolledPanel(frame)
    okButton    = wx.Button(frame, label='Ok')
    numRowsBox  = wx.SpinCtrl(frame,
                              min=minval,
                              max=maxval,
                              initial=len(listObj))
    listWidgets = []

    # Make a widget for every element in the list
    for i in range(len(listObj)):
        propVal = propObj.getPropVal(hasProps, i)
        widget  = makeFunc(panel, hasProps, listType, propVal)
        listWidgets.append(widget)

    frameSizer = wx.BoxSizer(wx.VERTICAL)
    frame.SetSizer(frameSizer)
    frameSizer.Add(numRowsBox, flag=wx.EXPAND)
    frameSizer.Add(panel,      flag=wx.EXPAND, proportion=1)
    frameSizer.Add(okButton,   flag=wx.EXPAND)

    panelSizer = wx.BoxSizert(wx.VERTICAL)
    panel.SetSizer(panelSizer)
    for i in range(len(listWidgets)):
        panelSizer.Add(listWidgets[i], flag=wx.EXPAND)


    def changeNumRows(*args):
        """
        Called when the numRows variable is changed (via the numRows
        spinbox). Adds or removes the last  item from the property
        list, and corresponding widget from the window.
        """

        oldLen = len(listObj)
        newLen = numRowsBox.GetValue()

        # add rows
        while oldLen < newLen:

            # add a new element to the list
            listObj.append(listType.default)
            propVal = propObj.getPropVal(hasProps, -1)

            # add a widget
            widg = makeFunc(frame, hasProps, listType, propVal)
            listWidgets.append(widg)
            panelSizer.Add(widg, flag=wx.EXPAND)
 
            oldLen = oldLen + 1

        # remove rows
        while oldLen > newLen:

            # kill the list item
            listObj.pop()

            # kill the widget
            widg = listWidgets.pop()
            widg.Destroy()

            # TODO Remove widget listener from property value ...

            oldLen = oldLen - 1

    numRowsBox.Bind(wx.EVT_SPINCTRL, changeNumRows)
    okButton.Bind(wx.EVT_BUTTON, lambda e: frame.Close())

    frame.ShowModal()

    
def _List(parent, hasProps, propObj, propVal):
    """
    Creates and returns a GUI panel containing two buttons which,
    when pushed, display dialogs allowing the user to edit the
    values contained in the list.
    """

    panel = wx.Panel(parent)

    # When the user pushes this button on the parent window,
    # a new window is displayed, allowing the user to edit
    # the values in the list individually
    editButton = wx.Button(panel, label='Edit')
    editButton.Bind(
        wx.EVT_BUTTON, lambda: _editListDialog(parent, hasProps, propObj))

    # When the user pushes this button, a new window is
    # displayed, allowing the user to type/paste bulk data
    pasteButton = wx.Button(panel, label='Paste data')
    pasteButton.Bind(
        wx.EVT_BUTTON, lambda: _pasteDataDialog(parent, hasProps, propObj))

    sizer = wx.BoxSizer(wx.HORIZONTAL)
    panel.SetSizer(sizer)

    sizer.Add(editButton,  flag=wx.EXPAND)
    sizer.Add(pasteButton, flag=wx.EXPAND)

    panel.Layout()
        
    return panel
