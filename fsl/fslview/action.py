#!/usr/bin/env python
#
# action.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import wx

class Action(wx.MenuItem):

    def __init__(self, menuItem, imageList, displayCtx):
        self._menuItem   = menuItem
        self._imageList  = imageList
        self._displayCtx = displayCtx

    def enable(self):
        self._menuItem.Enable(True)

    def disable(self):
        self._menuItem.Enable(False)

    def doAction(self, activeViewPanel):
        """
        Subclass implementations should check that the ``activeViewPanel``
        parameter is not ``None``.
        """
        raise RuntimeError('Action object must implement the doAction method')
