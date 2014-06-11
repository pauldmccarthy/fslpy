#!/usr/bin/env python
#
# widgets_number.py - Create widgets for modifying Number properties.
#
# The code in this file really belongs in widgets.py, but it is
# large and complex enough to warrent its own module.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import sys

import wx

import properties as props
import widgets

import fsl.gui.floatslider  as floatslider
import fsl.gui.numberdialog as numberdialog


def _makeSpinBox(parent, hasProps, propObj, propVal):
    """
    Creates a spinbox bound to given PropertyValue object.
    """

    def getMinVal(val):
        if val is not None: return val
        if   isinstance(propObj, props.Int):  return -2 ** 31 + 1
        elif isinstance(propObj, props.Real): return -sys.float_info.max
        
    def getMaxVal(val):
        if val is not None: return val
        if   isinstance(propObj, props.Int):  return 2 ** 31 - 1
        elif isinstance(propObj, props.Real): return sys.float_info.max 

    value   = propVal.get()
    minval  = propObj.getConstraint(hasProps, 'minval')
    maxval  = propObj.getConstraint(hasProps, 'maxval')
    isRange = (minval is not None) and (maxval is not None)
    params  = {}

    minval = getMinVal(minval)
    maxval = getMaxVal(maxval)
        
    if isinstance(propObj, props.Int):
        SpinCtr = wx.SpinCtrl

    elif isinstance(propObj, props.Real):
        
        SpinCtr = wx.SpinCtrlDouble

        if isRange: increment = (maxval - minval) / 100.0
        else:       increment = 0.5

        params['inc'] = increment
                
    else:
        raise TypeError('Unrecognised property type: {}'.format(
            propObj.__class__.__name__))
        
    params['min']     = minval
    params['max']     = maxval
    params['initial'] = value
    params['value']   = '{}'.format(value)

    spin = SpinCtr(parent, **params)
    
    widgets._propBind(hasProps, propObj, propVal, spin,
                      (wx.EVT_SPIN, wx.EVT_SPINCTRL, wx.EVT_SPINCTRLDOUBLE))

    def updateRange(*a):
        minval = getMinVal(propObj.getConstraint(hasProps, 'minval'))
        maxval = getMaxVal(propObj.getConstraint(hasProps, 'maxval'))
        spin.SetRange(minval, maxval)

    listenerName = 'widgets_number_py_updateRange_{}'.format(id(spin))
    propObj.addConstraintListener(hasProps, listenerName, updateRange)

    def onDestroy(ev):
        propObj.removeConstraintListener(hasProps, listenerName)
        ev.Skip()
    
    spin.Bind(wx.EVT_WINDOW_DESTROY, onDestroy)

    return spin


def _makeSlider(parent, hasProps, propObj, propVal):
    """
    Creates a slider bound to the given PropertyValue object.
    The slider is contained within a wx.Panel, which also contains
    min/max labels (or buttons if the property value bounds are
    editable).
    """

    value      = propVal.get()
    minval     = propObj.getConstraint(hasProps, 'minval')
    maxval     = propObj.getConstraint(hasProps, 'maxval')
    editBounds = propObj.getConstraint(hasProps, 'editBounds') 
    panel      = wx.Panel(parent)

    slider = floatslider.FloatSlider(
        panel,
        value=value,
        minValue=minval,
        maxValue=maxval)

    minLabel = wx.Button(panel, label='{}'.format(minval))
    maxLabel = wx.Button(panel, label='{}'.format(maxval))

    if not editBounds:
        minLabel.Disable()
        maxLabel.Disable()

    sizer = wx.BoxSizer(wx.HORIZONTAL)
        
    sizer.Add(minLabel) 
    sizer.Add(slider, flag=wx.EXPAND, proportion=1)
    sizer.Add(maxLabel)

    panel.SetSizer(sizer)
    panel.SetAutoLayout(1)
    sizer.Fit(panel)

    # Update slider min/max bounds and labels
    # whenever the property constraints change.    
    def updateRange(*a):
        minval = propObj.getConstraint(hasProps, 'minval')
        maxval = propObj.getConstraint(hasProps, 'maxval')

        minLabel.SetLabel('{}'.format(minval))
        maxLabel.SetLabel('{}'.format(maxval))
        
        slider.SetMin(minval)
        slider.SetMax(maxval)
        
        # The wx.Slider value changes when its bounds
        # are changed. It does this to keep the slider
        # position the same as before, but we don't
        # want that  ...
        slider.SetValue(propVal.get())


    widgets._propBind(hasProps, propObj, propVal, slider,
                      (wx.EVT_SPIN, wx.EVT_SPINCTRL))

    listenerName = 'widgets_number_py_updateRange_{}'.format(id(slider))
    propObj.addConstraintListener(hasProps, listenerName, updateRange)

    def onDestroy(ev):
        propObj.removeConstraintListener(hasProps, listenerName)
        ev.Skip()
    
    slider.Bind(wx.EVT_WINDOW_DESTROY, onDestroy)

    if editBounds:

        # When one of the min/max label buttons are pushed, pop
        # up a dialog allowing the user to enter a new value
        def editBounds(minbound):

            if minbound:
                constraint = 'minval'
                labeltxt   = 'New minimum value'
            else:
                constraint = 'maxval'
                labeltxt   = 'New maximum value'

            dlg = numberdialog.NumberDialog(
                panel.GetTopLevelParent(),
                message=labeltxt)

            if dlg.ShowModal() == wx.ID_OK:
                propObj.setConstraint(hasProps, constraint, dlg.GetValue())
            
        minLabel.Bind(wx.EVT_BUTTON,  lambda ev: editBounds(True))
        maxLabel.Bind(wx.EVT_BUTTON,  lambda ev: editBounds(False))

    return panel


def _Number(parent, hasProps, propObj, propVal):
    """
    Creates and returns a widget allowing the user to edit
    the given property (a props.Int or props.Real).
    """

    minval  = propObj.getConstraint(hasProps, 'minval')
    maxval  = propObj.getConstraint(hasProps, 'maxval')
    isRange = (minval is not None) and (maxval is not None)

    if not isRange:
        return _makeSpinBox(parent, hasProps, propObj, propVal)

    panel = wx.Panel(parent)
    sizer = wx.BoxSizer(wx.HORIZONTAL)

    spin   = _makeSpinBox(panel, hasProps, propObj, propVal)
    slider = _makeSlider( panel, hasProps, propObj, propVal)

    sizer.Add(slider, flag=wx.EXPAND, proportion=1)
    sizer.Add(spin,   flag=wx.EXPAND)

    panel.SetSizer(sizer)
    panel.SetAutoLayout(1)
    sizer.Fit(panel)
    
    return panel
