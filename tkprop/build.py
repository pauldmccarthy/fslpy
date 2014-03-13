#!/usr/bin/env python
#
# build.py - Automatically build a Tkinter GUI for an object with tkprop
#            Properties.
#
# This module provides functionality to automatically build a Tkinter
# interface containing widgets which allow the user to change the
# properties (tkprop.PropertyBase objects) of a specified
# tkprop.HasProperties object.

# The sole entry point for this module is the buildGUI function, which
# accepts as parameters a tk object to be used as the parent (e.g. a
# root or Frame object), a tkprop.HasProperties object, and an optional
# ViewItem object, which specifies how the interface is to be laid out.
#
# This third parameter allows the layout of the generated interface to
# be customised.  Property widgets may be grouped together by embedding
# them within a HGroup or VGroup object; they will then respectively be
# laid out horizontally or verticaly.  Groups may be embedded within a
# NotebookGroup object, which will result in an interface containing a
# tab for each child Group.  The label for, and behaviour of, the widget
# for an individual property may be customised with a Widget object.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import Tkinter as tk
import            ttk
import tkprop  as tkp


class ViewItem(object):
    """
    Superclass for Widgets and Groups. Represents an item to be displayed.
    """
    
    def __init__(self, label=None, visibleWhen=None, enabledWhen=None):
        """
        Parameters:
        
          - label:       A label for this item, which may be used in the
                         GUI.
        
          - visibleWhen: A 2-tuple which contains the name of a property
                         of the HasProperties object, or a list of
                         property names, and a reference to a function
                         which takes one argument , and returns a
                         boolean.  When the specified property changes,
                         the function is called, and the current property
                         value passed to it. The return value is used to
                         determine whether this item should be made
                         visible or invisible.
        
          - enabledWhen: Same as the visibleWhen parameter, except the
                         state of the item (or its children) is changed
                         between enabled and disabled.
        """
        
        self.label = label

        if visibleWhen is not None:
            props, func = visibleWhen
            if isinstance(props, str):
                props = [props]
            visibleWhen = (props, func)

        if enabledWhen is not None:
            props, func = enabledWhen
            if isinstance(props, str):
                props = [props]
            enabledWhen = (props, func)

        self.visibleWhen = visibleWhen
        self.enabledWhen = enabledWhen


class Button(ViewItem):
    """
    Represents a button which, when clicked, willl call a specified
    callback function.
    """

    def __init__(self, callback=None, **kwargs):
        self.callback = callback
        ViewItem.__init__(self, **kwargs)


class Widget(ViewItem):
    """
    Represents a low level widget which is used to modify a property value.
    """
    def __init__(self, propName, **kwargs):
        """
        Parameters:
        
          - propName: The name of the property which this widget can
                      modify.
        
          - kwargs:   Passed to the ViewItem constructor.
        """
        ViewItem.__init__(self, **kwargs)
        self.propName = propName


class Group(ViewItem):
    """
    Represents a collection of other ViewItems.
    """
    def __init__(self, children=[], showLabels=False, **kwargs):
        """
        Parameters:
        
          - children:   List of ViewItem objects, the children of this
                        Group.
        
          - showLabels: Whether labels should be displayed for each of
                        the children.
        
          - kwargs:     Passed to the ViewItem constructor.
        """
        ViewItem.__init__(self, **kwargs)
        self.children   = children
        self.showLabels = showLabels


class NotebookGroup(Group):
    """
    A Group representing a ttk.Notebook. Children are added as notebook
    pages.
    """
    pass


class HGroup(Group):
    """
    A group representing a ttk.Frame, whose children are laid out
    horizontally.
    """
    pass


class VGroup(Group): 
    """
    A group representing a ttk.Frame, whose children are laid out
    vertically.
    """
    pass


def _configureEnabledWhen(viewItem, tkObj, propObj, tkLabel=None):
    """
    Sets up event handling for enabling/disabling the Tkinter object
    represented by the given viewItem.
    """

    if viewItem.enabledWhen is None: return

    condProps, condFunc = viewItem.enabledWhen
    tkVars = [getattr(propObj, '{}_tkVar'.format(p)) for p in condProps]

    def _changeState(obj, state):
        """
        Sets the state of the given Tkinter object to the given state.
        If the given object is a container, the state of its children
        are (recursively) set.
        """
        
        try: obj.configure(state=state)
        
        except tk.TclError:
            for child in obj.winfo_children():
                _changeState(child, state)
    
    def _toggleEnabled(*a):
        """
        Calls the conditional function and enables/disables
        the tk object (and its label if there is one).
        """

        varVals = [tkVar.get() for tkVar in tkVars]

        if condFunc(*varVals): state = 'enabled'
        else:                  state = 'disabled'
        
        _changeState(tkObj, state)
        if tkLabel is not None: _changeState(tkLabel, state)

    # set up initial state
    _toggleEnabled()
    
    for tkVar in tkVars: tkVar.trace('w', _toggleEnabled)


def _configureVisibleWhen(viewItem, tkObj, propObj, tkLabel=None):
    """
    Sets up event handling for showing/hiding the Tkinter object
    represented by the given viewItem.
    """ 

    if viewItem.visibleWhen is None: return

    condProps, condFunc = viewItem.visibleWhen
    tkVars = [getattr(propObj, '{}_tkVar'.format(p)) for p in condProps]

    def _toggleVis(*a):

        varVals = [tkVar.get() for tkVar in tkVars]

        if not condFunc(*varVals):
            tkObj.grid_remove()
            if tkLabel is not None: tkLabel.grid_remove()
        else:
            tkObj.grid()
            if tkLabel is not None: tkLabel.grid()

    # set up initial visibility
    _toggleVis()
    
    for tkVar in tkVars: tkVar.trace('w', _toggleVis)


def _createLabel(parent, viewItem, propObj):
    """
    Creates a ttk.Label object containing a label for the given
    viewItem.
    """

    if isinstance(viewItem, str): labelText = viewItem
    else:                         labelText = viewItem.label

    label = ttk.Label(parent, text=labelText)
    return label


def _createButton(parent, widget):
    """
    Creates a ttk.Button object for the given Button widget.
    """

    button = ttk.Button(parent, text=widget.label, command=widget.callback)
    return button


def _createWidget(parent, widget, propObj):
    """
    Creates a widget for the given Widget object, using the
    tkprop.makeWidget function (see the tkprop.widgets module
    for more details).
    """

    tkWidget = tkp.makeWidget(parent, propObj, widget.propName)
    return tkWidget

    
def _createNotebookGroup(parent, group, propObj):
    """
    Creates a ttk.Notebook object for the given NotebookGroup object.
    The children of the group object are also created via recursive
    calls to the _create function.
    """

    notebook = ttk.Notebook(parent)

    for child in group.children:

        page = _create(notebook, child, propObj)
        page.pack(fill=tk.X, expand=1)
        
        notebook.add(page, text=child.label)

    return notebook


def _layoutGroup(group, parent, children, labels):
    """
    Lays out the children (and labels, if not None) of the
    given Group object. Parameters:
    
      - group:    HGroup or VGroup object
    
      - parent:   ttk.Frame object which represents the group
    
      - children: List of Tkinter/ttk objects, the children of
                  the group.

      - labels:   None if no labels, otherwise a list of ttk.Label
                  objects, one for each child.
    """

    if isinstance(group, VGroup):
        if labels is not None: parent.columnconfigure(1, weight=1)
        else:                  parent.columnconfigure(0, weight=1)

    for cidx in range(len(children)):

        if isinstance(group, HGroup):
            
            if labels is not None:
                parent.columnconfigure(cidx*2+1,weight=1) 
                labels  [cidx].grid(row=0, column=cidx*2,   sticky=tk.E+tk.W)
                children[cidx].grid(row=0, column=cidx*2+1, sticky=tk.E+tk.W)
            else:
                parent.columnconfigure(cidx,  weight=1)
                children[cidx].grid(row=0, column=cidx, sticky=tk.E+tk.W)
                
            
        elif isinstance(group, VGroup):
            
            if labels is not None:
                labels  [cidx].grid(row=cidx, column=0, sticky=tk.E+tk.W)
                children[cidx].grid(row=cidx, column=1, sticky=tk.E+tk.W)
            else:
                children[cidx].grid(row=cidx, column=0, sticky=tk.E+tk.W)
    

def _createGroup(parent, group, propObj):
    """
    Creates a ttk.Frame object for the given group. Children of the
    group are recursively created via calls to _create, and laid out on
    the Frame.
    """

    frame = ttk.Frame(parent)

    childObjs = []

    if group.showLabels: labelObjs = []
    else:                labelObjs = None

    for i,child in enumerate(group.children):

        if isinstance(child, str):
            child = Widget(child)
            group.children[i] = child

        labelObj = None
        if group.showLabels:
            labelObj = _createLabel(frame, child, propObj)
            labelObjs.append(labelObj)

        childObj = _create(frame, child, propObj)

        childObjs.append(childObj)

    _layoutGroup(group, frame, childObjs, labelObjs)

    # set up widget events after they have been
    # laid out, so their initial state (e.g.
    # visible, enabled, etc) is correct
    for cidx in range(len(childObjs)):

        child    = group.children[cidx]
        childObj = childObjs[cidx]

        if labelObjs is not None: labelObj = labelObjs[cidx]
        else:                     labelObj = None

        _configureVisibleWhen(child, childObj, propObj, labelObj)
        _configureEnabledWhen(child, childObj, propObj, labelObj) 

    return frame


def _create(parent, viewItem, propObj):
    """
    Creates the given ViewItem object and, if it is a group, all of its
    children.
    """

    if isinstance(viewItem, str):
        viewItem = Widget(viewItem)

    if isinstance(viewItem, Widget):
        return _createWidget(parent, viewItem, propObj)

    elif isinstance(viewItem, Button):
        return _createButton(parent, viewItem)
        
    elif isinstance(viewItem, NotebookGroup):
        return _createNotebookGroup(parent, viewItem, propObj)
        
    elif isinstance(viewItem, Group):
        return _createGroup(parent, viewItem, propObj)

    return None


def _defaultView(propObj):
    """
    Creates a default view specification for the given object.
    """

    propDict = propObj.__class__.__dict__
    
    props = filter(
        lambda (name,prop): isinstance(prop, tkp.PropertyBase),
        propDict.items())
    
    propNames,props = zip(*props)

    propNames = map(Widget, propNames)

    return VGroup(label=propObj.__class__.__name__,
                  children=propNames,
                  showLabels=True)


def buildGUI(parent, propObj, view=None):
    """
    Builds a Tkinter/ttk interface which allows the properties of the
    given propObj object (a tkprop.HasProperties object) to be edited.
    Returns a reference to the top level Tkinter object (typically a
    ttk.Frame or ttk.Notebook).
    """

    if view is None: view = _defaultView(propObj)
        
    return _create(parent, view, propObj)
