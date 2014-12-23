#!/usr/bin/env python
#
# profilepanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import wx

import props

import fsl.fslview.layouts as layouts
import fsl.fslview.strings as strings


class ProfilePanel(wx.Panel):

    def __init__(self, parent, profile):
        wx.Panel.__init__(self, parent)

        self._name        = '{}_{}'.format(self.__class__.__name__, id(self))
        self._profile     = profile
        self._actionPanel = wx.Panel(self)
        self._actionSizer = wx.BoxSizer(wx.HORIZONTAL)
        self._sizer       = wx.BoxSizer(wx.VERTICAL)

        self._propPanel = props.buildGUI(
            self,
            profile,
            view=layouts.layouts[profile])

        actions = profile.getActions()

        for (name, func) in actions.items():

            btn = wx.Button(self._actionPanel,
                            label=strings.labels[profile, name])
            self._actionSizer.Add(btn, flag=wx.EXPAND)
            btn.Bind(wx.EVT_BUTTON, lambda ev, f=func: f.doAction())
            btn.Enable(profile.isEnabled(name))

            def toggle(val, valid, ctx, n=name, b=btn):
                b.Enable(profile.isEnabled(n))
                           
            profile.addActionToggleListener(name, self._name, toggle)


        self._sizer.Add(self._propPanel,   flag=wx.EXPAND)
        self._sizer.Add(self._actionPanel, flag=wx.EXPAND)

        self._actionPanel.SetSizer(self._actionSizer)
        self             .SetSizer(self._sizer)


        self._actionPanel.Layout()
        self             .Layout()
