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

        self._profile = profile

        propNames, _ = profile.getAllProperties()

        propNames.remove('mode')

        view = props.HGroup(['mode'] + propNames)

        props.buildGUI(self, profile, view)
