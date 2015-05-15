#!/usr/bin/env python
#
# orthoviewprofile.py - Mouse/keyboard user interaction for the OrthoPanel.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines a mouse/keyboard interaction 'view' profile for the
:class:`.OrthoPanel'` class.

There are three view 'modes' available in this profile:

 - Navigate mode:  The user can change the currently displayed location.

 - Zoom mode:      The user can zoom in/out of a canvas with the mouse 
                   wheel, and draw a rectangle on a canvas in which to
                   zoom.

 - Pan mode:       The user can pan around a canvas (if the canvas is
                   zoomed in).

The :attr:`OrthoViewProfile.mode` property controls the current mode.
Alternately, keyboard modifier keys (e.g. shift) may be used to temporarily
switch into one mode from another; these temporary modes are defined in the
:attr:`OrthoViewProfile._tempModeMap` class attribute.
"""

import logging

import wx

import fsl.fslview.profiles as profiles
import fsl.data.image       as fslimage


log = logging.getLogger(__name__)


class OrthoViewProfile(profiles.Profile):


    def __init__(self,
                 canvasPanel,
                 overlayList,
                 displayCtx,
                 extraModes=None,
                 extraActions=None):
        """Creates an :class:`OrthoViewProfile`, which can be registered
        with the given ``canvasPanel`` which is assumed to be an
        :class:`.OrthoPanel` instance.
        """

        if extraModes   is None: extraModes   = []
        if extraActions is None: extraActions = {}

        modes   = ['nav', 'pan', 'zoom']
        actionz = {
            'resetZoom'    : self.resetZoom,
            'centreCursor' : self.centreCursor,
        }

        modes   = modes + extraModes
        actionz = dict(actionz.items() + extraActions.items())

        profiles.Profile.__init__(self,
                                  canvasPanel,
                                  overlayList,
                                  displayCtx,
                                  modes,
                                  actionz)

        self._xcanvas = canvasPanel.getXCanvas()
        self._ycanvas = canvasPanel.getYCanvas()
        self._zcanvas = canvasPanel.getZCanvas()

        # This attribute will occasionally store a
        # reference to a gl.annotations.Rectangle -
        # see the _zoomModeLeftMouse* handlers
        self._lastRect = None


    def getEventTargets(self):
        """
        """
        return [self._xcanvas, self._ycanvas, self._zcanvas]


    def resetZoom(self, *a):

        opts = self._canvasPanel.getSceneOptions()

        opts.zoom  = 100
        opts.xzoom = 100
        opts.yzoom = 100
        opts.zzoom = 100


    def centreCursor(self, *a):

        bounds = self._displayCtx.bounds

        xmid = bounds.xlo + 0.5 * bounds.xlen
        ymid = bounds.ylo + 0.5 * bounds.ylen
        zmid = bounds.zlo + 0.5 * bounds.zlen

        self._displayCtx.location.xyz = [xmid, ymid, zmid]


    ########################
    # Navigate mode handlers
    ########################


    def _navModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Left mouse drags in location mode update the
        :attr:`.DisplayContext.location` to follow the mouse location.
        """

        if canvasPos is None:
            return

        self._displayCtx.location = canvasPos

        
    def _navModeChar(self, ev, canvas, key):
        """Left mouse drags in location mode update the
        :attr:`.DisplayContext.location`.

        Arrow keys map to the horizontal/vertical axes, and -/+ keys map
        to the depth axis of the canvas which was the target of the event.
        """ 

        overlay = self._displayCtx.getSelectedOverlay()

        if overlay is None:
            return
        
        display = self._displayCtx.getDisplay(overlay)
        pos     = self._displayCtx.location.xyz

        if not isinstance(overlay, fslimage.Image):
            log.warn('Non-volumetric overlay types not supported yet')
            return

        # If we're displaying voxel space,
        # we want a keypress to move one
        # voxel in the appropriate direction
        if   display.transform == 'id':     offsets = [1, 1, 1]
        elif display.transform == 'pixdim': offsets = overlay.pixdim

        # Otherwise we'll just move an arbitrary 
        # amount in the image world space - 2mm
        else:                               offsets = [2, 2, 2]

        try:    ch = chr(key)
        except: ch = None

        if   key == wx.WXK_LEFT:  pos[canvas.xax] -= offsets[canvas.xax]
        elif key == wx.WXK_RIGHT: pos[canvas.xax] += offsets[canvas.xax]
        elif key == wx.WXK_UP:    pos[canvas.yax] += offsets[canvas.yax]
        elif key == wx.WXK_DOWN:  pos[canvas.yax] -= offsets[canvas.yax]
        elif ch  in ('-', '_'):   pos[canvas.zax] -= offsets[canvas.zax]
        elif ch  in ('+', '='):   pos[canvas.zax] += offsets[canvas.zax]

        self._displayCtx.location.xyz = pos

        
    ####################
    # Zoom mode handlers
    ####################

        
    def _zoomModeMouseWheel(self,
                            ev, 
                            canvas,
                            wheel,
                            mousePos=None,
                            canvasPos=None):
        """Mouse wheel motion in zoom mode increases/decreases the zoom level
        of the target canvas.
        """
        if   wheel > 0: wheel =  50
        elif wheel < 0: wheel = -50
        canvas.zoom += wheel

        
    def _zoomModeChar(self, ev, canvas, key):
        """The +/- keys in zoom mode increase/decrease the zoom level
        of the target canvas.
        """

        try:    ch = chr(key)
        except: ch = None

        zoom = 0

        if   key == wx.WXK_DOWN: zoom = -1
        elif key == wx.WXK_UP:   zoom =  1
        elif ch  == '-':         zoom = -1
        elif ch  in ('=', '+'):  zoom =  1

        if zoom == 0:
            return

        self._zoomModeMouseWheel(canvas, zoom)

        
    def _zoomModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Left mouse drags in zoom mode draw a rectangle on the target
        canvas.

        When the user releases the mouse (see :meth:`_zoomModeLeftMouseUp`),
        the canvas will be zoomed in to the drawn rectangle.
        """

        if canvasPos is None:
            return

        mouseDownPos, canvasDownPos = self.getMouseDownLocation()

        corner = [canvasDownPos[canvas.xax], canvasDownPos[canvas.yax]]
        width  = canvasPos[canvas.xax] - corner[0]
        height = canvasPos[canvas.yax] - corner[1]

        self._lastRect = canvas.getAnnotations().rect(corner,
                                                      width,
                                                      height,
                                                      colour=(1, 1, 0))
        canvas.Refresh()

        
    def _zoomModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        """When the left mouse is released in zoom mode, the target
        canvas is zoomed in to the rectangle region that was drawn by the
        user.
        """

        if canvasPos is None:
            return

        mouseDownPos, canvasDownPos = self.getMouseDownLocation()

        if self._lastRect is not None:
            canvas.getAnnotations().dequeue(self._lastRect)
            self._lastRect = None

        rectXlen = abs(canvasPos[canvas.xax] - canvasDownPos[canvas.xax])
        rectYlen = abs(canvasPos[canvas.yax] - canvasDownPos[canvas.yax])

        if rectXlen == 0: return
        if rectYlen == 0: return

        rectXmid = (canvasPos[canvas.xax] + canvasDownPos[canvas.xax]) / 2.0
        rectYmid = (canvasPos[canvas.yax] + canvasDownPos[canvas.yax]) / 2.0

        xlen = self._displayCtx.bounds.getLen(canvas.xax)
        ylen = self._displayCtx.bounds.getLen(canvas.yax)

        xzoom   = xlen / rectXlen
        yzoom   = ylen / rectYlen
        zoom    = min(xzoom, yzoom) * 100.0
        maxzoom = canvas.getConstraint('zoom', 'maxval')

        if zoom >= maxzoom:
            zoom = maxzoom

        if zoom > canvas.zoom:
            canvas.zoom = zoom
            canvas.centreDisplayAt(rectXmid, rectYmid)

        canvas.Refresh()
        
        
    ###################
    # Pan mode handlers
    ###################
    
        
    def _panModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Left mouse drags in pan mode move the target canvas display about
        to follow the mouse.

        If the target canvas is not zoomed in, this has no effect.
        """

        if canvasPos is None:
            return
        
        mouseDownPos, canvasDownPos = self.getMouseDownLocation()

        xoff = canvasPos[canvas.xax] - canvasDownPos[canvas.xax]
        yoff = canvasPos[canvas.yax] - canvasDownPos[canvas.yax]

        canvas.panDisplayBy(-xoff, -yoff)

    
    def _panModeChar(self, ev, canvas, key):
        """The arrow keys in pan mode move the target canvas display around
        (unless the canvas is not zoomed in).
        """

        xoff = 0
        yoff = 0
        
        if   key == wx.WXK_DOWN:  yoff = -2
        elif key == wx.WXK_UP:    yoff =  2
        elif key == wx.WXK_LEFT:  xoff = -2
        elif key == wx.WXK_RIGHT: xoff =  2
        else:                     return

        canvas.panDisplayBy(xoff, yoff)
