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

class FloatSlider(wx.Slider):
    """
    A cheap and nasty subclass of wx.Slider which supports floating point
    numbers of any range. The desired range is transformed into the range
    [-2**31+1, 2**31].
    """

    def __init__(self,
                 parent,
                 value,
                 minValue,
                 maxValue,
                 **kwargs):

        self._sliderMin   = -2 ** 31
        self._sliderMax   =  2 ** 31 - 1
        self._sliderRange = abs(self._sliderMax - self._sliderMin)

        self.SetRange(minValue, maxValue)

        value = self._realToSlider(value)
        
        wx.Slider.__init__(self,
                           parent,
                           value=value,
                           minValue=self._sliderMin,
                           maxValue=self._sliderMax,
                           **kwargs)

    def GetRange(self):
        return (self._realMin, self._realMax)

    def SetRange(self, minValue, maxValue):
        self._realMin   = float(minValue)
        self._realMax   = float(maxValue)
        if self._realMin == self._realMax:
            self._realMax = self._realMax + 0.01
        self._realRange = abs(self._realMin - self._realMax)
    
    def GetMin(self): return self.GetRange()[0]
    def GetMax(self): return self.GetRange()[1]
    
    def SetMin(self, minValue): self.SetRange(minValue, self.GetMax())
    def SetMax(self, maxValue): self.SetRange(self.GetMin(), maxValue)

    def _sliderToReal(self, value):
        value = self._realMin + (value - self._sliderMin) * \
            (self._realRange / self._sliderRange)
        return value
        
    def _realToSlider(self, value):
        value = self._sliderMin + (value - self._realMin) * \
            (self._sliderRange / self._realRange)
        return int(round(value))

    def SetValue(self, value):
        value = self._realToSlider(value)
        wx.Slider.SetValue(self, value)

    def GetValue(self):
        value = wx.Slider.GetValue(self)
        return self._sliderToReal(value)


def _makeSpinBox(parent, hasProps, propObj, propVal):
    """
    """

    def getMinVal(val):
        if val is not None: return val
        if   isinstance(propObj, props.Int):    return -2 ** 31 + 1
        elif isinstance(propObj, props.Double): return -sys.float_info.max
        
    def getMaxVal(val):
        if val is not None: return val
        if   isinstance(propObj, props.Int):    return 2 ** 31 - 1
        elif isinstance(propObj, props.Double): return sys.float_info.max 

    value   = propVal.get()
    minval  = propObj.getConstraint(hasProps, 'minval')
    maxval  = propObj.getConstraint(hasProps, 'maxval')
    isRange = (minval is not None) and (maxval is not None)
    params  = {}

    minval = getMinVal(minval)
    maxval = getMaxVal(maxval)
        
    if isinstance(propObj, props.Int):
        SpinCtr = wx.SpinCtrl

    elif isinstance(propObj, props.Double):
        
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
    
    spin.Bind(
        wx.EVT_WINDOW_DESTROY,
        lambda ev: propObj.removeConstraintListener(hasProps, listenerName))

    return spin


def _makeSlider(parent, hasProps, propObj, propVal):
    """
    """

    value   = propVal.get()
    minval  = propObj.getConstraint(hasProps, 'minval')
    maxval  = propObj.getConstraint(hasProps, 'maxval') 
    panel   = wx.Panel(parent)

    slider = FloatSlider(
        panel,
        value=value,
        minValue=minval,
        maxValue=maxval)

    minLabel = wx.StaticText(panel, label='{}'.format(minval))
    maxLabel = wx.StaticText(panel, label='{}'.format(maxval))

    sizer = wx.BoxSizer(wx.HORIZONTAL)
        
    sizer.Add(minLabel) 
    sizer.Add(slider, flag=wx.EXPAND, proportion=1)
    sizer.Add(maxLabel)

    panel.SetSizer(sizer)
    panel.SetAutoLayout(1)
    sizer.Fit(panel)

    def updateRange(*a):
        minval = propObj.getConstraint(hasProps, 'minval')
        maxval = propObj.getConstraint(hasProps, 'maxval')

        minLabel.SetLabel('{}'.format(minval))
        maxLabel.SetLabel('{}'.format(maxval))
        
        slider.SetRange(minval, maxval)

    widgets._propBind(hasProps, propObj, propVal, slider,
                      (wx.EVT_SPIN, wx.EVT_SPINCTRL))

    listenerName = 'widgets_number_py_updateRange_{}'.format(id(slider))
    propObj.addConstraintListener(hasProps, listenerName, updateRange)
    
    slider.Bind(
        wx.EVT_WINDOW_DESTROY,
        lambda ev: propObj.removeConstraintListener(hasProps, listenerName)) 

    return panel


def _Number(parent, hasProps, propObj, propVal):
    """
    Creates and returns a widget allowing the user to edit
    the given property (a props.Int or props.Double).
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
