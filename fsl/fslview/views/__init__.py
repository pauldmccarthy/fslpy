#!/usr/bin/env python
#
# __init__.py - This package contains a collection of wx.Panel subclasses
#               which provide a view of an image collection.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This package contains a collection of :class:`wx.Panel` subclasses
which provide a view of an image collection (see
:class:`~fsl.data.fslimage.ImageList`).
"""

import orthopanel
import lightboxpanel

OrthoPanel    = orthopanel   .OrthoPanel
LightBoxPanel = lightboxpanel.LightBoxPanel
