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


def _pasteDataDialog(parent, listProp, propObj):
    """
    A dialog which displays an editable text field, allowing the user
    to type/paste bulk data which will be used to populate the list
    (one line per item).
    
    Parameters:
      - parent:   Tkinter parent object
      - listProp: The tkprop.List property object
      - propObj:  The tkprop.HasProperties object which owns listProp.    
    """

    listObj = propObj.getTkVar(listProp.label)
    
    window = tk.Toplevel()
    frame  = ttk.Frame(window)

    frame.pack(fill=tk.BOTH, expand=True)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(   0, weight=1)

    # TODO label explaining what to do
    text    = tk.Text(frame, wrap="none")
    vScroll = ttk.Scrollbar(frame, orient=tk.VERTICAL,   command=text.yview)
    hScroll = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=text.xview)
    
    initText = '\n'.join([str(l) for l in listObj])
    text.insert('1.0', initText)

    def pasteIntoList():
        """
        Copies whatever the user typed/pasted
        into the text area into the list.
        """

        listData = text.get('1.0', 'end')
        listData = listData.split('\n')
        listData = [s.strip() for s in listData]
        listData = filter(len, listData)

        setattr(propObj, listProp.label, listData)
        
        window.destroy()

    # ok/cancel buttons
    btnFrame     = ttk.Frame(frame)
    okButton     = ttk.Button(btnFrame, text="Ok",     command=pasteIntoList)
    cancelButton = ttk.Button(btnFrame, text="Cancel", command=window.destroy)

    # lay out the widgets!
    text    .grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
    hScroll .grid(row=1, column=0, sticky=tk.E+tk.W)
    vScroll .grid(row=0, column=1, sticky=tk.N+tk.S)
    btnFrame.grid(row=2, column=0, sticky=tk.E+tk.W, columnspan=2)

    btnFrame.columnconfigure(0, weight=1)
    btnFrame.columnconfigure(1, weight=1)
    okButton    .grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
    cancelButton.grid(row=0, column=1, sticky=tk.N+tk.S+tk.E+tk.W)

    # make this window modal
    window.transient(parent)
    window.grab_set()
    parent.wait_window(window) 


def _editListDialog(parent, listProp, propObj):
    """
    A dialog which displays a widget for every item in the list, and
    which allows the user to adjust the number of items in the list.
    
    Parameters:
      - parent:   Tkinter parent object
      - listProp: The tkprop.List property object
      - propObj:  The tkprop.HasProperties object which owns listProp.
    """

    listType  = listProp.listType
    listObj   = propObj.getTkVar(listProp.label)
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
        widget = makeFunc(frame, propObj, listType, v.tkVar)
        listWidgets.append(widget)

    # A spinbox, and associated TK variable, allowing
    # the user to change the number of items in the list
    numRowsName = '{}_numRows'.format(listProp.label)
    numRows     = tk.IntVar(master=window,
                            name=numRowsName,
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
            tkVar = tkVarList[-1].tkVar

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

    traceName = numRows.trace('w', changeNumRows)

    # layout
    numRowsBox.grid(row=0, column=0, sticky=tk.W+tk.E)
    for i,w in enumerate(listWidgets):
        w.grid(row=i+1, column=0, sticky=tk.W+tk.E)

    okButton.grid(row=len(listWidgets)+2, column=0, sticky=tk.W+tk.E)

    frame.columnconfigure(0, weight=1)
    frame.pack(fill=tk.BOTH, expand=True)

    # make the list edit dialog modal
    window.transient(parent)
    window.grab_set()
    parent.wait_window(window)


def _List(parent, propObj, tkProp, tkVar):
    """
    Creates and returns a ttk.Frame containing two buttons which,
    when pushed, display dialogs allowing the user to edit the
    values contained in the list.
    """

    frame = ttk.Frame(parent)

    # When the user pushes this button on the parent window,
    # a new window is displayed, allowing the user to edit
    # the values in the list individually
    editButton = ttk.Button(
        frame, text='Edit',
        command=lambda: _editListDialog(parent, tkProp, propObj))

    # When the user pushes this button, a new window is
    # displayed, allowing the user to type/paste bulk data
    pasteButton = ttk.Button(
        frame, text='Paste data',
        command=lambda: _pasteDataDialog(parent, tkProp, propObj))

    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=1)
    editButton .grid(row=0, column=0, sticky=tk.E+tk.W)
    pasteButton.grid(row=0, column=1, sticky=tk.E+tk.W)
        
    return frame
