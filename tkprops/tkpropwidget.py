#!/usr/bin/env python
#
# tkpropwidget.py - Generate widgets for tkprop property objects.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import sys

import tkprops.tkprop as tkp

import Tkinter as tk
import            ttk


def _setupValidation(widget, propObj, tkProp):

    def _validate(oldValue, newValue):

        valid = False
        try:
            setattr(propObj, tkProp.label, newValue)
            valid = True
            
        except ValueError as e:
            setattr(propObj, tkProp.label, tkProp.default)

        widget.after_idle(lambda: widget.config(validate='focusout'))
        widget.icursor(tk.END)
 
        return valid

    vcmd = (widget.register(_validate), '%s', '%P')

    widget.config(validate='focusout', validatecommand=vcmd)
    

def _FilePath(parent, propObj, tkProp, tkVar):
    return ttk.Entry(parent, textvariable=tkVar)
    

def _Choice(parent, propObj, tkProp, tkVar):

    choices = tkProp.choices
    widget  = ttk.Combobox(parent, textvariable=tkVar, values=choices)

    return widget


def _String(parent, propObj, tkProp, tkVar):

    widget = ttk.Entry(parent, textvariable=tkVar)
    _setupValidation(widget, propObj, tkProp)
    
    return widget
    

def _Number(parent, propObj, tkProp, tkVar):

    value  = tkVar.get()
    minval = tkProp.minval
    maxval = tkProp.maxval

    makeScale = True

    if any((minval is None, maxval is None)):
        makeScale = False

    if makeScale:

        # TODO labels
        widget = ttk.Scale(parent, orient=tk.HORIZONTAL,
                           from_=minval, to=maxval,
                           variable=tkVar)
        
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

        _setupValidation(widget, propObj, tkProp)

    return widget


def _Double(parent, propObj, tkProp, tkVar):
    return _Number(parent, propObj, tkProp, tkVar)


def _Int(parent, propObj, tkProp, tkVar):
    return _Number(parent, propObj, tkProp, tkVar)


def _Boolean(parent, propObj, tkProp, tkVar):

    value = bool(tkVar.get())
    return ttk.Checkbutton(parent, variable=tkVar)


def makeWidget(parent, propObj, propName):
    """
    Given a tkprop.HasProperties object, the name of a property, and a Tkinter
    parent object, creates and returns a Tkinter widget, or a frame containing
    widgets, which may be used to edit the property.
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
