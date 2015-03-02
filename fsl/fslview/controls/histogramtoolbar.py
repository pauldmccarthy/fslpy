#!/usr/bin/env python
#
# histogramtoolbar.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
import logging

import fsl.fslview.panel as fslpanel


log = logging.getLogger(__name__)


class HistogramToolBar(fslpanel.FSLViewToolBar):

    def __init__(self, parent, imageList, displayCtx, histPanel):

        import fsl.fslview.layouts as layouts
        
        fslpanel.FSLViewToolBar.__init__(self, parent, imageList, displayCtx)
        
        self.GenerateTools(layouts.layouts[self], histPanel)


    def destroy(self):
        fslpanel.FSLViewToolBar.destroy(self)
