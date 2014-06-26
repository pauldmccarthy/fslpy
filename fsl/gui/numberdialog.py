#!/usr/bin/env python
#
# numberdialog.py - An alternative to wx.NumberEntryDialog.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""An alternative to ``wx.NumberEntryDialog`` which supports floating point."""

import wx

class NumberDialog(wx.Dialog):
    """Dialog which prompts the user for a number.
    
    A dialog which contains a ``wx.TextCtrl``, and Ok/Cancel buttons,
    allowing the user to specify a number. If the user pushes the Ok
    button, the number they entered will be accessible via the
    :meth:`GetValue` method.

    I've specifically not used the ``wx.SpinCtrl`` or ``wx.SpinCtrlDouble``,
    because they are too limited in their flexibility with regard to
    validation and events. 
    """

    def __init__(self,
                 parent,
                 real=True,
                 title=None,
                 message=None,
                 initial=None,
                 minValue=None,
                 maxValue=None):
        """Create and lay out a NumberDialog.

        :param parent:          Wx parent object.

        :param bool real:       If true, a floating point number will be 
                                accepted. Otherwise, only integers are
                                accepted.

        :param str title:       Dialog title.
        
        :param str message:     If not None, a ``wx.StaticText`` label is
                                added, containing the message.

        :param number initial:  Initial value.
        
        :param number minValue: Minimum value.
        
        :param number maxValue: Maximum value.
        """

        if title   is None: title   = ''
        if initial is None: initial = 0

        wx.Dialog.__init__(self, parent, title=title)

        self._value    = None
        self._real     = real
        self._minValue = minValue
        self._maxValue = maxValue

        if self._real: initial = float(initial)
        else:          initial = int(  initial)

        self._panel = wx.Panel(self)
        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self._panel.SetSizer(self._sizer)

        self._buttonPanel = wx.Panel(self._panel)
        self._buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        self._buttonPanel.SetSizer(self._buttonSizer)

        if message is not None:
            self._label = wx.StaticText(self._panel, label=message)
            self._sizer.Add(self._label, flag=wx.EXPAND)

        self._textctrl = wx.TextCtrl(self._panel, style=wx.TE_PROCESS_ENTER)
        self._textctrl.SetValue('{}'.format(initial))

        self._sizer.Add(self._textctrl, flag=wx.EXPAND)

        self._errorLabel = wx.StaticText(self._panel)
        self._errorLabel.SetForegroundColour('#992222')
        
        self._sizer.Add(self._errorLabel)
        self._sizer.Show(self._errorLabel, False)

        self._okButton     = wx.Button(self._buttonPanel, label='Ok')
        self._cancelButton = wx.Button(self._buttonPanel, label='Cancel')

        self._buttonSizer.Add(self._okButton,     flag=wx.EXPAND, proportion=1)
        self._buttonSizer.Add(self._cancelButton, flag=wx.EXPAND, proportion=1)

        self._sizer.Add(self._buttonPanel, flag=wx.EXPAND)

        self._textctrl    .Bind(wx.EVT_TEXT_ENTER, self._onOk)
        self._okButton    .Bind(wx.EVT_BUTTON,     self._onOk)
        self._cancelButton.Bind(wx.EVT_BUTTON,     self._onCancel)
        
        self._panel.Layout()
        self._panel.Fit()

        self.Fit()

        
    def GetValue(self):
        """Return the value that the user entered.
        
        After a valid value has been entered, and OK button pushed (or
        enter pressed), this method may be used to retrieve the value.
        Returns ``None`` in all other situations.
        """
        return self._value


    def _validate(self):
        """Validates the current value.

        If the value is valid, returns it.  Otherwise a ``ValueError`` is
        raised with an appropriate message.
        """
        
        value = self._textctrl.GetValue()

        if self._real: cast = float
        else:          cast = int
        
        try:
            value = cast(value)
        except:
            if self._real: err = ' floating point'
            else:          err = 'n integer'
            raise ValueError('The value must be a{}'.format(err))

        if self._minValue is not None and value < self._minValue:
            raise ValueError('The value must be at '
                             'least {}'.format(self._minValue))
            
        if self._maxValue is not None and value > self._maxValue:
            raise ValueError('The value must be at '
                             'most {}'.format(self._maxValue))

        return value


    def _onOk(self, ev):
        """Called when the Ok button is pushed, or enter is pressed.

        If the entered value is valid, it is stored and the dialog is closed.
        The value may be retrieved via the :meth:`GetValue` method. If the
        value is not valid, the dialog remains open.
        """
        
        try:
            value = self._validate()
            
        except ValueError as e:
            self._errorLabel.SetLabel(e.message)
            self._sizer.Show(self._errorLabel, True)
            self._panel.Layout()
            self._panel.Fit()
            self.Fit()
            return
            
        self._value = value
        self.EndModal(wx.ID_OK)
        self.Destroy()

        
    def _onCancel(self, ev):
        """Called when the Cancel button is pushed. Closes the dialog."""
        self._value = None
        self.EndModal(wx.ID_CANCEL)
        self.Destroy() 


def _testNumberDialog():
    """Little test program."""

    app    = wx.App()
    frame  = wx.Frame(None)
    panel  = wx.Panel(frame)
    sizer  = wx.BoxSizer(wx.HORIZONTAL)
    button = wx.Button(panel, label='Show dialog!')

    sizer.Add(button, flag=wx.EXPAND)
    panel.SetSizer(sizer)


    def _showDlg(ev):
        dlg = NumberDialog(
            frame,
            real=True,
            title='Enter number',
            message='Enter a number between 0 and 100',
            initial=20,
            minValue=0,
            maxValue=100)

        if dlg.ShowModal() != wx.ID_OK:
            print 'Not ok'
        else:
            print 'Number entered: {}'.format(dlg.GetValue())


    button.Bind(wx.EVT_BUTTON, _showDlg)

    frame.Show()
    app.MainLoop()
