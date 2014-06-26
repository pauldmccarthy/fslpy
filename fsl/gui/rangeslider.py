#!/usr/bin/env python
#
# rangeslider.py - Twin sliders for defining the values of a range.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Twin sliders for defining the values of a range.

Provides two classes, :class:`RangePanel`, and :class:`RangeSliderSpinPanel`.

The :class:`RangePanel` is a widget which contains two sliders or spinboxes,
allowing a range to be set. The slider/spinbox which controls the low range
value must always be less than the slider which/spinbox controls the high
value.

The :class:`RangeSliderSpinPanel` is a widget which contains two
:class:`RangePanel` widgets - one with sliders, and one with spinboxes. All
four control widgets are linked.
"""


import wx
import wx.lib.newevent as wxevent

import floatslider
import numberdialog


_RangeEvent,      _EVT_RANGE       = wxevent.NewEvent()
_RangeLimitEvent, _EVT_RANGE_LIMIT = wxevent.NewEvent()


EVT_RANGE = _EVT_RANGE
"""Identifier for the :data:`RangeEvent`."""

EVT_RANGE_LIMIT = _EVT_RANGE_LIMIT
"""Identifier for the :data:`RangeLimitEvent`."""


RangeEvent = _RangeEvent
"""Event emitted by :class:`RangePanel` and :class:`RangeSliderSpinPanel`
objects  when either of their low or high values change. Contains two
attributes, ``low`` and ``high``, containing the new low/high range values.
"""


RangeLimitEvent = _RangeLimitEvent
"""Event emitted by :class:`RangeSliderSpinPanel` objects when the user
modifies the range limits. Contains two attributes, ``min`` and ``max``,
containing the new minimum/maximum range limits.
"""


class RangePanel(wx.Panel):
    """A :class:`wx.Panel` containing two widgets (either
    :class:`~fsl.gui.floatslider.FloatSlider`, or
    :class:`wx.SpinCtrlDouble`), representing the 'low'
    and 'high' values of a range, respectively. When the
    user changes the low slider to a value beyond the
    current high value, the high value is increased such
    that it remains at least a minimum value above the
    low value. The inverse relationship is also enforced.
    """ 

    def __init__(self,
                 parent,
                 widgetType,
                 minValue=None,
                 maxValue=None,
                 lowValue=None,
                 highValue=None,
                 lowLabel=None,
                 highLabel=None,
                 minDistance=None):
        """Initialise a :class:`RangePanel` panel.
        
        :param parent:             The :mod:`wx` parent object.

        :param str widgetType:     Widget type - either 'slider' or 'spin'.
        
        :param number minValue:    Minimum range value.
        
        :param number maxValue:    Maximum range value.

        :param str lowLabel:       If not ``None``, a :class:`wx.StaticText` 
                                   widget is placed to the left of the low 
                                   widget, containing the given label.

        :param str highLabel:      If not ``None``, a :class:`wx.StaticText` 
                                   widget is placed to the left of the high 
                                   widget, containing the given label.

        :param number lowValue:    Initial low range value.
        
        :param number highValue:   Initial high range value.
        
        :param number minDistance: Minimum distance to be maintained between
                                   low/high values.
        """

        if widgetType not in ('slider', 'spin'):
            raise ValueError('Unknown widget type: {}'.format(widgetType))

        wx.Panel.__init__(self, parent)

        if minValue    is None: minValue    = 0
        if maxValue    is None: maxValue    = 1
        if lowValue    is None: lowValue    = 0
        if highValue   is None: highValue   = 1
        if minDistance is None: minDistance = 0.01

        self._minDistance = minDistance

        if widgetType == 'slider':
            self._lowWidget  = floatslider.FloatSlider(self)
            self._highWidget = floatslider.FloatSlider(self)
            self._lowWidget .Bind(wx.EVT_SLIDER, self._onLowChange)
            self._highWidget.Bind(wx.EVT_SLIDER, self._onHighChange)
            
        elif widgetType == 'spin':
            self._lowWidget  = wx.SpinCtrlDouble(self)
            self._highWidget = wx.SpinCtrlDouble(self)
            self._lowWidget .Bind(wx.EVT_SPINCTRLDOUBLE, self._onLowChange)
            self._highWidget.Bind(wx.EVT_SPINCTRLDOUBLE, self._onHighChange)

        self._sizer = wx.GridBagSizer(1, 1)
        self._sizer.SetEmptyCellSize((0, 0))
        
        self.SetSizer(self._sizer)

        self._sizer.Add(self._lowWidget,  pos=(0, 1), flag=wx.EXPAND | wx.ALL)
        self._sizer.Add(self._highWidget, pos=(1, 1), flag=wx.EXPAND | wx.ALL)

        if lowLabel is not None:
            self._lowLabel = wx.StaticText(self, label=lowLabel)
            self._sizer.Add(self._lowLabel,
                            pos=(0, 0),
                            flag=wx.EXPAND | wx.ALL)

        if highLabel is not None:
            self._highLabel = wx.StaticText(self, label=highLabel)
            self._sizer.Add(self._highLabel,
                            pos=(1, 0),
                            flag=wx.EXPAND | wx.ALL) 

        self.SetLimits(minValue, maxValue)
        self.SetRange( lowValue, highValue)

        self._sizer.AddGrowableCol(1)

        self.Layout()


    def _onLowChange(self, ev):
        """Called when the user changes the low widget.  Attempts to make
        sure that the high widget is at least (low value + min distance),
        then posts a :data:`RangeEvent`.
        """

        lowValue  = self.GetLow()
        highValue = self.GetHigh()

        if lowValue >= (self.GetMax() - self._minDistance):
            self.SetLow(self.GetMax() - self._minDistance)
            lowValue = self.GetLow()

        if highValue <= (lowValue + self._minDistance):
            highValue = lowValue + self._minDistance
            self.SetHigh(highValue)
            highValue = self.GetHigh()

        ev = RangeEvent(low=lowValue, high=highValue)
        ev.SetEventObject(self)

        wx.PostEvent(self, ev)

            
    def _onHighChange(self, ev):
        """Called when the user changes the high widget.  Attempts to make
        sure that the low widget is at least (high value - min distance),
        then posts a :data:`RangeEvent`.
        """ 

        lowValue  = self.GetLow()
        highValue = self.GetHigh()

        if highValue <= (self.GetMin() + self._minDistance):
            self.SetHigh(self.GetMin() + self._minDistance)
            highValue = self.GetHigh() 

        if lowValue >= (highValue - self._minDistance):
            lowValue = highValue - self._minDistance
            self.SetLow(lowValue)
            lowValue = self.GetLow()
            
        ev = RangeEvent(low=lowValue, high=highValue)
        ev.SetEventObject(self) 

        wx.PostEvent(self, ev)

        
    def GetRange(self):
        """Returns a tuple containing the current (low, high) range values."""
        return (self.GetLow(), self.GetHigh())

        
    def SetRange(self, lowValue, highValue):
        """Sets the current (low, high) range values.""" 
        self.SetLow( lowValue)
        self.SetHigh(highValue)

        
    def GetLow(self):
        """Returns the current low range value."""
        return self._lowWidget.GetValue()

        
    def GetHigh(self):
        """Returns the current high range value.""" 
        return self._highWidget.GetValue()

        
    def SetLow(self, lowValue):
        """Set the current low range value, and attempts to make sure
        that the high value is at least (low value + min distance).
        """
        self._lowWidget.SetValue(lowValue)

        highValue = self.GetHigh()
        if highValue <= lowValue + self._minDistance:
            self._highWidget.SetValue(lowValue + self._minDistance)

        
    def SetHigh(self, highValue):
        """Set the current high range value, and attempts to make sure
        that the high value is at least (low value + min distance).
        """ 
        self._highWidget.SetValue(highValue)
        
        lowValue = self.GetLow()
        if lowValue >= highValue - self._minDistance:
            self._lowWidget.SetValue(highValue - self._minDistance)


    def getLimits(self):
        """Returns a tuple containing the current (minimum, maximum) range
        limit values.
        """
        return (self.GetMin(), self.GetMax())

        
    def SetLimits(self, minValue, maxValue):
        """Sets the current (minimum, maximum) range limit values.""" 
        self.SetMin(minValue)
        self.SetMax(maxValue)


    def GetMin(self):
        """Returns the current minimum range value."""
        return self._lowWidget.GetMin()

        
    def GetMax(self):
        """Returns the current maximum range value.""" 
        return self._highWidget.GetMax()

        
    def SetMin(self, minValue):
        """Sets the current minimum range value."""
        self._lowWidget .SetMin(minValue)
        self._highWidget.SetMin(minValue)

        
    def SetMax(self, maxValue):
        """Sets the current maximum range value."""
        self._lowWidget .SetMax(maxValue)
        self._highWidget.SetMax(maxValue)


class RangeSliderSpinPanel(wx.Panel):
    """A :class:`wx.Panel` which contains two sliders and two spinboxes.

    The sliders and spinboxes are contained within two :class:`RangePanel`
    instances respectively). One slider and spinbox are used to edit the
    'low' value of a range, and the other slider/spinbox are used to edit
    the 'high' range value. Buttons are optionally displayed on either end
    which display the minimum/maximum limits and, when clicked, allow the
    user to modify said limits.
    """
    
    def __init__(self,
                 parent,
                 minValue=None,
                 maxValue=None,
                 lowValue=None,
                 highValue=None,
                 minDistance=None,
                 lowLabel=None,
                 highLabel=None,
                 showLimits=True,
                 editLimits=False):
        """Initialise a :class:`RangeSliderSpinPanel`.
        
        :param parent:             The :mod:`wx` parent object.
        
        :param number minValue:    Minimum low value.
        
        :param number maxValue:    Maximum high value.
        
        :param number lowValue:    Initial low value.
        
        :param number highValue:   Initial high value.
        
        :param number minDistance: Minimum distance to maintain between low
                                   and high values.

        :param str lowLabel:       If not ``None``, a :class:`wx.StaticText` 
                                   widget is placed to the left of the low 
                                   slider, containing the label.

        :param str highLabel:      If not ``None``, a :class:`wx.StaticText`
                                    widget is placed to the left of the high 
                                   slider, containing the label. 
        
        :param bool showLimits:    If ``True``, a button will be shown on
                                   either side, displaying the minimum/maximum
                                   values.
        
        :param bool editLimits:    If ``True``, when aforementioned buttons are
                                   clicked, a
                                   :class:~fsl.gui.numberdialog.NumberDialog`
                                   window will pop up, allowing the user to
                                   edit the min/max limits.
        """

        wx.Panel.__init__(self, parent)

        if minValue    is None: minValue    = 0
        if maxValue    is None: maxValue    = 1
        if lowValue    is None: lowValue    = 0
        if highValue   is None: highValue   = 1
        if minDistance is None: minDistance = 0.01 
        
        if not showLimits: editLimits = False
        
        self._showLimits = showLimits

        params = {
            'minValue'    : minValue,
            'maxValue'    : maxValue,
            'lowValue'    : lowValue,
            'highValue'   : highValue,
            'minDistance' : minDistance
        }
        
        self._sliderPanel = RangePanel(self,
                                       widgetType='slider',
                                       lowLabel=lowLabel,
                                       highLabel=highLabel,
                                       **params)
        self._spinPanel   = RangePanel(self, widgetType='spin', **params)
        
        self._sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self._sizer)

        self._sizer.Add(self._sliderPanel, flag=wx.EXPAND, proportion=1)
        self._sizer.Add(self._spinPanel,   flag=wx.EXPAND)

        self._sliderPanel.Bind(EVT_RANGE, self._onRangeChange)
        self._spinPanel  .Bind(EVT_RANGE, self._onRangeChange) 

        if showLimits:
            self._minButton = wx.Button(self, label='{}'.format(minValue))
            self._maxButton = wx.Button(self, label='{}'.format(maxValue))

            self._sizer.Insert(0, self._minButton, flag=wx.EXPAND | wx.ALL)
            self._sizer.Add(      self._maxButton, flag=wx.EXPAND | wx.ALL)

            self._minButton.Enable(editLimits)
            self._maxButton.Enable(editLimits)

            self._minButton.Bind(wx.EVT_BUTTON, self._onLimitButton)
            self._maxButton.Bind(wx.EVT_BUTTON, self._onLimitButton)
            
        self.Layout()

        
    def _onRangeChange(self, ev):
        """Called when the user modifies the low or high range values.
        Syncs the change between the sliders and spinboxes, and emits
        a :data:`RangeEvent`.
        """
        source = ev.GetEventObject()

        lowValue, highValue = source.GetRange()

        if source == self._sliderPanel:
            self._spinPanel.SetRange(lowValue, highValue)
        elif source == self._spinPanel:
            self._sliderPanel.SetRange(lowValue, highValue)

        ev = RangeEvent(low=lowValue, high=highValue)
        ev.SetEventObject(self)

        wx.PostEvent(self, ev)

            
    def _onLimitButton(self, ev):
        """Called when one of the min/max buttons is pushed. Pops up
        a dialog prompting the user to enter a new value, and updates
        the range limits accordingly. Emits a :data:`RangeLimitEvent`.
        """

        source = ev.GetEventObject()
        
        if source == self._minButton:
            labeltxt = 'New minimum value'
            initVal  = self.GetMin()
            minVal   = None
            maxVal   = self.GetMax()
            
        elif source == self._maxButton:
            labeltxt = 'New maximum value'
            initVal  = self.GetMax()
            minVal   = self.GetMin() 
            maxVal   = None
            
        else:
            return

        dlg = numberdialog.NumberDialog(
            self.GetTopLevelParent(),
            message=labeltxt,
            initial=initVal,
            minValue=minVal,
            maxValue=maxVal)

        pos = ev.GetEventObject().GetScreenPosition()
        dlg.SetPosition(pos)
        if dlg.ShowModal() != wx.ID_OK:
            return

        if   source == self._minButton: self.SetMin(dlg.GetValue())
        elif source == self._maxButton: self.SetMax(dlg.GetValue())

        ev = RangeLimitEvent(min=self.GetMin(), max=self.GetMax())
        ev.SetEventObject(self)

        wx.PostEvent(self, ev)

        
    def SetLimits(self, minValue, maxValue):
        """Sets the minimum/maximum range values."""
        self.SetMin(minValue)
        self.SetMax(maxValue)

        
    def SetMin(self, minValue):
        """Sets the minimum range value."""
        self._sliderPanel.SetMin(minValue)
        self._spinPanel  .SetMin(minValue)

        if self._showLimits:
            self._minButton.SetLabel('{}'.format(minValue))

            
    def SetMax(self, maxValue):
        """Sets the maximum range value."""
        self._sliderPanel.SetMax(maxValue)
        self._spinPanel  .SetMax(maxValue)
        
        if self._showLimits:
            self._maxButton.SetLabel('{}'.format(maxValue))

            
    def GetMin(self):
        """Returns the minimum range value."""
        return self._sliderPanel.GetMin()

        
    def GetMax(self):
        """Returns the maximum range value.""" 
        return self._sliderPanel.GetMax()

        
    def GetLow( self):
        """Returns the current low range value."""
        return self._sliderPanel.GetLow()

        
    def GetHigh(self):
        """Returns the current high range value."""
        return self._sliderPanel.GetHigh()

        
    def SetLow(self, lowValue):
        """Sets the current low range value."""
        self._sliderPanel.SetLow(lowValue)
        self._spinPanel  .SetLow(lowValue)

        
    def SetHigh(self, highValue):
        """Sets the current high range value.""" 
        self._sliderPanel.SetHigh(highValue)
        self._spinPanel  .SetHigh(highValue)


    def GetRange(self):
        """Return the current (low, high) range values."""
        return self._sliderPanel.GetRange()


    def SetRange(self, lowValue, highValue):
        """Set the current low and high range values."""
        self._sliderPanel.SetRange(lowValue, highValue)
        self._spinPanel  .SetRange(lowValue, highValue)
        
        
def _testRangeSliderSpinPanel():
    """Little test program."""

    app   = wx.App()
    frame = wx.Frame(None)
    sizer = wx.BoxSizer(wx.VERTICAL)
    frame.SetSizer(sizer)
    
    slider = RangeSliderSpinPanel(
        frame,
        minValue=0,
        maxValue=100,
        lowValue=0,
        highValue=100,
        minDistance=5,
        lowLabel='Low',
        highLabel='High',
        showLimits=True,
        editLimits=True)

    sizer.Add(slider, flag=wx.EXPAND)

    def _range(ev):
        print 'Range: {} {}'.format(ev.low, ev.high)

    def _limit(ev):
        print 'Limit: {} {}'.format(ev.min, ev.max)
    
       
    slider.Bind(EVT_RANGE,       _range)
    slider.Bind(EVT_RANGE_LIMIT, _limit)
    
    frame.Layout()
    frame.Show()
    app.MainLoop()
