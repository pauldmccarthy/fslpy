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

The :class:`~fsl.fslview.views.viewpanel.ViewPanel` class is the superclass
for every view panel.

A convenience function, :func:`listViewPanels`, is provided to allow
dynamic lookup of all :class:`~fsl.fslview.views.viewpanel.ViewPanel` types.
"""

import fsl.fslview.panel as fslpanel

import canvaspanel
import orthopanel
import lightboxpanel
import timeseriespanel
import histogrampanel

FSLViewPanel    = fslpanel       .FSLViewPanel
CanvasPanel     = canvaspanel    .CanvasPanel
OrthoPanel      = orthopanel     .OrthoPanel
LightBoxPanel   = lightboxpanel  .LightBoxPanel
TimeSeriesPanel = timeseriespanel.TimeSeriesPanel
HistogramPanel  = histogrampanel .HistogramPanel


def listViewPanels():
    """Convenience function which returns a list containing all
    :class:`~fsl.fslview.views.viewpanel.ViewPanel` classes in
    the :mod:`views` package.
    """

    atts = globals()

    viewPanels = []

    for name, val in atts.items():
        
        if not isinstance(val, type): continue
        if val == FSLViewPanel:       continue
            
        if issubclass(val, FSLViewPanel) and \
           val != CanvasPanel :
            viewPanels.append(val)
            
    return viewPanels
