#!/usr/bin/env python
#
# actionpanel.py - Build a GUI for an ActionProvider instance.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ActionPanel` class, a :class:`wx.Panel`
which contains buttons and widgets allowing the user to run the actions of,
and modify the properties of an :class:`~fsl.fslview.actions.ActionProvider`
instance.
"""

import logging
log = logging.getLogger(__name__)


import wx

import props

import fsl.fslview.strings as strings

class ActionPanel(wx.Panel):
    """
    """

    def __init__(self, parent, provider, propz=None, actionz=None):

        wx.Panel.__init__(self, parent)

        if propz   is None: propz, _ = provider.getAllProperties()
        if actionz is None: actionz  = provider.getActions().keys()

        self._provider = provider
        
        self._propPanel   = wx.Panel(self)
        self._actionPanel = wx.Panel(self)

        self._propSizer   = wx.GridSizer(len(propz), 2)
        self._actionSizer = wx.BoxSizer(wx.HORIZONTAL)
        self._mainSizer   = wx.BoxSizer(wx.VERTICAL)

        self             .SetSizer(self._mainSizer)
        self._propPanel  .SetSizer(self._propSizer)
        self._actionPanel.SetSizer(self._actionSizer)

        for prop in propz:
            
            label  = wx.StaticText(self._propPanel,
                                   label=strings.labels[provider, prop])
            widget = props.makeWidget(self._propPanel, provider, prop)

            self._propSizer.Add(label, flag=wx.EXPAND)
            self._propSizer.Add(widget, flag=wx.EXPAND)

        for action in actionz:

            button = wx.Button(self._actionPanel,
                               label=strings.labels[provider, action])
            self._actionSizer.Add(button, flag=wx.EXPAND)

            self._provider.getAction(action).bindToWidget(
                button, wx.EVT_BUTTON, button)

        self._mainSizer.Add(self._propPanel,   flag=wx.EXPAND)
        self._mainSizer.Add(self._actionPanel, flag=wx.EXPAND)
