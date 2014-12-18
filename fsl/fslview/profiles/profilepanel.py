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

class ProfilePanel(wx.Panel):

    def __init__(self, parent, profile):
        wx.Panel.__init__(self, parent)

        self._name        = '{}_{}'.format(self.__class__.__name__, id(self))
        self._profile     = profile
        self._propPanel   = wx.Panel(self)
        self._actionPanel = wx.Panel(self)
        self._actionSizer = wx.BoxSizer(wx.HORIZONTAL)
        self._sizer       = wx.BoxSizer(wx.VERTICAL)

        propNames, _ = profile.getAllProperties()

        propNames.remove('mode')

        modeProp = profile.getProp('mode')
        if len(modeProp.getChoices(profile)) > 0:
            propNames = ['mode'] + propNames

        view = props.HGroup(propNames)

        props.buildGUI(self._propPanel, profile, view)

        actions = profile.getActions()

        for (name, func) in actions.items():

            btn = wx.Button(self._actionPanel, label=name)
            self._actionSizer.Add(btn)
            btn.Bind(wx.EVT_BUTTON, lambda ev, f=func: f())
            btn.Enable(profile.isEnabled(name))

            def toggle(val, valid, ctx, n=name, b=btn):
                b.Enable(profile.isEnabled(n))
                           
            profile.addActionToggleListener(name, self._name, toggle)


        self._sizer.Add(self._propPanel)
        self._sizer.Add(self._actionPanel)

        self._actionPanel.SetSizer(self._actionSizer)
        self             .SetSizer(self._sizer)


        self._actionPanel.Layout()
        self             .Layout()
