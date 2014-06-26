#!/usr/bin/env python
#
# floatslider.py - Floating point slider widgets.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Floating point slider widgets.

Provides two classes, :class:`FloatSlider` and :class:`SliderSpinPanel`.

The :class:`FloatSlider` class is an alternative to :class:`wx.Slider` which
supports floating point numbers.

The :class:`SliderSpinPanel` class is a panel containing a :class:`FloatSlider`
and a :class:`wx.SpinCtrlDouble`, linked such that changes in one are reflected
in the other. The :class:`SliderSpinPanel` class also allows the user to change
the slider limits, via the :class:`~fsl.gui.numberdialog.NumberDialog` class.
"""

import wx
import wx.lib.newevent as wxevent

import numberdialog

class FloatSlider(wx.Slider):
    """Floating point slider widget.
    
    A cheap and nasty subclass of :class:`wx.Slider` which supports floating
    point numbers of any range. The desired range is transformed into the
    internal range :math:`[-2^{31}, 2^{31-1}]`.
    """

    def __init__(self,
                 parent,
                 value=None,
                 minValue=None,
                 maxValue=None,
                 **kwargs):
        """Initialise a FloatSlider.

        :param parent:         The :mod:`wx` parent object.
        
        :param float value:    Initial slider value.
        
        :param float minValue: Minimum slider value.
        
        :param float maxValue: Maximum slider value.
        
        :param kwargs:         Passed through to the :class:`wx.Slider`
                               constructor.
        """

        if value    is None: value    = 0
        if minValue is None: minValue = 0
        if maxValue is None: maxValue = 1
        
        self.__sliderMin   = -2 ** 31
        self.__sliderMax   =  2 ** 31 - 1
        self.__sliderRange = abs(self.__sliderMax - self.__sliderMin)

        wx.Slider.__init__(self,
                           parent,
                           minValue=self.__sliderMin,
                           maxValue=self.__sliderMax,
                           **kwargs)

        self.__SetRange(minValue, maxValue)
        self.SetValue(value)
        

    def GetRange(self):
        """Return a tuple containing the (minimum, maximum) slider values."""
        return (self.__realMin, self.__realMax)


    def __SetRange(self, minValue, maxValue):
        """Set the minimum/maximum slider values.

        This logic is not in the public :meth:`SetRange` method so
        we can overcome a chicken-and-egg problem in :meth:`__init__` -
        :meth:`SetValue` needs :attr:`__realMin` and :attr:`__realMax`
        to be set, but :meth:`SetRange` needs to retrieve the value
        before setting :attr:`__realMin` and :attr:`__realMax`.
        """ 

        self.__realMin   = float(minValue)
        self.__realMax   = float(maxValue)
        if self.__realMin == self.__realMax:
            self.__realMax = self.__realMax + 1
        self.__realRange = abs(self.__realMin - self.__realMax)

        
    def SetRange(self, minValue, maxValue):
        """Set the minimum/maximum slider values."""

        # wx.Slider values change when their bounds
        # are changed. It does this to keep the
        # slider position the same as before, but I
        # think it is more appropriate to keep the
        # slider value the same ... 
        oldValue = self.GetValue()
        self.__SetRange(minValue, maxValue)
        self.SetValue(oldValue)

        
    def GetMin(self):
        """Return the minimum slider value."""
        return self.GetRange()[0]

    
    def GetMax(self):
        """Return the maximum slider value."""
        return self.GetRange()[1]

        
    def SetMin(self, minValue):
        """Set the minimum slider value."""
        self.SetRange(minValue, self.GetMax())

        
    def SetMax(self, maxValue):
        """Set the maximum slider value."""
        self.SetRange(self.GetMin(), maxValue)

        
    def __sliderToReal(self, value):
        """Converts the given value from slider space to real space."""
        value = self.__realMin + (value - self.__sliderMin) * \
            (self.__realRange / self.__sliderRange)
        return value

        
    def __realToSlider(self, value):
        """Converts the given value from real space to slider space.""" 
        value = self.__sliderMin + (value - self.__realMin) * \
            (self.__sliderRange / self.__realRange)
        return int(round(value))

        
    def SetValue(self, value):
        """Set the slider value."""
        value = self.__realToSlider(value)

        if value < self.__sliderMin: value = self.__sliderMin
        if value > self.__sliderMax: value = self.__sliderMax

        wx.Slider.SetValue(self, value)

        
    def GetValue(self):
        """Returns the slider value."""
        value = wx.Slider.GetValue(self)
        return self.__sliderToReal(value)


_SliderSpinValueEvent, _EVT_SSP_VALUE = wxevent.NewEvent()
_SliderSpinLimitEvent, _EVT_SSP_LIMIT = wxevent.NewEvent()


EVT_SSP_VALUE        = _EVT_SSP_VALUE
"""Identifier for the :data:`SliderSpinValueEvent`."""


EVT_SSP_LIMIT        = _EVT_SSP_LIMIT
"""Identifier for the :data:`SliderSpinLimitEvent`."""


SliderSpinValueEvent = _SliderSpinValueEvent
"""Event emitted when the :class:`SliderSpinPanel` value
changes. Contains a single attribute, ``value``, which
contains the new value.
"""


SliderSpinLimitEvent = _SliderSpinLimitEvent
"""Event emitted when the :class:`SliderSpinPanel` limits
change. Contains two attributes, ``min`` and ``max``, which
contain the new limit values.
"""


class SliderSpinPanel(wx.Panel):
    """A panel containing a :class:`FloatSlider` and a
    :class:`wx.SpinCtrlDouble`.

    The slider and spinbox are linked such that changes to one are
    reflected in the other.  The :class:`SliderSpinPanel` class also
    provides the option to have the minimum/maximum limits displayed
    on either side of the slider/spinbox, and to have those limits
    editable via a button push.

    Users of the :class:`SliderSpinPanel` may wish to bind listeners to
    the following events:
    
      - :data:`EVT_SSP_VALUE`: Emitted when the slider value changes.
    
      - :data:`EVT_SSP_LIMIT`: Emitted when the slider limits change.
    """

    def __init__(self,
                 parent,
                 real=True,
                 value=None,
                 minValue=None,
                 maxValue=None,
                 label=None,
                 showLimits=True,
                 editLimits=False):
        """
        Initialise a :class:`SliderSpinPanel` object.

        :param parent:          The :mod:`wx` parent object.

        :param bool real:       If ``False``, a :class:`wx.Slider` and
                                :class:`wx.SpinCtrl` are used, instead of a
                                :class:`FloatSlider` and
                                :class:`wx.SpinCtrlDouble`.
        
        :param number value:    Initial slider/spin value.
        
        :param number minValue: Minimum slider/spin value.
        
        :param number maxValue: Maximum slider/spin value.

        :param str label:       If not ``None``, a :class:`wx.StaticText`
                                widget is added to the left of the slider,
                                containing the given label.
        
        :param bool showLimits: If ``True``, buttons placed on the left and
                                right, displaying the minimum/maximum limits.
        
        :param bool editLimits: If ``True``, when said buttons are clicked, a
                                :class:`~fsl.gui.numberdialog.NumberDialog`
                                window pops up allowing the user to edit the
                                limit values. Has no effect if ``showLimits``
                                is ``False``.
        """

        wx.Panel.__init__(self, parent)

        if value    is None: value    = 0
        if minValue is None: minValue = 0
        if maxValue is None: maxValue = 1 

        if not showLimits: editLimits = False
        
        self._showLimits = showLimits

        if real:
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
        else:
            self._slider = wx.Slider(
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

        if label is not None:
            self._label = wx.StaticText(self, label=label)
            self._sizer.Add(self._label, flag=wx.EXPAND)

        self._sizer.Add(self._slider,  flag=wx.EXPAND, proportion=1)
        self._sizer.Add(self._spinbox, flag=wx.EXPAND)

        self._slider .Bind(wx.EVT_SLIDER,         self._onSlider)
        self._spinbox.Bind(wx.EVT_SPINCTRLDOUBLE, self._onSpin)

        if showLimits:
            self._minButton = wx.Button(self, label='{}'.format(minValue))
            self._maxButton = wx.Button(self, label='{}'.format(maxValue))

            self._sizer.Insert(0, self._minButton, flag=wx.EXPAND)
            self._sizer.Add(      self._maxButton, flag=wx.EXPAND)

            self._minButton.Enable(editLimits)
            self._maxButton.Enable(editLimits)

            self._minButton.Bind(wx.EVT_BUTTON, self._onLimitButton)
            self._maxButton.Bind(wx.EVT_BUTTON, self._onLimitButton)

        self.Layout()

        
    def _onLimitButton(self, ev):
        """Called when either of the minimum/maximum limit buttons
        are clicked. Pops up a :class:`~fsl.gui.numberdialog.NumberDialog`
        window and, if the user changes the value, updates the slider/spin
        limits, and emits an :data:`EVT_SSP_LIMIT` event.
        """

        source = ev.GetEventObject()

        if source == self._minButton:
            message = 'New minimum value'
            initVal = self.GetMin()
            minVal  = None
            maxVal  = self.GetMax()
        elif source == self._maxButton:
            message = 'New maximum value'
            initVal = self.GetMax()
            minVal  = self.GetMin()
            maxVal  = None
        else:
            return

        dlg = numberdialog.NumberDialog(
            self.GetTopLevelParent(),
            message=message,
            initial=initVal,
            minValue=minVal,
            maxValue=maxVal)

        pos = ev.GetEventObject().GetScreenPosition()
        dlg.SetPosition(pos)
        if dlg.ShowModal() != wx.ID_OK:
            return

        if   source == self._minButton: self.SetMin(dlg.GetValue())
        elif source == self._maxButton: self.SetMax(dlg.GetValue())

        wx.PostEvent(self, SliderSpinLimitEvent(
            min=self.GetMin(),
            max=self.GetMax()))

        
    def _onSlider(self, ev):
        """Called when the user changes the slider value. Updates the
        spinbox value and emits an :data:`EVT_SSP_VALUE` event.
        """
        val = self._slider.GetValue()
        self._spinbox.SetValue(val)
        wx.PostEvent(self, SliderSpinValueEvent(value=val)) 

        
    def _onSpin(self, ev):
        """Called when the user changes the spinbox value. Updates the
        slider value and emits an :data:`EVT_SSP_VALUE` event.
        """
        val = self._spinbox.GetValue()
        self._slider.SetValue(val)
        wx.PostEvent(self, SliderSpinValueEvent(value=val)) 

        
    def GetRange(self):
        """Return a tuple containing the (minimum, maximum) slider/spinbox
        values.
        """
        return self._slider.GetRange()

        
    def GetMin(self):
        """Returns the minimum slider/spinbox value."""
        return self._slider.GetMin()

        
    def GetMax(self):
        """Returns the maximum slider/spinbox value."""
        return self._slider.GetMax()

        
    def GetValue(self):
        """Returns the current slider/spinbox value. """
        return self._slider.GetValue()

        
    def SetRange(self, minValue, maxValue):
        """Sets the minimum/maximum slider/spinbox values.""" 
        self.SetMin(minValue)
        self.SetMax(maxValue)

        
    def SetMin(self, minValue):
        """Sets the minimum slider/spinbox value.""" 
        self._slider .SetMin(minValue)
        self._spinbox.SetMin(minValue)

        if self._showLimits:
            self._minButton.SetLabel('{}'.format(minValue))

            
    def SetMax(self, maxValue):
        """Sets the maximum slider/spinbox value.""" 
        self._slider .SetMax(maxValue)
        self._spinbox.SetMax(maxValue)

        if self._showLimits:
            self._maxButton.SetLabel('{}'.format(maxValue)) 

            
    def SetValue(self, value):
        """Sets the current slider/spinbox value.""" 
        self._slider .SetValue(value)
        self._spinbox.SetValue(value)
