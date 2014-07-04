#!/usr/bin/env python
#
# __init__.py - This package contains a collection of wx.Panel subclasses
#               which provide some sort of interface for controlling
#               aspects of the image display.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This package contains a collection of :class:`wx.Panel` subclasses which
provide some sort of interface for controlling aspects of the image display.
"""

import locationpanel
import imagelistpanel
import imagedisplaypanel

LocationPanel     = locationpanel    .LocationPanel
ImageListPanel    = imagelistpanel   .ImageListPanel
ImageDisplayPanel = imagedisplaypanel.ImageDisplayPanel
