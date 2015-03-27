#!/usr/bin/env python
#
# histogramtoolbar.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
import logging

import fsl.fslview.toolbar as fsltoolbar


log = logging.getLogger(__name__)


class HistogramToolBar(fsltoolbar.FSLViewToolBar):

    def __init__(self, parent, imageList, displayCtx, histPanel):

        import fsl.fslview.layouts as layouts
        
        fsltoolbar.FSLViewToolBar.__init__(self, parent, imageList, displayCtx)
        
        self.GenerateTools(layouts.layouts[self], histPanel)


    def destroy(self):
        fsltoolbar.FSLViewToolBar.destroy(self)
