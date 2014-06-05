#!/usr/bin/env python
#
# NumberDialog.py - Similar to the wx.NumberEntryDialog, except allows
#                   both floating point and integer types
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import sys
import wx

class NumberDialog(wx.Dialog):
    """
    A dialog which contains a wx.SpinCtrl/SpinCtrlDouble, and Ok/Cancel
    buttons, allowing the user to specify a number. If the user pushes
    the Ok button, the number they entered will be accessible via the
    GetValue() method.
    """

    def __init__(self,
                 parent,
                 real=False,
                 title=None,
                 message=None,
                 initial=None,
                 minval=None,
                 maxval=None):
        """
        Creates and lays out the NumberDialog. Parameters:
        
          - real:    If true, a wx.SpinCtrlDouble will be used. Otherwise,
                     a wx.SpinCtrl is used.
        
          - title:   Dialog title.
        
          - message: If not None, a wx.StaticText label is added, containing
                     the message.
        
          - initial: Initial spinctrl value.
        
          - minval:  Minimum spinctrl value.
        
          - maxval:  Maximum spinctrl value.
        """

        if title   is None: title   = ''
        if initial is None: initial = 0

        wx.Dialog.__init__(self, parent, title=title)

        self._value = None

        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.sizer)

        self.buttonPanel = wx.Panel(self.panel)
        self.buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.buttonPanel.SetSizer(self.buttonSizer)

        if message is not None:
            self.label = wx.StaticText(self.panel, label=message)
            self.sizer.Add(self.label, flag=wx.EXPAND)

        if real:
            if minval is None: minval = -sys.float_info.max
            if maxval is None: maxval =  sys.float_info.max
            self.spinctrl = wx.SpinCtrlDouble(self.panel,
                                              min=minval,
                                              max=minval,
                                              initial=initial,
                                              value='{}'.format(initial))
        else:
            if minval is None: minval = -2 ** 31
            if maxval is None: maxval =  2 ** 31 - 1
            self.spinctrl = wx.SpinCtrl(self.panel,
                                        min=minval,
                                        max=maxval,
                                        initial=initial,
                                        value='{}'.format(initial))

        self.sizer.Add(self.spinctrl, flag=wx.EXPAND)

        self.okButton     = wx.Button(self.buttonPanel, label='Ok')
        self.cancelButton = wx.Button(self.buttonPanel, label='Cancel')

        self.buttonSizer.Add(self.okButton,     flag=wx.EXPAND, proportion=1)
        self.buttonSizer.Add(self.cancelButton, flag=wx.EXPAND, proportion=1)

        self.sizer.Add(self.buttonPanel, flag=wx.EXPAND)

        def onOk(ev):
            self._value = self.spinctrl.GetValue()
            self.EndModal(wx.ID_OK)
            self.Destroy()

        def onCancel(ev):
            self.EndModal(wx.ID_CANCEL)
            self.Destroy()

        self.okButton    .Bind(wx.EVT_BUTTON, onOk)
        self.cancelButton.Bind(wx.EVT_BUTTON, onCancel)

        self.panel.Layout()
        self.panel.Fit()

        self.Fit()


    def GetValue(self):
        return self._value
