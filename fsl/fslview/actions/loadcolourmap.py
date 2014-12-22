#!/usr/bin/env python
#
# loadcolourmap.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)


import fsl.fslview.actions        as actions
import fsl.fslview.colourmaps     as fslcmap
import fsl.fslview.displaycontext as displaycontext


class LoadColourMapAction(actions.Action):
    
    def doAction(self):

        import wx

        app = wx.GetApp()
        dlg = wx.FileDialog(app.GetTopWindow(),
                            message='Open colourmap file',
                            style=wx.FD_OPEN)

        if dlg.ShowModal() != wx.ID_OK:
            return

        fslcmap.registerColourMap(dlg.GetPath())


        displaycontext.ImageDisplay.cmap.setConstraint(
            None,
            'cmapNames',
            fslcmap.getColourMaps())

        for image in self._imageList:
            print 'updating colourmap for image {}'.format(image.name)
            display = self._displayCtx.getDisplayProperties(image)
            display.setConstraint('cmap', 'cmapNames', fslcmap.getColourMaps())
