#!/usr/bin/env python
#
# floatslider.py - An alternative to wx.Slider  which supports floating
#                  point numbers.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import wx

class FloatSlider(wx.Slider):
    """
    A cheap and nasty subclass of wx.Slider which supports floating point
    numbers of any range. The desired range is transformed into the range
    [-2**31, 2**31-1].
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
