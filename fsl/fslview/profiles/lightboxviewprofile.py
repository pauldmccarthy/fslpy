#!/usr/bin/env python
#
# lightboxviewprofile.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)


import wx

import fsl.fslview.profiles as profiles


class LightBoxViewProfile(profiles.Profile):
    def __init__(self, canvasPanel, imageList, displayCtx):
        profiles.Profile.__init__(self,
                                  canvasPanel,
                                  imageList,
                                  displayCtx)

        self._canvas = canvasPanel.getCanvas()

    def getEventTargets(self):
        return [self._canvas]

        
    def _mouseWheel(self, ev, canvas, wheel, mousePos=None, canvasPos=None):
        """Called when the mouse wheel is moved.

        Updates the top row displayed on the canvas.
        """
        wheelDir = ev.GetWheelRotation()

        if   wheelDir > 0: wheelDir = -1
        elif wheelDir < 0: wheelDir =  1

        self._canvasPanel.getCanvas().topRow += wheelDir

        
    def _leftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Called when the mouse is clicked or dragged on the canvas.

        Updates the canvas and display context location.
        """

        if canvasPos is None:
            return

        self._displayCtx.location.xyz = canvasPos
