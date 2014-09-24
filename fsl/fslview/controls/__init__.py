#!/usr/bin/env python
#
# __init__.py - This package contains a collection of wx.Panel subclasses
#               which provide some sort of interface for controlling
#               aspects of the image display.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This package contains a collection of :class:`wx.Panel` subclasses which
provide some sort of interface for controlling aspects of image display.

The :class:`~fsl.fslview.controls.controlpanel.ControlPanel` class is the
superclass for every control panel.

A convenience function, :func:`listControlPanels`, is provided to allow
dynamic lookup of all :class:`~fsl.fslview.controls.controlpanel.ControlPanel`
types.
"""

import fsl.fslview.controlpanel as controlpanel 
import locationpanel
import imagelistpanel
import imagedisplaypanel

ControlPanel      = controlpanel     .ControlPanel
LocationPanel     = locationpanel    .LocationPanel
ImageListPanel    = imagelistpanel   .ImageListPanel
ImageDisplayPanel = imagedisplaypanel.ImageDisplayPanel


def listControlPanels():
    """Convenience function which returns a list containing all
    :class:`~fsl.fslview.controlpanel.ControlPanel` classes
    in the :mod:`controls` package.
    """

    atts = globals()

    ctrlPanels = []

    for name, val in atts.items():
        
        if not isinstance(val, type): continue
        if val == ControlPanel:       continue
            
        if issubclass(val, ControlPanel):
            ctrlPanels.append(val)
            
    return ctrlPanels
