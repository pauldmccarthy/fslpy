#!/usr/bin/env python
#
# widgets_list.py - A widget for editing a tkprop.List property.
#
# This file really belongs in widgets.py, but it is large and
# complex enough to warrent its own module.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import sys

import os

import tkprop  as tkp

import widgets

import Tkinter as tk
import            ttk




def _pasteDataDialog(parent):
    """
    A dialog which displays an editable text field, allowing the user
    to type/paste bulk data which will be used to populate the list
    (one line per item).
    """

    listType  = listProp.listType
    tkVarList = listObj._tkVars
    window = tk.Toplevel()
    frame  = ttk.Frame(window)


    frame.pack(fill=tk.BOTH, expand=True)

    # make the list edit dialog modal
    window.transient(parent)
    window.grab_set()
    parent.wait_window(window) 
    pass


def _editListDialog(parent, listProp, listObj, propObj):
    """
    A dialog which displays a widget for every item in the list,
    and which allows the user to adjust the number of items in
    the list.
    Parameters:
      - parent
      - listProp
      - listObj
      - propObj
    """

    listType  = listProp.listType
    tkVarList = listObj._tkVars

    # Get a reference to a function which can make
    # individual widgets for each list item
    makeFunc = getattr(
        widgets,
        '_{}'.format(listType.__class__.__name__), None)

    if makeFunc is None:
        raise ValueError(
            'Unknown property type: {}'.format(listProp.__class__.__name__)) 

    window = tk.Toplevel()
    frame  = ttk.Frame(window)

    listWidgets = []

    # Make a widget for every element in the list
    for i,v in enumerate(tkVarList):
        widget = makeFunc(frame, propObj, listType, v)
        listWidgets.append(widget)

    # A spinbox, and associated TK variable, allowing
    # the user to change the number of items in the list
    numRows   = tk.IntVar(
        name='{}_numRows'.format(listProp.label),
        value=len(listObj))

    minval = listProp.minlen if (listProp.minlen is not None) else 0
    maxval = listProp.maxlen if (listProp.maxlen is not None) else sys.maxint
    numRowsBox = tk.Spinbox(frame,
                            from_=minval,
                            to=maxval,
                            textvariable=numRows,
                            increment=1)

    # A button to push when the user is finished
    okButton = ttk.Button(frame, text='Ok', command=window.destroy)

    def changeNumRows(*args):
        """
        Called when the numRows variable is changed (via the numRows
        spinbox). Adds or removes items from the property list, and
        corresponding widgets from the window.
        """

        oldLen = len(listObj)
        newLen = numRows.get()

        # add rows
        while oldLen < newLen:

            # add a tkVar
            listObj.append(listType.default)
            tkVar = tkVarList[-1]

            # add a widget
            widg = makeFunc(frame, propObj, listProp.listType, tkVar)
            widg.grid(row=len(listObj), column=0, sticky=tk.W+tk.E)
            listWidgets.append(widg)

            oldLen = oldLen + 1

        # remove rows
        while oldLen > newLen:

            # kill the tkVar
            listObj.pop()

            # kill the widget
            widg = listWidgets.pop()
            widg.grid_forget()
            widg.destroy()

            oldLen = oldLen - 1

        # adjust the okButton location
        okButton.grid(row=newLen+1, column=0, sticky=tk.W+tk.E)

    numRows.trace('w', changeNumRows)

    # layout
    numRowsBox.grid(row=0, column=0, sticky=tk.W+tk.E)
    for i,w in enumerate(listWidgets):
        w.grid(row=i+1, column=0, sticky=tk.W+tk.E)

    okButton.grid(row=i+2, column=0, sticky=tk.W+tk.E)

    frame.columnconfigure(0, weight=1)
    frame.pack(fill=tk.BOTH, expand=True)

    # make the list edit dialog modal
    window.transient(parent)
    window.grab_set()
    parent.wait_window(window)


def _List(parent, propObj, tkProp, tkVar):
    """
    Basic list implementation - will be improved.
    """

    frame = ttk.Frame(parent)

    print('Making list widgets for {} !!'.format(tkProp.label))

    # When the user pushes this button on the parent window, a new window
    # is displayed, allowing the user to edit the values in the list 
    editButton = ttk.Button(
        frame, text='Edit',
        command=lambda: _editListDialog(parent, tkProp, tkVar, propObj))

    # When the user pushes this button, a new window is
    # displayed, allowing the user to type/paste bulk data
    pasteButton = ttk.Button(
        frame, text='Paste data',
        command=lambda: _pasteDataDialog(parent, tkProp, tkVar, propObj))

    editButton .pack(side=tk.LEFT,  fill=tk.X, expand=True)
    pasteButton.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
    return frame
