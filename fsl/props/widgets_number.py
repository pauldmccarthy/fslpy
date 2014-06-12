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
    editLimits = propObj.getConstraint(hasProps, 'editLimits') 

    slider = floatslider.SliderSpinPanel(
        parent,
        value=value,
        minValue=minval,
        maxValue=maxval,
        showLimits=True,
        editLimits=editLimits)

    # bind the slider value to the property value
    widgets._propBind(
        hasProps, propObj, propVal, slider, floatslider.EVT_SSP_VALUE)

    # Update slider min/max bounds and labels
    # whenever the property constraints change.    
    def updateSliderRange(*a):
        minval = propObj.getConstraint(hasProps, 'minval')
        maxval = propObj.getConstraint(hasProps, 'maxval')
        
        slider.SetRange(minval, maxval)
        # TODO check that value has changed due to the range change?


    listenerName = 'widgets_number_py_updateRange_{}'.format(id(slider))
    propObj.addConstraintListener(hasProps, listenerName, updateSliderRange)

    # remove the listener when the slider is destroyed
    def onDestroy(ev):
        propObj.removeConstraintListener(hasProps, listenerName)
        ev.Skip()
    
    slider.Bind(wx.EVT_WINDOW_DESTROY, onDestroy)

    if editLimits:

        # When the user edits the slider bounds,
        # update the property constraints
        def updatePropRange(ev):
            propObj.setConstraint(hasProps, 'minval', ev.min)
            propObj.setConstraint(hasProps, 'maxval', ev.max)

        slider.Bind(floatslider.EVT_SSP_LIMIT, updatePropRange)

    return slider


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
    else:
        return _makeSlider( parent, hasProps, propObj, propVal)
