#!/usr/bin/env python
#
# orthosettingspanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging


import fsl.fslview.panel as fslpanel


log = logging.getLogger(__name__)


class OrthoSettingsPanel(fslpanel.FSLViewPanel):

    def __init__(self, parent, imageList, displayCtx, ortho):
        fslpanel.FSLViewPanel.__init__(self, parent, imageList, displayCtx)

        self.orthoPanel = ortho


    def destroy(self):
        fslpanel.FSLViewPanel.destroy(self)
