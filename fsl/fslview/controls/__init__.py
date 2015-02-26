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

The :class:`~fsl.fslview.panel.ControlPanel` class is the superclass for
every control panel.

A convenience function, :func:`listControlPanels`, is provided to allow
dynamic lookup of all :class:`~fsl.fslview.panel.ControlPanel` types.
"""

import fsl.fslview.panel as fslpanel 
import locationpanel
import imagelistpanel
# import imagedisplaypanel
import imagedisplaytoolbar
import atlaspanel

FSLViewPanel        = fslpanel           .FSLViewPanel
FSLViewToolBar      = fslpanel           .FSLViewToolBar
LocationPanel       = locationpanel      .LocationPanel
ImageListPanel      = imagelistpanel     .ImageListPanel
ImageDisplayPanel   = imagedisplaypanel  .ImageDisplayPanel
ImageDisplayToolBar = imagedisplaytoolbar.ImageDisplayToolBar
AtlasPanel          = atlaspanel         .AtlasPanel


def listControlPanels():
    """Convenience function which returns a list containing all
    :class:`~fsl.fslview.panel.ControlPanel` classes in the
    :mod:`controls` package.
    """

    atts = globals()

    ctrlPanels = []

    for name, val in atts.items():
        
        if not isinstance(val, type): continue
        if val == FSLViewPanel:       continue
            
        if issubclass(val, FSLViewPanel):
            ctrlPanels.append(val)
            
    return ctrlPanels


def listToolBars():
    atts = globals()

    toolbars = []

    for name, val in atts.items():
        
        if not isinstance(val, type): continue
        if val == FSLViewToolBar:     continue
            
        if issubclass(val, FSLViewToolBar):
            toolbars.append(val)
            
    return toolbars
