#!/usr/bin/env python
#
# build.py - Automatically build a wx GUI for a props.HasProperties
#            object.
#
# This module provides functionality to automatically build a GUI
# containing widgets which allow the user to change the properties
# (props.PropertyBase objects) of a specified props.HasProperties
# object.

# The sole entry point for this module is the buildGUI function, which
# accepts as parameters a GUI object to be used as the parent (e.g. a
# wx.Frame object), a props.HasProperties object, an optional
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
import logging

import wx

import wx.lib.agw.flatnotebook as wxnb

import widgets

class ViewItem(object):
    """
    Superclass for Widgets, Buttons, Labels  and Groups. Represents an
    item to be displayed.
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
                         which takes one argument, and returns a
                         boolean.  When the specified property changes,
                         the function is called, and the HasProperties
                         instance passed to it. The return value is used
                         to determine whether this item should be made
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
        the object to be labelled.
        """

        if viewItem is not None:
            kwargs['key']         = '{}_label'.format(viewItem.key)
            kwargs['label']       = viewItem.label
            kwargs['tooltip']     = viewItem.tooltip
            kwargs['visibleWhen'] = viewItem.visibleWhen
            kwargs['enabledWhen'] = viewItem.enabledWhen
            
        ViewItem.__init__(self, **kwargs)


class Widget(ViewItem):
    """
    Represents a widget which is used to modify a property value.
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
    def __init__(self, children, showLabels=True, border=False, **kwargs):
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
    A Group representing a GUI Notebook. Children are added as notebook
    pages.
    """
    def __init__(self, children, **kwargs):
        kwargs['border'] = kwargs.get('border', True)
        Group.__init__(self, children, **kwargs)


class HGroup(Group):
    """
    A group representing a GUI panel, whose children are laid out
    horizontally.
    """
    pass


class VGroup(Group): 
    """
    A group representing a GUI panel, whose children are laid out
    vertically.
    """
    def __init__(self, children, **kwargs):
        kwargs['border'] = kwargs.get('border', True)
        Group.__init__(self, children, **kwargs) 


class PropGUI(object):
    """
    A container class used for convenience. Stores references to
    all wx objects that are created, and to all conditional
    callbacks (which control visibility/state).
    """
    
    def __init__(self):
        self.onChangeCallbacks = []
        self.guiObjects        = {}
        self.topLevel          = None
 

def _configureEnabledWhen(viewItem, guiObj, hasProps):
    """
    Returns a reference to a callback function for this view item,
    if its enabledWhen attribute was set.
    Parameters:

      - viewItem: The ViewItem object
      - guiObj:   The GUI object created from the ViewItem
      - hasProps: The HasProperties instance
    """

    if viewItem.enabledWhen is None: return None

    parent         = guiObj.GetParent()
    isNotebookPage = isinstance(parent, wxnb.FlatNotebook)

    def _toggleEnabled():
        """
        Calls the viewItem.enabledWhen function and
        enables/disables the GUI object, depending
        upon the result.
        """

        if viewItem.enabledWhen(hasProps): state = True
        else:                              state = False

        # TODO The wx.lib.agw.flatnotebook seems to be a little
        # flaky for enable/disable support. It may be a better
        # option to use the standard wx.Notebook class, with
        # some custom event handlers for preventing access to
        # a disabled tab.
        if isNotebookPage:

            isCurrent = parent.GetCurrentPage() == guiObj
            isEnabled = parent.GetEnabled(guiObj._notebookIdx)

            if isEnabled != state:
                parent.EnableTab(guiObj._notebookIdx, state)
                
                if not state and isCurrent:
                    parent.AdvanceSelection()
            
        elif guiObj.IsEnabled() != state:
            guiObj.Enable(state)

    return _toggleEnabled


def _configureVisibleWhen(viewItem, guiObj, hasProps):
    """
    Returns a reference to a callback function for this view item,
    if its visibleWhen attribute was set.
    """ 

    if viewItem.visibleWhen is None: return None

    if isinstance(guiObj.GetParent(), wxnb.FlatNotebook):
        raise TypeError('Visibility of notebook pages is not '\
                        'configurable - use enabledWhen instead.')

    def _toggleVis():

        visible = viewItem.visibleWhen(hasProps)
        parent = guiObj.GetParent()

        if visible != guiObj.IsShown():
            parent.GetSizer().Show(guiObj, visible)
            parent.GetSizer().Layout()
        
    return _toggleVis


def _createLabel(parent, viewItem, hasProps, propGui):
    """
    Creates a GUI static text label object containing a label for the
    given viewItem.
    """

    label = wx.StaticText(parent, label=viewItem.label)
    return label


def _createButton(parent, viewItem, hasProps, propGui):
    """
    Creates a GUI Button object for the given ViewItem (assumed to be a
    Button).
    """

    btnText = None

    if   viewItem.text  is not None: btnText = viewItem.text
    elif viewItem.label is not None: btnText = viewItem.label
    elif viewItem.key   is not None: btnText = viewItem.key
        
    button = wx.Button(parent, label=btnText)
    button.Bind(wx.EVT_BUTTON, lambda e: viewItem.callback)
    return button


def _createWidget(parent, viewItem, hasProps, propGui):
    """
    Creates a widget for the given Widget object, using the
    props.makeWidget function (see the props.widgets module
    for more details).
    """

    widget = widgets.makeWidget(parent, hasProps, viewItem.key)
    return widget


def _createNotebookGroup(parent, group, hasProps, propGui):
    """
    Creates a GUI Notebook object for the given NotebookGroup object.
    The children of the group object are also created via recursive
    calls to the _create function.
    """

    notebook = wxnb.FlatNotebook(
        parent,
        agwStyle=wxnb.FNB_NO_X_BUTTON    | \
                 wxnb.FNB_NO_NAV_BUTTONS | \
                 wxnb.FNB_NODRAG)

    for i,child in enumerate(group.children):
        
        if child.label is None: pageLabel = '{}'.format(i)
        else:                   pageLabel = child.label

        if isinstance(child, Group):
            child.border = False

        page = _create(notebook, child, hasProps, propGui)
        notebook.InsertPage(i, page, text=pageLabel)
        page._notebookIdx = i

    notebook.SetSelection(0)

    return notebook


def _layoutHGroup(group, parent, children, labels):
    """
    Lays out the children (and labels, if not None) of the
    given HGroup object. Parameters:
    
      - group:    HGroup object
    
      - parent:   GUI object which represents the group
    
      - children: List of GUI objects, the children of the group.

      - labels:   None if no labels, otherwise a list of GUI Label
                  objects, one for each child.
    """

    sizer = wx.BoxSizer(wx.HORIZONTAL)

    for cidx in range(len(children)):

        if labels is not None and labels[cidx] is not None:
            sizer.Add(labels[cidx], flag=wx.EXPAND)
                
        sizer.Add(children[cidx], flag=wx.EXPAND, proportion=1)

        # TODO I have not added support
        # for child groups with borders

    parent.SetSizer(sizer)
    sizer.Layout()
    sizer.Fit(parent)

    
def _layoutVGroup(group, parent, children, labels):
    """
    Lays out the children (and labels, if not None) of the
    given VGroup object. Parameters the same as _layoutHGroup.
    """

    sizer = wx.GridBagSizer(1,1)
    sizer.SetEmptyCellSize((0,0))

    for cidx in range(len(children)):

        vItem       = group.children[cidx]
        child       = children[cidx]
        label       = labels[cidx]
        childParams = {}

        # Groups within VGroups, which don't have a border, are 
        # laid out the same as any other widget, which probably
        # looks a bit ugly. If they do have a border, however, 
        # they are laid out so as to span the entire width of
        # the parent VGroup. Instead of having a separate label
        # widget, the label is embedded in the border. The
        # _createGroup function takes care of creating the
        # border/label for the child GUI object.
        if (isinstance(vItem, Group) and vItem.border):

            label = None
            childParams['pos']    = (cidx, 0)
            childParams['span']   = (1,2)
            childParams['border'] = 20
            childParams['flag']   = wx.EXPAND | wx.ALL

        # No labels are being drawn for any child, so all
        # children should span both columns. In this case
        # we could just use a vertical BoxSizer instead of
        # a GridBagSizer,  but I'm going to leave that for
        # the time being.
        elif not group.showLabels:
            childParams['pos']    = (cidx, 0)
            childParams['span']   = (1, 2)
            childParams['border'] = 2
            childParams['flag']   = wx.EXPAND | wx.BOTTOM

        # Otherwise the child is drawn in the standard way -
        # label on the left column, child on the right.
        else:
            childParams['pos']    = (cidx, 1)
            childParams['border'] = 2
            childParams['flag']   = wx.EXPAND | wx.BOTTOM
            
        if label is not None:
            sizer.Add(labels[cidx], pos=(cidx,0), flag=wx.EXPAND)
            
        sizer.Add(child, **childParams)

    sizer.AddGrowableCol(1)

    parent.SetSizer(sizer)
    sizer.Layout()
    sizer.Fit(parent)


def _createGroup(parent, group, hasProps, propGui):
    """
    Creates a GUI panel object for the given HGroup or VGroup. Children
    of the group are recursively created via calls to _create, and laid
    out on the Frame via the _layoutGroup function.
    """


    if group.border:
        
        borderPanel = wx.Panel(parent, style=wx.SUNKEN_BORDER)
        borderSizer = wx.BoxSizer(wx.VERTICAL)
        panel       = wx.Panel(borderPanel)
        
        if group.label is not None:
            label = wx.StaticText(borderPanel, label=group.label)
            line  = wx.StaticLine(borderPanel, style=wx.LI_HORIZONTAL)
            
            font  = label.GetFont()
            font.SetPointSize(font.GetPointSize() - 2)
            font.SetWeight(wx.FONTWEIGHT_LIGHT)
            label.SetFont(font)
            
            borderSizer.Add(label, border=5, flag=wx.ALL)
            borderSizer.Add(line,  border=5, flag=wx.EXPAND|wx.ALL)
        
        borderSizer.Add(panel, border=5, flag=wx.EXPAND|wx.ALL, proportion=1)
        borderPanel.SetSizer(borderSizer)
        borderSizer.Layout()
        borderSizer.Fit(borderPanel)
        
    else:
        panel = wx.Panel(parent)

    childObjs = []
    labelObjs = []

    for i,child in enumerate(group.children):
        
        childObj = _create(panel, child, hasProps, propGui)

        # Create a label for the child if necessary
        if group.showLabels and group.childLabels[i] is not None:
            labelObj = _create(panel, group.childLabels[i], hasProps, propGui)
        else:
            labelObj = None

        labelObjs.append(labelObj) 
        childObjs.append(childObj)

    if   isinstance(group, HGroup):
        _layoutHGroup(group, panel, childObjs, labelObjs)
    elif isinstance(group, VGroup):
        _layoutVGroup(group, panel, childObjs, labelObjs)

    if group.border: return borderPanel
    else:            return panel


# These aliases are defined so we can introspectively look
# up the appropriate _create* function based upon the class
# name of the ViewItem being created, in the _create
# function below.
_createHGroup = _createGroup
_createVGroup = _createGroup


def _create(parent, viewItem, hasProps, propGui):
    """
    Creates the given ViewItem object and, if it is a group, all of its
    children.
    """

    cls = viewItem.__class__.__name__

    createFunc = getattr(sys.modules[__name__], '_create{}'.format(cls), None)

    if createFunc is None:
        raise ValueError('Unrecognised ViewItem: {}'.format(
            viewItem.__class__.__name__))

    guiObject = createFunc(parent, viewItem, hasProps, propGui)
    visibleCb = _configureVisibleWhen(viewItem, guiObject, hasProps)
    enableCb  = _configureEnabledWhen(viewItem, guiObject, hasProps)

    if visibleCb is not None: propGui.onChangeCallbacks.append(visibleCb)
    if enableCb  is not None: propGui.onChangeCallbacks.append(enableCb)

    if viewItem.tooltip is not None:

        # Add the tooltip to the GUI object, and
        # also do so recursively to any children
        def setToolTip(obj):
            
            obj.SetToolTipString(viewItem.tooltip)

            children = obj.GetChildren()
            if len(children) > 0:
                map(setToolTip, children)
        
        setToolTip(guiObject)

    propGui.guiObjects[viewItem.key] = guiObject

    return guiObject


def _defaultView(hasProps):
    """
    Creates a default view specification for the given HasProperties
    object, with all properties laid out vertically. This function is
    only called if a view specification was not provided in the call
    to the buildGUI function (defined below).
    """

    propNames, propObjs = hasProps.getAllProperties()

    widgets = [Widget(name, label=name) for name in propNames]
    
    return VGroup(label=hasProps.__class__.__name__, children=widgets)


def _prepareView(viewItem, labels, tooltips):
    """
    Recursively steps through the given viewItem and its children (if
    any). If the viewItem is a string, it is assumed to be a property
    name, and it is turned into a Widget object. If the viewItem does
    not have a label/tooltip, and there is a label/tooltip for it in
    the given labels/tooltips dict, then its label/tooltip is set.
    Returns a reference to the updated/newly created ViewItem.
    """

    if isinstance(viewItem, str):
        viewItem = Widget(viewItem)

    if not isinstance(viewItem, ViewItem):
        raise ValueError('Not a ViewItem')

    if viewItem.label   is None:
        viewItem.label   = labels  .get(viewItem.key, viewItem.key)
    if viewItem.tooltip is None:
        viewItem.tooltip = tooltips.get(viewItem.key, None) 

    if isinstance(viewItem, Group):

        # children may have been specified as a tuple,
        # so we cast it to a list, making it mutable
        viewItem.children    = list(viewItem.children)
        viewItem.childLabels = []

        for i,child in enumerate(viewItem.children):
            viewItem.children[i] = _prepareView(child, labels, tooltips)

        # Create a Label object for each 
        # child of this group if necessary
        for child in viewItem.children:

            # unless no labels are to be shown
            # for the items in this group
            mkLabel = viewItem.showLabels

            # or there is no label specified for this child
            mkLabel = mkLabel and (child.label is not None)

            # or this child is a group with a border
            mkLabel = mkLabel and not (isinstance(child, Group) and child.border)

            # unless there is no label specified
            if mkLabel: viewItem.childLabels.append(Label(child))
            else:       viewItem.childLabels.append(None)

    return viewItem

    
def _prepareEvents(hasProps, propGui):
    """
    If the visibleWhen or enabledWhen conditional attributes were set
    for any ViewItem objects, a callback function is set on all
    properties. When any property value changes, the visibleWhen/
    enabledWhen callback functions are called.
    """

    if len(propGui.onChangeCallbacks) == 0:
        return

    def onChange(*a):
        for cb in propGui.onChangeCallbacks:
            cb()
        propGui.topLevel.GetSizer().Layout()
        propGui.topLevel.Refresh()
        propGui.topLevel.Update()


    propNames, propObjs = hasProps.getAllProperties()

    # initialise widget states
    onChange()

    # add a callback listener to every property
    for propObj,propName in zip(propObjs,propNames):

        lName = 'ChangeEvent_{}'.format(propName)
        propObj.addListener(hasProps, lName, onChange)
 

def buildGUI(parent,
             hasProps,
             view=None,
             labels=None,
             tooltips=None):
    """
    Builds a GUI interface which allows the properties of the given
    hasProps object (a props.HasProperties instance) to be edited.
    Returns a reference to the top level GUI object (typically a
    wx.Frame or wx.Notebook).

    Parameters:
    
     - parent:   parent GUI object
     - hasProps: props.HasProperties object
    
    Optional:
    
     - view:     ViewItem object, specifying the interface layout
     - labels:   Dict specifying labels
     - tooltips: Dict specifying tooltips
    """

    if view is None: view = _defaultView(hasProps)

    if labels   is None: labels   = {}
    if tooltips is None: tooltips = {}

    propGui   = PropGUI()
    view      = _prepareView(view, labels, tooltips) 
    mainPanel = _create(parent, view, hasProps, propGui)
    
    propGui.topLevel = mainPanel
    _prepareEvents(hasProps, propGui)

    # TODO return the propGui object, so the caller
    # has access to all of the GUI objects that were
    # created, via the propGui.guiObjects dict. ??

    return mainPanel
