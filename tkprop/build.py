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
# root or Frame object), a tkprop.HasProperties object, an optional
# ViewItem object, which specifies how the interface is to be laid
# out, and two optional dictionaries for passing in labels and
# tooltips.
#
# The view parameter allows the layout of the generated interface to
# be customised.  Property widgets may be grouped together by embedding
# them within a HGroup or VGroup object; they will then respectively be
# laid out horizontally or verticaly.  Groups may be embedded within a
# NotebookGroup object, which will result in an interface containing a
# tab for each child Group.  The label for, and behaviour of, the widget
# for an individual property may be customised with a Widget object.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import sys

import Tkinter           as tk
import                      ttk
import tkprop            as tkp
import tkprop.properties as properties


class ViewItem(object):
    """
    Superclass for Widgets, Buttons and Groups. Represents an item to be
    displayed.
    """
    
    def __init__(self, key=None, label=None, tooltip=None,
                 visibleWhen=None, enabledWhen=None):
        """
        Parameters:

          - key:         An identifier for this item. If this item is a
                         Widget, this should be the property name that
                         the widget edits. This key is used to look up
                         labels and tooltips, if they are passed in as
                         dicts (see the buildGUI function).
        
          - label:       A label for this item, which may be used in the
                         GUI.

          - tooltip:     A tooltip, which may be displayed when the user
                         hovers the mouse over the widget for this
                         ViewItem.
        
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
        
        self.key         = key
        self.label       = label
        self.tooltip     = tooltip
        self.visibleWhen = visibleWhen
        self.enabledWhen = enabledWhen


class Button(ViewItem):
    """
    Represents a button which, when clicked, will call a specified
    callback function.
    """

    def __init__(self, key=None, text=None, callback=None, **kwargs):
        self.callback = callback
        self.text     = text
        ViewItem.__init__(self, key, **kwargs)


class Label(ViewItem):
    """
    Represents a static text label.
    """
    def __init__(self, viewItem=None, **kwargs):
        """
        A Label object may either be created in the same way as any other
        ViewItem object, or it may be created from another ViewItem object,
        the object to be lablled.
        """

        if viewItem is not None:
            kwargs['key']         = '{}_label'.format(viewItem.key)
            kwargs['label']       = viewItem.label
            kwargs['tooltip']     = viewItem.tooltip
            kwargs['visibleWhen'] = viewItem.visibleWhen
            kwargs['enabledWhen'] = viewItem.enabledWhen
            
        ViewItem.__init__(self, **kwargs)
    pass


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
        
        kwargs['key'] = propName
        ViewItem.__init__(self, **kwargs)


class Group(ViewItem):
    """
    Represents a collection of other ViewItems.
    """
    def __init__(self, children=[], showLabels=True, border=False, **kwargs):
        """
        Parameters:
        
          - children:   List of ViewItem objects, the children of this
                        Group.
        
          - showLabels: Whether labels should be displayed for each of
                        the children. If this is true, an attribute will
                        be added to this Group object in the _prepareView
                        function, called 'childLabels', and containing a
                        Label object for each child.

          - border:     If True, this group will be drawn with a border
                        around it. If this group is a child of another
                        VGroup, it will be laid out a bit differently,
                        too.
        
          - kwargs:     Passed to the ViewItem constructor.
        """
        ViewItem.__init__(self, **kwargs)
        self.children   = children
        self.border     = border
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


class PropGUI(object):
    """
    A container class used for convenience. Stores references to
    all Tkinter/ttk objects that are created, and to all conditional
    callbacks (which control visibility/state).
    """
    
    def __init__(self):
        self.onChangeCallbacks = []
        self.tkObjects         = {}
 

def _configureEnabledWhen(viewItem, tkObj, propObj):
    """
    Returns a reference to a callback function for this view item,
    if its enabledWhen attribute was set.
    """

    if viewItem.enabledWhen is None: return None

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
    
    def _toggleEnabled():
        """
        Calls the conditional function and enables/disables
        the tk object (and its label if there is one).
        """

        if viewItem.enabledWhen(propObj): state = 'enabled'
        else:                             state = 'disabled'
        
        _changeState(tkObj, state)

    return _toggleEnabled


def _configureVisibleWhen(viewItem, tkObj, propObj):
    """
    Returns a reference to a callback function for this view item,
    if its visibleWhen attribute was set.
    """ 

    if viewItem.visibleWhen is None: return None

    def _toggleVis():

        if not viewItem.visibleWhen(propObj): tkObj.grid_remove()
        else:                                 tkObj.grid()

    return _toggleVis


def _createLabel(parent, viewItem, propObj, propGui):
    """
    Creates a ttk.Label object containing a label for the given
    viewItem.
    """

    label = ttk.Label(parent, text=viewItem.label)
    return label


def _createButton(parent, viewItem, propObj, propGui):
    """
    Creates a ttk.Button object for the given Button widget.
    """

    btnText = None

    if   viewItem.text  is not None: btnText = viewItem.text
    elif viewItem.label is not None: btnText = viewItem.label
    elif viewItem.key   is not None: btnText = viewItem.key
        
    button = ttk.Button(parent, text=btnText, command=viewItem.callback)
    return button


def _createWidget(parent, viewItem, propObj, propGui):
    """
    Creates a widget for the given Widget object, using the
    tkprop.makeWidget function (see the tkprop.widgets module
    for more details).
    """

    tkWidget = tkp.makeWidget(parent, propObj, viewItem.key)
    return tkWidget

    
def _createNotebookGroup(parent, group, propObj, propGui):
    """
    Creates a ttk.Notebook object for the given NotebookGroup object.
    The children of the group object are also created via recursive
    calls to the _create function.
    """

    notebook = ttk.Notebook(parent)

    for child in group.children:

        page = _create(notebook, child, propObj, propGui)
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
            
            if labels is not None and labels[cidx] is not None:
                parent.columnconfigure(cidx*2+1,weight=1) 
                labels  [cidx].grid(row=0, column=cidx*2,   sticky=tk.W+tk.E)
                children[cidx].grid(row=0, column=cidx*2+1, sticky=tk.W+tk.E)
            else:
                parent.columnconfigure(cidx,  weight=1)
                children[cidx].grid(row=0, column=cidx, sticky=tk.W+tk.E)
            
        elif isinstance(group, VGroup):

            # Groups within VGroups, which don't have a border, are 
            # laid out the same as any other widget, which probably
            # looks a bit ugly. If they do have a border, however,
            # they are laid out so as to span the entire width of
            # the parent VGroup, and given a border. Instead of
            # having a separate label widget, the label is embedded
            # in the border.
            if isinstance(group.children[cidx], (HGroup, VGroup)) and \
               group.children[cidx].border:

                children[cidx].grid(
                    row=cidx, column=0, columnspan=2,
                    sticky=tk.E+tk.W+tk.N+tk.S)

            elif labels is not None:
                if labels[cidx] is not None:
                    labels  [cidx].grid(row=cidx, column=0, sticky=tk.E+tk.W)
                    children[cidx].grid(row=cidx, column=1, sticky=tk.E+tk.W)
                else:
                    children[cidx].grid(row=cidx, column=0, columnspan=2,
                                        sticky=tk.E+tk.W)
            else:
                children[cidx].grid(row=cidx, column=0, sticky=tk.E+tk.W)


def _createGroup(parent, group, propObj, propGui):
    """
    Creates a ttk.Frame object for the given group. Children of the
    group are recursively created via calls to _create, and laid out on
    the Frame.
    """

    if group.border:
        frame = ttk.LabelFrame(parent)
        frame.config(
            borderwidth=20,
            relief=tk.SUNKEN,
            labelanchor='n',
            text=group.label) 
    else:
        frame = ttk.Frame(parent)

    childObjs = []

    if group.showLabels: labelObjs = []
    else:                labelObjs = None

    for i,child in enumerate(group.children):

        labelObj = None

        if group.showLabels:
            if group.childLabels[i] is not None:
                labelObj = _create(
                    frame, group.childLabels[i], propObj, propGui)
                labelObjs.append(labelObj)
            else:
                labelObjs.append(None)
            

        childObj = _create(frame, child, propObj, propGui)

        childObjs.append(childObj)

    _layoutGroup(group, frame, childObjs, labelObjs)

    return frame


# These aliases are so we can introspectively look up the
# appropriate _create* function based upon the class name
# of the ViewItem being created.
_createHGroup = _createGroup
_createVGroup = _createGroup


def _create(parent, viewItem, propObj, propGui):
    """
    Creates the given ViewItem object and, if it is a group, all of its
    children.
    """

    cls = viewItem.__class__.__name__

    createFunc = getattr(sys.modules[__name__], '_create{}'.format(cls), None)

    if createFunc is None:
        raise ValueError('Unrecognised ViewItem: {}'.format(
            viewItem.__class__.__name__))

    tkObject  = createFunc(parent, viewItem, propObj, propGui)
    visibleCb = _configureVisibleWhen(viewItem, tkObject, propObj)
    enableCb  = _configureEnabledWhen(viewItem, tkObject, propObj)

    if visibleCb is not None: propGui.onChangeCallbacks.append(visibleCb)
    if enableCb  is not None: propGui.onChangeCallbacks.append(enableCb)

    propGui.tkObjects[viewItem.key] = tkObject

    return tkObject


def _defaultView(propObj):
    """
    Creates a default view specification for the given object.
    """

    propDict = propObj.__class__.__dict__
    
    props = filter(
        lambda (name,prop): isinstance(prop, tkp.PropertyBase),
        propDict.items())
    
    propNames,props = zip(*props)

    return VGroup(label=propObj.__class__.__name__, children=propNames)


def _prepareView(viewItem, labels, tooltips):
    """
    Recursively steps through the given viewItem and its children (if any).
    If the viewItem is a string, it is assumed to be a property name, and
    it is turned into a Widget object. If the viewItem does not have a
    label/tooltip, and there is a label/tooltip for it in the given
    labels/tooltips dict, then its label/tooltip is set.  Returns a
    reference to the updated ViewItem.
    """

    if isinstance(viewItem, str):
        viewItem = Widget(viewItem)

    if not isinstance(viewItem, ViewItem):
        raise ValueError('Not a ViewItem')

    if viewItem.label   is None:
        viewItem.label   = labels  .get(viewItem.key, None)
    if viewItem.tooltip is None:
        viewItem.tooltip = tooltips.get(viewItem.key, None) 

    if isinstance(viewItem, Group):

        # children may have been specified as
        # a tuple, so we cast it to a list
        viewItem.children = list(viewItem.children)

        for i,child in enumerate(viewItem.children):
            viewItem.children[i] = _prepareView(child, labels, tooltips)

        if viewItem.showLabels:
            viewItem.childLabels = []

            for child in viewItem.children:
                if child.label is None:
                    viewItem.childLabels.append(None)
                elif isinstance(child, (HGroup,VGroup)) and child.border:
                    viewItem.childLabels.append(None)
                else:
                    viewItem.childLabels.append(Label(child))

    return viewItem

    
def _prepareEvents(propObj, propGui):
    """
    If the visibleWhen or enabledWhen conditional attributes were set for any
    ViewItem objects, a trace callback function is set on all Tkinter control
    variables. When any variable value changes, the visibleWhen/enabledWhen
    callback functions are called.
    """

    if len(propGui.onChangeCallbacks) == 0:
        return

    def onChange(*a):
        for cb in propGui.onChangeCallbacks:
            cb()

    propDict = propObj.__class__.__dict__
    
    props = filter(
        lambda (name,prop): isinstance(prop, tkp.PropertyBase),
        propDict.items())
    
    propNames,props = zip(*props)

    tkVars = [getattr(propObj, '{}_tkVar'.format(name)) for name in propNames]

    # initialise widget states
    onChange()

    for t in tkVars:
        
        # The List property type stores a reference to the underlying
        # _ListWrapper object in the _tkVar attribute. The Tkinter
        # variables are stored in this _ListWrapper object.
        if not isinstance(t, properties._ListWrapper): 
            t.trace('w', onChange)

        # TODO add support for lists. This will probably require
        # some additions to the properties._ListWrapper class,
        # as it will need to manage addition/removal of traces
        # on the list variables.
        else:
            pass


def buildGUI(parent, propObj, view=None, labels=None, tooltips=None):
    """
    Builds a Tkinter/ttk interface which allows the properties of the
    given propObj object (a tkprop.HasProperties object) to be edited.
    Returns a reference to the top level Tkinter object (typically a
    ttk.Frame or ttk.Notebook).

    Parameters:
    
     - parent:   Tkinter parent object
     - propObj:  tkprop.HasProperties object
    
    Optional:
    
     - view:     ViewItem object, specifying the interface layout
     - labels:   Dict specifying labels
     - tooltips: Dict specifying tooltips
    """

    if view is None: view = _defaultView(propObj)

    if labels   is None: labels   = {}
    if tooltips is None: tooltips = {}

    view = _prepareView(view, labels, tooltips)

    propGui = PropGUI()
        
    topLevel = _create(parent, view, propObj, propGui)

    _prepareEvents(propObj, propGui)

    return topLevel
