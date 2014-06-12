#!/usr/bin/env python
#
# floatslider.py - Provides two classes, FloatSlider and SliderSpinPanel.

# The FloatSlider class is an alternative to wx.Slider which supports
# floating point numbers.
#
# The SliderSpinPanel class is a panel containing a FloatSlider and a
# wx.SpinCtrlDouble, linked such that changes in one are reflected in the
# other.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import wx
import wx.lib.newevent as wxevent

import numberdialog

class FloatSlider(wx.Slider):
    """
    A cheap and nasty subclass of wx.Slider which supports floating point
    numbers of any range. The desired range is transformed into the range
    [-2**31, 2**31-1].
    """

    def __init__(self,
                 parent,
                 value=0,
                 minValue=0,
                 maxValue=100,
                 **kwargs):
        """
        Initialises a FloatSlider. Parameters:
          - parent:   The wx parent.
          - value:    Initial slider value
          - minValue: Minimum slider value
          - maxValue: Maximum slider value
          - kwargs:   Passed through to the wx.Slider constructor
        """

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
        """
        Return a tuple containing the (minimum, maximum) slider values.
        """
        return (self._realMin, self._realMax)

        
    def SetRange(self, minValue, maxValue):
        """
        Set the minimum/maximum slider values.
        """
        self._realMin   = float(minValue)
        self._realMax   = float(maxValue)
        if self._realMin == self._realMax:
            self._realMax = self._realMax + 1
        self._realRange = abs(self._realMin - self._realMax)

        
    def GetMin(self):
        """
        Return the minimum slider value.
        """
        return self.GetRange()[0]

    
    def GetMax(self):
        """
        Return the maximum slider value.
        """
        return self.GetRange()[1]

        
    def SetMin(self, minValue):
        """
        Set the minimum slider value.
        """
        self.SetRange(minValue, self.GetMax())

        
    def SetMax(self, maxValue):
        """
        Set the maximum slider value.
        """
        self.SetRange(self.GetMin(), maxValue)

        
    def _sliderToReal(self, value):
        """
        Converts the given value from slider space to real space.
        """
        value = self._realMin + (value - self._sliderMin) * \
            (self._realRange / self._sliderRange)
        return value

        
    def _realToSlider(self, value):
        """
        Converts the given value from real space to slider space.
        """ 
        value = self._sliderMin + (value - self._realMin) * \
            (self._sliderRange / self._realRange)
        return int(round(value))

        
    def SetValue(self, value):
        """
        Set the slider value.
        """
        value = self._realToSlider(value)

        if value < self._sliderMin: value = self._sliderMin
        if value > self._sliderMax: value = self._sliderMax

        wx.Slider.SetValue(self, value)

        
    def GetValue(self):
        """
        Returns the slider value.
        """
        value = wx.Slider.GetValue(self)
        return self._sliderToReal(value)


# Event emitted when the SliderSpinPanel value changes.
# Contains a single parameter, 'value', which contains
# the new value.
SliderSpinValueEvent, EVT_SSP_VALUE = wxevent.NewEvent()

# Event emitted when the SliderSpinPanel range changes.
# Contains two parameters, 'min' and 'max', which contain
# the new range values.
SliderSpinRangeEvent, EVT_SSP_RANGE = wxevent.NewEvent() 

class SliderSpinPanel(wx.Panel):
    """
    A panel which contains a FloatSlider and a wx.SpinCtrlDouble, linked
    such that changes to one are reflected in the other.  The class also
    provides the option to have the minimum/maximum bounds displayed on
    either side of the slider/spinbox, and to have those bounds editable
    via a button push.

    Users of the SliderSpinPanel may wish to bind listeners to the
    following events:
      - EVT_SSP_VALUE: Emitted when the slider value changes.
      - EVT_SSP_RANGE: Emitted when the slider range changes.
    """

    def __init__(self,
                 parent,
                 value,
                 minValue,
                 maxValue,
                 showBounds=True,
                 editBounds=False):
        """
        Initialises a SliderSpinPanel object. Parameters:
        
          - parent:     wx parent object.
        
          - value:      Initial slider/spin value.
        
          - minValue:   Minimum slider/spin value.
        
          - maxValue:   Maximum slider/spin value.
        
          - showBounds: If True, buttons placed on the left and right,
                        displaying the minimum/maximum bounds.
        
          - editBounds: If True, when said buttons are clicked, a dialog
                        window pops up allowing the user to edit the bound
                        values (see numberdialog.py). Has no effect if
                        showBounds is False.
        """

        wx.Panel.__init__(self, parent)

        if not showBounds: editBounds = False
        
        self._showBounds = showBounds

        self._slider = FloatSlider(
            self,
            value=value,
            minValue=minValue,
            maxValue=maxValue)
        self._spinbox = wx.SpinCtrlDouble(
            self,
            min=minValue,
            max=maxValue,
            value='{}'.format(value),
            initial=value)

        self._sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self._sizer)

        self._sizer.Add(self._slider,  flag=wx.EXPAND, proportion=1)
        self._sizer.Add(self._spinbox, flag=wx.EXPAND)

        self._slider .Bind(wx.EVT_SLIDER,         self._onSlider)
        self._spinbox.Bind(wx.EVT_SPIN,           self._onSpin)
        self._spinbox.Bind(wx.EVT_SPINCTRL,       self._onSpin)
        self._spinbox.Bind(wx.EVT_SPINCTRLDOUBLE, self._onSpin)

        if showBounds:
            self._minButton = wx.Button(self, label='{}'.format(minValue))
            self._maxButton = wx.Button(self, label='{}'.format(maxValue))

            self._sizer.Insert(0, self._minButton, flag=wx.EXPAND)
            self._sizer.Add(      self._maxButton, flag=wx.EXPAND)

            self._minButton.Enable(editBounds)
            self._maxButton.Enable(editBounds)

            self._minButton.Bind(wx.EVT_BUTTON, self._onBoundButton)
            self._maxButton.Bind(wx.EVT_BUTTON, self._onBoundButton)

        self.Layout()

        
    def _onBoundButton(self, ev):
        """
        Called when either of the minimum/maximum bound buttons are
        clicked. Pops up a numberdialog.NumberDialog window and, if
        the user changes the value, updates the slider/spin bounds,
        and emits an EVT_SSP_RANGE event.
        """

        source = ev.GetEventObject()

        if source == self._minButton:
            message = 'New minimum value'
            initVal = self.GetMin()
        elif source == self._maxButton:
            message = 'New maximum value'
            initVal = self.GetMax()
        else:
            return

        dlg = numberdialog.NumberDialog(
            self.GetTopLevelParent(),
            message=message,
            initial=initVal)

        if dlg.ShowModal() != wx.ID_OK:
            return

        if   source == self._minButton: self.SetMin(dlg.GetValue())
        elif source == self._maxButton: self.SetMax(dlg.GetValue())

        wx.PostEvent(self, SliderSpinRangeEvent(
            min=self.GetMin(),
            max=self.GetMax()))

        
    def _onSlider(self, ev):
        """
        Called when the user changes the slider value. Updates the
        spinbox value and emits an EVT_SSP_VALUE event.
        """
        val = self._slider.GetValue()
        self._spinbox.SetValue(val)
        wx.PostEvent(self, SliderSpinValueEvent(value=val)) 

        
    def _onSpin(self, ev):
        """
        Called when the user changes the spinbox value. Updates the
        slider value and emits an EVT_SSP_VALUE event.
        """
        val = self._spinbox.GetValue()
        self._slider.SetValue(val)
        wx.PostEvent(self, SliderSpinValueEvent(value=val)) 

        
    def GetRange(self):
        """
        Return a tuple containing the (minimum, maximum) slider/spinbox
        values.
        """
        return self._slider.GetRange()

        
    def GetMin(self):
        """
        Returns the minimum slider/spinbox value.
        """
        return self._slider.GetMin()

        
    def GetMax(self):
        """
        Returns the maximum slider/spinbox value.
        """
        return self._slider.GetMax()

        
    def GetValue(self):
        """
        Returns the current slider/spinbox value.
        """
        return self._slider.GetValue()

        
    def SetRange(self, minValue, maxValue):
        """
        Sets the minimum/maximum slider/spinbox values.
        """ 
        self.SetMin(minValue)
        self.SetMax(maxValue)

        
    def SetMin(self, minValue):
        """
        Sets the minimum slider/spinbox value.
        """ 
        self._slider .SetMin(minValue)
        self._spinbox.SetMin(minValue)

        if self._showBounds:
            self._minButton.SetLabel('{}'.format(minValue))

            
    def SetMax(self, maxValue):
        """
        Sets the maximum slider/spinbox value.
        """ 
        self._slider .SetMax(maxValue)
        self._spinbox.SetMax(maxValue)

        if self._showBounds:
            self._maxButton.SetLabel('{}'.format(maxValue)) 

            
    def SetValue(self, value):
        """
        Sets the current slider/spinbox value.
        """ 
        self._slider .SetValue(value)
        self._spinbox.SetValue(value)
