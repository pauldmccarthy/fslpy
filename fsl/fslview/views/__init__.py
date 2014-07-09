#!/usr/bin/env python
#
# __init__.py - This package contains a collection of wx.Panel subclasses
#               which provide a view of an image collection.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This package contains a collection of :class:`wx.Panel` subclasses
which provide a view of an image collection (see
:class:`~fsl.data.image.ImageList`).

The :class:`ViewPanel` class is the superclass for every view panel.
"""

import viewpanel
import orthopanel
import lightboxpanel
import timeseriespanel

ViewPanel       = viewpanel      .ViewPanel
OrthoPanel      = orthopanel     .OrthoPanel
LightBoxPanel   = lightboxpanel  .LightBoxPanel
TimeSeriesPanel = timeseriespanel.TimeSeriesPanel
