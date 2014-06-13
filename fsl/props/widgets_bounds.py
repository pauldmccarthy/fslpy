#!/usr/bin/env python
#
# widgets_bounds.py - Create widgets for modifying Bounds properties.
#
# This module is not intended to be used directly - it is imported
# into the props.widgets namespace.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import wx

import fsl.gui.rangeslider as rangeslider

def _boundBind(hasProps, propObj, sliderPanel, propVal, axis):
    """
    Binds the given RangeSliderSpinPanel to the given BoundValueList
    so that changes in one are propagated to the other.
    """

    lName      = 'BoundBind_{}'.format(id(sliderPanel))
    editLimits = propObj.getConstraint(hasProps, 'editLimits')    
    lowProp    = propVal.getPropertyValueList()[axis * 2]
    highProp   = propVal.getPropertyValueList()[axis * 2 + 1]

    def lowGuiUpdate(value, *a):
        if sliderPanel.GetLow() == value: return
        sliderPanel.SetLow(value)
        
    def highGuiUpdate(value, *a):
        if sliderPanel.GetHigh() == value: return
        sliderPanel.SetHigh(value)

    def propUpdate(ev):
        lowProp .set(ev.low)
        highProp.set(ev.high)
        ev.Skip()

    def updateSliderRange(*a):
        minval = propVal.getMin(axis)
        maxval = propVal.getMax(axis)
        sliderPanel.SetLimits(minval, maxval)

    def updatePropRange(ev):
        propVal.setMin(axis, ev.min)
        propVal.setMax(axis, ev.max)
        ev.Skip()

    sliderPanel.Bind(rangeslider.EVT_RANGE, propUpdate)

    lowProp .addListener(lName, lowGuiUpdate)
    highProp.addListener(lName, highGuiUpdate)

    propObj.addItemConstraintListener(
        hasProps, axis * 2,     lName, updateSliderRange)
    propObj.addItemConstraintListener(
        hasProps, axis * 2 + 1, lName, updateSliderRange)

    if editLimits:
        sliderPanel.Bind(rangeslider.EVT_RANGE_LIMIT, updatePropRange)

    def onDestroy(ev):
        lowProp .removeListener(lName)
        highProp.removeListener(lName)
        propObj.removeItemConstraintListener(hasProps, axis * 2,     lName)
        propObj.removeItemConstraintListener(hasProps, axis * 2 + 1, lName)
        ev.Skip()
        
    sliderPanel.Bind(wx.EVT_WINDOW_DESTROY, onDestroy)


def _Bounds(parent, hasProps, propObj, propVal):
    """
    Creates and returns a panel containing sliders/spinboxes which allow
    the user to edit the low/high values along each dimension of the
    given Bounds property.
    """

    ndims    = propObj._ndims
    labels   = propObj._labels
    panel    = wx.Panel(parent)
    sizer    = wx.BoxSizer(wx.VERTICAL)

    if labels is None: labels = [None] * 2 * ndims
    
    panel.SetSizer(sizer)

    for i in range(ndims):
        editLimits  = propObj.getConstraint(hasProps, 'editLimits')
        minDistance = propObj.getConstraint(hasProps, 'minDistance')
        minval      = propVal.getMin(i)
        maxval      = propVal.getMax(i)
        loval       = propVal.getLo(i)
        hival       = propVal.getHi(i)

        if editLimits  is None: editLimits  = False
        if minDistance is None: minDistance = 0
        if minval      is None: minval      = loval
        if maxval      is None: maxval      = hival
        slider = rangeslider.RangeSliderSpinPanel(
            panel,
            minValue=minval,
            maxValue=maxval,
            lowValue=loval,
            highValue=hival,
            lowLabel=labels[i * 2],
            highLabel=labels[i * 2 + 1],
            minDistance=minDistance, 
            showLimits=True,
            editLimits=editLimits)

        sizer.Add(slider, flag=wx.EXPAND)

        _boundBind(hasProps, propObj, slider, propVal, i)

    panel.Layout()
    return panel
