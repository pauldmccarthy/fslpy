#!/usr/bin/env python
#
# widgets.py - Generate widgets for tkprop property objects.
#
# The sole entry point for this module is the makeWidget function. You
# don't need to worry about the rest of the code.
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
    to be managing the given tkProp (tkprop.PropertyBase) object.  When
    a new value is entered into the widget, as soon as the widget loses
    focus, the new value is passed to the validate() method of the
    property object. If the validate method raises an error, the
    property (and widget) value is reverted to its previous value
    (which was previously stored when the widget gained focus).
    """

    # Container used for storing the previous value of the property,
    # and sharing this value amongst the inner functions below.
    oldValue = [0]

    # When the widget receives focus, save the current
    # property value, so we can roll back to it if
    # necessary
    def _focused(event):
        oldValue[0] = tkVar.get()

    # When the widget loses focus, pass the entered
    # value to the property validate() method. 
    def _validate(newValue):

        try:
            tkProp.validate(propObj, newValue)
            return True
            
        except ValueError as e:
            return False

    # If the new value is invalid, revert
    # the property to its former value
    def _invalid():

        tkVar.set(oldValue[0])

        # The tk validation type is reset on some (not all)
        # widgets, if the invalidcommand (this function)
        # modifies the tk control variable.  So here we
        # just re-initialise validation on the widget.
        widget.after_idle(lambda: widget.config(validate='focusout'))

    # Set up all of the validation and event callbacks
    vcmd   = (widget.register(_validate), '%P')
    invcmd = (widget.register(_invalid),)
    
    widget.bind('<FocusIn>', _focused)
    widget.config(
        validate='focusout',
        validatecommand=vcmd,
        invalidcommand=invcmd)


# This variable is used to retain the most recently
# visited directory in file dialogs. New file dialogs
# are initialised to display this directory.
#
# This is currently a global setting, but it may be
# more appropriate to make it a per-widget setting.
# Easily done, just make this a dict, with the widget
# (or property name) as the key.
_lastFilePathDir = None
def _FilePath(parent, propObj, tkProp, tkVar):
    """
    Creates and returns a tk Frame containing an Entry and a
    Button. The button, when clicked, opens a file dialog
    allowing the user to choose a file/directory to open, or
    a location to save (this depends upon how the tkprop
    [tkprop.FilePath] object was configured).
    """

    global _lastFilePathDir
    if _lastFilePathDir is None:
        _lastFilePathDir = os.getcwd()

    frame   = tk.Frame(parent)
    textbox = ttk.Entry(frame, textvariable=tkVar)
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

        if path is not None:
            _lastFilePathDir = op.dirname(path)
            tkVar.set(path)

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
    labelVar = getattr(propObj, '{}_tkLabelVar'.format(tkProp.label))

    widget  = ttk.Combobox(parent,
                           values=labels,
                           textvariable=labelVar,
                           state='readonly')
    
    return widget


def _String(parent, propObj, tkProp, tkVar):
    """
    Creates and returns a ttk Entry object, allowing
    the user to set the given tkPRop (tkprop.String)
    object.
    """

    widget = ttk.Entry(parent, textvariable=tkVar)
    _setupValidation(widget, propObj, tkProp, tkVar)
    
    return widget



def _Number(parent, propObj, tkProp, tkVar):
    """
    Creates and returns a tk widget, either a ttk.Scale,
    or a tk.Spinbox, allowing the user to set the given
    tkProp object (either a tkprop.Int or tkprop.Double).
    """

    value  = tkVar.get()
    minval = tkProp.minval
    maxval = tkProp.maxval

    makeScale = True

    # if both minval and maxval have been set, we
    # can use a Scale. Otherwise we use a spinbox.
    if any((minval is None, maxval is None)):
        makeScale = False

    if makeScale:

        # Embed the Scale inside a Frame, along with
        # labels which display the minimum and
        # maximum and a Spinbox allowing direct
        # modification of the current value.
        scaleFrame = ttk.Frame(parent)
        scaleFrame.columnconfigure(0, weight=1)
        scaleFrame.columnconfigure(1, weight=1)
        scaleFrame.columnconfigure(2, weight=1)

        widget = ttk.Scale(scaleFrame, orient=tk.HORIZONTAL,
                           from_=minval, to=maxval,
                           variable=tkVar)

        minLabel = ttk.Label(scaleFrame, text='{}'.format(minval),
                             anchor=tk.W)
        
        curLabel = tk.Spinbox(scaleFrame,
                              from_=minval, to=maxval,
                              textvariable=tkVar,
                              format='%0.6f',
                              increment=(maxval-minval)/20.0)
        
        maxLabel = ttk.Label(scaleFrame, text='{}'.format(maxval),
                             anchor=tk.E)

        widget  .grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W,
                      columnspan=3)
        minLabel.grid(row=1, column=0, sticky=tk.W)
        curLabel.grid(row=1, column=1)
        maxLabel.grid(row=1, column=2, sticky=tk.E)

        _setupValidation(curLabel, propObj, tkProp, tkVar)
                
        widget = scaleFrame

    # The minval and maxval attributes have not both
    # been set, so we create a Spinbox instead of a Scale.
    else:

        # Tkinter spinboxes don't behave well if you
        # don't set both of the from_ and to limits.
        if minval is None:
            if   isinstance(tkProp, tkp.Int):    minval = -sys.maxint-1
            elif isinstance(tkProp, tkp.Double): minval = sys.float_info.min
        if maxval is None:
            if   isinstance(tkProp, tkp.Int):    maxval = sys.maxint
            elif isinstance(tkProp, tkp.Double): maxval = sys.float_info.max

        widget = tk.Spinbox(parent,
                            from_=minval, to=maxval,
                            textvariable=tkVar,
                            increment=1)

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

    value = bool(tkVar.get())
    return ttk.Checkbutton(parent, variable=tkVar)


def makeWidget(parent, propObj, propName):
    """
    Given propObj (a tkprop.HasProperties object), propName (the name of a
    property of propObj), and parent (a Tkinter object), creates and returns a
    Tkinter widget, or a frame containing widgets, which may be used to edit
    the property.
    """

    tkProp = getattr(propObj, '{}_tkProp'.format(propName), None)
    tkVar  = getattr(propObj, '{}_tkVar' .format(propName), None)

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
