#!/usr/bin/env python
#
# histogramtoolbar.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
import logging

import wx

import props

import fsl.data.strings    as strings
import fsl.fslview.actions as actions
import fsl.fslview.panel   as fslpanel


log = logging.getLogger(__name__)


class HistogramToolBar(fslpanel.FSLViewToolBar):

    def __init__(self, parent, imageList, displayCtx, histPanel):

        import fsl.fslview.layouts as layouts
        
        fslpanel.FSLViewToolBar.__init__(self, parent, imageList, displayCtx)
        
        toolSpecs = layouts.layouts[self]

        for toolSpec in toolSpecs:
            tool = props.buildGUI(self, histPanel, toolSpec)

            if isinstance(toolSpec, actions.ActionButton):
                label = None
            else:
                label = strings.properties[histPanel, toolSpec.key]

            self.AddTool(tool, label)


    def destroy(self):
        fslpanel.FSLViewToolBar.destroy(self)
