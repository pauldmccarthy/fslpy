#!/usr/bin/env python
#
# widgets.py - Generate wx GUI widgets for props.PropertyBase objects.
#
# The sole entry point for this module is the makeWidget function,
# which is called via the build module when it automatically
# builds a GUI for the properties of a props.HasProperties instance.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import sys

import os
import os.path as op

import logging

from collections import OrderedDict
from collections import Iterable

import wx

# the List property is complex enough to get its own module.
from widgets_list import _List

import properties as props


def _propBind(hasProps, propObj, propVal, guiObj, evType, labelMap=None):

    if not isinstance(evType, Iterable): evType = [evType]

    listenerName = 'propBind_{}'.format(id(guiObj))
    valMap       = None

    if labelMap is not None:
        valMap = dict([(lbl,val) for (val,lbl) in labelMap.items()])

    def _guiUpdate(value, *a):

        if guiObj.GetValue() == value: return

        if valMap is not None: guiObj.SetValue(valMap[value])
        else:                  guiObj.SetValue(value)
        
    def _propUpdate(*a):

        # TODO remove property value listener when GUI object is destroyed
        try:
            value = guiObj.GetValue()
        except:
            raise

        if propVal.get() == value: return

        if labelMap is not None: propVal.set(labelMap[value])
        else:                    propVal.set(value)

    guiObj.SetValue(propVal.get())

    for ev in evType: guiObj.Bind(ev, _propUpdate)
    
    propVal.addListener(listenerName, _guiUpdate)


def _setupValidation(widget, hasProps, propObj, propVal):
    """
    Configures input validation for the given widget, which is assumed
    to be managing the given prop (props.PropertyBase) object.  Any
    changes to the property value are validated and, if the new value
    is invalid, the widget background colour is changed to a light
    red, so that the user is aware of the invalid-ness.
    """

    invalidBGColour = '#ff9999'
    validBGColour   = widget.GetBackgroundColour()

    def _changeBGOnValidate(value, valid, instance, *a):
        """
        Called whenever the property value changes. Checks
        to see if the new value is valid and changes the
        widget background colour according to the validity
        of the new value.
        """
        if valid: widget.SetBackgroundColour(validBGColour)
        else:     widget.SetBackgroundColour(invalidBGColour)

        widget.Refresh()

    # We add a callback listener to the PropertyValue object,
    # rather than to the PropertyBase, as one property may be
    # associated with multiple variables, and we don't want
    # the widgets associated with those other variables to
    # change background.
    propVal.addListener('changeBGOnValidate', _changeBGOnValidate)

    # Validate the initial property value,
    # so the background is appropriately set
    _changeBGOnValidate(None, propVal.isValid(), None)
    

# The _lastFilePathDir variable is used to retain the
# most recentlyvisited directory in file dialogs. New
# file dialogs are initialised to display this
# directory.
#
# This is currently a global setting, but it may be
# more appropriate to make it a per-widget setting.
# Easily done, just make this a dict, with the widget
# (or property name) as the key.
_lastFilePathDir = None
def _FilePath(parent, hasProps, propObj, propVal):
    """
    Creates and returns a ttk Frame containing an Entry and a
    Button. The button, when clicked, opens a file dialog
    allowing the user to choose a file/directory to open, or
    a location to save (this depends upon how the propObj
    [props.FilePath] object was configured).
    """

    tkVar = _createTkVar(propVal, tk.StringVar)

    global _lastFilePathDir
    if _lastFilePathDir is None:
        _lastFilePathDir = os.getcwd()

    frame   = ttk.Frame(parent)
    textbox = ttk.Entry(frame, textvariable=tkVar)
    _setupValidation(textbox, hasProps, propObj, propVal)

    def chooseFile():
        global _lastFilePathDir

        if propObj.exists:

            if propObj.isFile:
                path = tkfile.askopenfilename(
                    initialdir=_lastFilePathDir,
                    title='Open file')
            else:
                path = tkfile.askdirectory(
                    initialdir=_lastFilePathDir,
                    title='Open directory') 

        else:
            path = tkfile.asksaveasfilename(
                initialdir=_lastFilePathDir,
                title='Save file')

        if path != '' and path is not None:
            _lastFilePathDir = op.dirname(path)
            tkVar.set(path)

    button = ttk.Button(frame, text='Choose', command=chooseFile)

    textbox.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)
    button .pack(fill=tk.Y,    side=tk.RIGHT)
    
    return frame
    

def _Choice(parent, hasProps, propObj, propVal):
    """
    Creates and returns a ttk Combobox allowing the
    user to set the given propObj (props.Choice) object.
    """

    choices = propObj.choices
    labels  = propObj.choiceLabels
    
    valMap  = OrderedDict(zip(choices, labels))
    tkVar   = _createTkVar(propVal, tk.StringVar, valMap)

    widget  = ttk.Combobox(parent, values=labels, textvariable=tkVar)

    widget.configure(state='readonly')
    
    return widget


def _String(parent, hasProps, propObj, propVal):
    """
    Creates and returns a ttk Entry object, allowing
    the user to edit the given propObj (props.String)
    object.
    """

    widget = wx.TextCtrl(parent)

    _propBind(hasProps, propObj, propVal, widget, wx.EVT_TEXT)
    
    return widget


def _Number(parent, hasProps, propObj, propVal):
    """
    Creates and returns a widget allowing the user to edit
    the given property (a props.Int or props.Double).
    """

    value   = propVal.get()
    minval  = propObj.minval
    maxval  = propObj.maxval

    if   isinstance(propObj, props.Int):    SpinCtr = wx.SpinCtrl
    elif isinstance(propObj, props.Double): SpinCtr = wx.SpinCtrlDouble
        
    else:
        raise TypeError('Unrecognised property type: {}'.format(
            propObj.__class__.__name__))

    makeSlider = (minval is not None) and (maxval is not None)

    if   isinstance(propObj, props.Int):    increment = None
    elif isinstance(propObj, props.Double):
        if makeSlider: increment = (maxval-minval)/20.0
        else:          increment = 0.5

    params = {}
    if increment is not None: params['inc']     = increment
    if minval    is not None: params['min']     = minval
    if maxval    is not None: params['max']     = maxval
    if value     is not None: params['initial'] = value

    # The minval and maxval attributes have not both
    # been set, so we create a spinbox instead of a slider.
    if not makeSlider:

        widget = SpinCtr(parent, **params)
        
        _propBind(hasProps, propObj, propVal, widget,
                  [wx.EVT_SPINCTRL, wx.EVT_TEXT])
        _setupValidation(widget, hasProps, propObj, propVal)

    # if both minval and maxval have been set, we can use a slider. 
    else:

        panel = wx.Panel(parent)

        slider = wx.Slider(
            panel,
            value=value,
            minValue=minval,
            maxValue=maxval)

        spin = SpinCtr(panel, **params)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        panel.SetSizer(sizer)
        sizer.Add(slider, flag=wx.EXPAND, proportion=1)
        sizer.Add(spin)

        sizer.Layout()

        _propBind(hasProps, propObj, propVal, slider, wx.EVT_SLIDER)
        _propBind(hasProps, propObj, propVal, spin,   wx.EVT_SPINCTRL)
        _setupValidation(spin, hasProps, propObj, propVal)

        widget = panel


    return widget


def _Double(parent, hasProps, propObj, propVal):
    return _Number(parent, hasProps, propObj, propVal)


def _Int(parent, hasProps, propObj, propVal):
    return _Number(parent, hasProps, propObj, propVal)


def _Percentage(parent, hasProps, propObj, propVal):
    # TODO Add '%' signs to Scale labels.
    return _Number(parent, hasProps, propObj, propVal) 
        

def _Boolean(parent, hasProps, propObj, propVal):
    """
    Creates and returns a check box, allowing the user
    to set the given propObj (props.Boolean) object.
    """

    checkBox = wx.CheckBox(parent)
    _propBind(hasProps, propObj, propVal, checkBox, wx.EVT_CHECKBOX)
    return checkBox


def makeWidget(parent, hasProps, propName):
    """
    Given hasProps (a props.HasProperties object), propName (the name
    of a property of hasProps), and parent GUI object, creates and
    returns a widget, or a frame containing widgets, which may be
    used to edit the property.
    """

    propObj = hasProps.getProp(propName)
    propVal = propObj.getPropVal(hasProps)

    if propObj is None:
        raise ValueError('Could not find property {}.{}'.format(
            hasProps.__class__.__name__, propName))

    makeFunc = getattr(
        sys.modules[__name__],
        '_{}'.format(propObj.__class__.__name__), None)

    if makeFunc is None:
        raise ValueError(
            'Unknown property type: {}'.format(propObj.__class__.__name__))

    return makeFunc(parent, hasProps, propObj, propVal)
