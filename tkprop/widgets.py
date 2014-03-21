#!/usr/bin/env python
#
# widgets.py - Generate widgets for tkprop property objects.
#
# The sole entry point for this module is the makeWidget function,
# which is called via the build module when it automatically
# builds a GUI for the properties of a HasProperty instance.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import sys

import os
import os.path as op

from collections import OrderedDict

import tkprop       as tkp
import Tkinter      as tk
import tkFileDialog as tkfile
import                 ttk

# the List property is complex enough to get its own module.
from tkprop.widgets_list import _List


def _setupValidation(widget, propObj, tkProp, tkVar):
    """
    Configures input validation for the given widget, which is assumed
    to be managing the given tkProp (tkprop.PropertyBase) object.  Any
    changes to the property value are validated and, if the new value
    is invalid, the widget background colour is changed to a light
    red, so that the user is aware of the invalid-ness.
    """

    invalidBGColour = '#ff9999'
    _setBG = None

    # this is a new ttk widget - we need to use
    # a style to change the background colour
    try: 
        defaultStyleName = widget['style'] or widget.winfo_class()
        invalidStyleName = 'Invalid.' + defaultStyleName

        invalidStyle = ttk.Style()
        invalidStyle.configure(invalidStyleName, background=invalidBGColour)

        def _setBG(isValid):
            if isValid: widget.configure(style=defaultStyleName)
            else:       widget.configure(style=invalidStyleName)

    # this is an old Tk widget - we change
    # the background colour directly
    except tk.TclError:

        defaultBGColour = widget['background']

        def _setBG(isValid):
            if isValid: widget.configure(background=defaultBGColour)
            else:       widget.configure(background=invalidBGColour)

    def _changeBGOnValidate(value, valid, instance, *a):
        """
        Called whenever the property value changes. Checks
        to see if the new value is valid and changes the
        widget background colour according to the validity
        of the new value.
        """
        _setBG(valid)
        
    listenerName = 'ChangeBGOnValidate_{}'.format(tkVar.name)
    tkVar.addListener(listenerName, _changeBGOnValidate)

    # Validate the initial property value,
    # so the background is appropriately set
    tkProp.forceValidation(propObj)
    

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
def _FilePath(parent, propObj, tkProp, tkVar):
    """
    Creates and returns a ttk Frame containing an Entry and a
    Button. The button, when clicked, opens a file dialog
    allowing the user to choose a file/directory to open, or
    a location to save (this depends upon how the tkprop
    [tkprop.FilePath] object was configured).
    """

    global _lastFilePathDir
    if _lastFilePathDir is None:
        _lastFilePathDir = os.getcwd()

    frame   = ttk.Frame(parent)
    textbox = ttk.Entry(frame, textvariable=tkVar.tkVar)
    _setupValidation(textbox, propObj, tkProp, tkVar)

    def chooseFile():
        global _lastFilePathDir

        if tkProp.exists:

            if tkProp.isFile:
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
            tkVar.tkVar.set(path)

    button  = ttk.Button(frame, text='Choose', command=chooseFile)

    textbox.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)
    button .pack(fill=tk.Y,    side=tk.RIGHT)
    
    return frame
    

def _Choice(parent, propObj, tkProp, tkVar):
    """
    Creates and returns a ttk Combobox allowing the
    user to set the given tkProp (tkprop.Choice) object.
    """

    # See the documentation for properties.Choice._makeTkVar
    # for an explanation of what is going on here.
    labels   = tkProp.choiceLabels
    labelVar = tkProp.getLabelVar(propObj)
    widget   = ttk.Combobox(parent, values=labels, textvariable=labelVar)

    widget.configure(state='readonly')
    
    return widget


def _String(parent, propObj, tkProp, tkVar):
    """
    Creates and returns a ttk Entry object, allowing
    the user to edit the given tkProp (tkprop.String)
    object.
    """

    widget = ttk.Entry(parent, textvariable=tkVar.tkVar)
    _setupValidation(widget, propObj, tkProp, tkVar)
    
    return widget


def _Number(parent, propObj, tkProp, tkVar):
    """
    Creates and returns a tk widget, either a ttk.Scale,
    or a tk.Spinbox, allowing the user to edit the given
    tkProp object (a tkprop.Int or tkprop.Double).
    """

    value  = tkVar.tkVar.get()
    minval = tkProp.minval
    maxval = tkProp.maxval

    makeScale = True

    # if both minval and maxval have been set, we
    # can use a Scale. Otherwise we use a spinbox.
    if any((minval is None, maxval is None)):
        makeScale = False

    # Tkinter spinboxes don't behave well if you
    # don't set both of the from_ and to limits.
    if minval is None:
        if   isinstance(tkProp, tkp.Int):    minval = -sys.maxint-1
        elif isinstance(tkProp, tkp.Double): minval = sys.float_info.min
    if maxval is None:
        if   isinstance(tkProp, tkp.Int):    maxval = sys.maxint
        elif isinstance(tkProp, tkp.Double): maxval = sys.float_info.max

    # string format, and increment magnitude, for spinboxes
    if isinstance(tkProp, tkp.Int):
        formatStr = '%0.0f'
        increment = 1
    else:
        formatStr = '%0.4f'

        if makeScale: increment = (maxval-minval)/20.0
        else:         increment = 0.5
    
    if makeScale:

        # Embed the Scale inside a Frame, along with
        # labels which display the minimum and
        # maximum and a Spinbox allowing direct
        # modification of the current value.
        scaleFrame = ttk.Frame(parent)

        widget = ttk.Scale(scaleFrame, orient=tk.HORIZONTAL,
                           from_=minval, to=maxval,
                           variable=tkVar.tkVar)

        minLabel = ttk.Label(scaleFrame, text='{}'.format(minval),
                             anchor=tk.W)

        curEntry = tk.Spinbox(scaleFrame,
                              from_=minval, to=maxval,
                              textvariable=tkVar.tkVar,
                              format=formatStr,
                              increment=increment)
        
        maxLabel = ttk.Label(scaleFrame, text='{}'.format(maxval),
                             anchor=tk.E)

        minLabel.pack(side=tk.LEFT, fill=tk.X)
        widget  .pack(side=tk.LEFT, fill=tk.X, expand=True)
        maxLabel.pack(side=tk.LEFT, fill=tk.X)
        curEntry.pack(side=tk.LEFT, fill=tk.X)

        _setupValidation(curEntry, propObj, tkProp, tkVar)
                
        widget = scaleFrame

    # The minval and maxval attributes have not both
    # been set, so we create a Spinbox instead of a Scale.
    else:
        widget = tk.Spinbox(parent,
                            from_=minval, to=maxval,
                            textvariable=tkVar.tkVar,
                            format=formatStr,
                            increment=increment)

        _setupValidation(widget, propObj, tkProp, tkVar)

    return widget


def _Double(parent, propObj, tkProp, tkVar):
    return _Number(parent, propObj, tkProp, tkVar)


def _Int(parent, propObj, tkProp, tkVar):
    return _Number(parent, propObj, tkProp, tkVar)


def _Percentage(parent, propObj, tkProp, tkVar):
    # TODO Add '%' signs to Scale labels.
    return _Number(parent, propObj, tkProp, tkVar) 
        

def _Boolean(parent, propObj, tkProp, tkVar):
    """
    Creates and returns a ttk Checkbutton, allowing the
    user to set the given tkProp (tkprop.Boolean) object.
    """

    return ttk.Checkbutton(parent, variable=tkVar.tkVar)


def makeWidget(parent, propObj, propName):
    """
    Given propObj (a tkprop.HasProperties object), propName (the name of a
    property of propObj), and parent (a Tkinter object), creates and returns a
    Tkinter widget, or a frame containing widgets, which may be used to edit
    the property.
    """

    tkProp = propObj.getTkProp(propName)
    tkVar  = propObj.getTkVar( propName)

    if any((tkProp is None, tkVar is None)):
        raise ValueError('Could not find property {}.{}'.format(
            propObj.__class__.__name__, propName))

    makeFunc = getattr(
        sys.modules[__name__],
        '_{}'.format(tkProp.__class__.__name__), None)

    if makeFunc is None:
        raise ValueError(
            'Unknown property type: {}'.format(tkProp.__class__.__name__))

    return makeFunc(parent, propObj, tkProp, tkVar)
