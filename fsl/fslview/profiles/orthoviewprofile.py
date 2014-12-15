#!/usr/bin/env python
#
# orthoviewprofile.py - Mouse/keyboard user interaction for the OrthoPanel.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines a mouse/keyboard interaction 'view' profile for the
:class:`~fsl.fslview.views.orthopanel.OrthoPanel'` class.

There are three view 'modes' available in this profile:

 - Location mode:  The user can change the currently displayed location.

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
log = logging.getLogger(__name__)

from collections import OrderedDict

import wx

import props

import fsl.fslview.profiles as profiles


class OrthoViewProfile(profiles.Profile):

    mode = props.Choice(
        OrderedDict([
            ('loc',  'Location'),
            ('zoom', 'Zoom'),
            ('pan',  'Pan')]))


    def __init__(self, canvasPanel, imageList, displayCtx):
        """Creates an :class:`OrthoViewProfile`, which can be registered
        with the given ``canvasPanel`` which is assumed to be a
        :class:`~fsl.fslview.views.orthopanel.OrthoPanel` instance.
        """
        profiles.Profile.__init__(self, canvasPanel, imageList, displayCtx)

        self._xcanvas = canvasPanel.getXCanvas()
        self._ycanvas = canvasPanel.getYCanvas()
        self._zcanvas = canvasPanel.getZCanvas()

        self.addTempMode('loc', wx.WXK_ALT,     'pan')
        self.addTempMode('loc', wx.WXK_CONTROL, 'zoom')
        
        self.addAltHandler('loc',  'RightMouseDrag',  'loc',  'LeftMouseDrag')
        self.addAltHandler('loc',  'MiddleMouseDrag', 'pan',  'LeftMouseDrag')
        self.addAltHandler('loc',  'RightMouseDown',  'loc',  'RightMouseDrag')
        self.addAltHandler('pan',  'RightMouseDown',  'pan',  'RightMouseDrag')
        self.addAltHandler('zoom', 'RightMouseDown',  'zoom', 'RightMouseDrag')
        self.addAltHandler('loc',  'LeftMouseDown',   'loc',  'LeftMouseDrag')
        self.addAltHandler('pan',  'LeftMouseDown',   'pan',  'LeftMouseDrag')
        self.addAltHandler('zoom', 'LeftMouseDown',   'zoom', 'LeftMouseDrag')
        self.addAltHandler('zoom', 'RightMouseDrag',  'loc',  'LeftMouseDrag')
        self.addAltHandler('zoom', 'MiddleMouseDrag', 'pan',  'LeftMouseDrag')        


    def getEventTargets(self):
        """
        """
        return [self._xcanvas, self._ycanvas, self._zcanvas]


    ########################
    # Location mode handlers
    ########################


    def _locModeLeftMouseDrag(self, canvas, mousePos, canvasPos):
        """Left mouse drags in location mode update the
        :attr:`~fsl.fslview.displaycontext.DisplayContext.location` to follow
        the mouse location.
        """
        
        self._displayCtx.location = canvasPos

        
    def _locModeChar(self, canvas, key):
        """Left mouse drags in location mode update the
        :attr:`~fsl.fslview.displaycontext.DisplayContext.location`.

        Arrow keys map to the horizontal/vertical axes, and -/+ keys map
        to the depth axis of the canvas which was the target of the event.
        """ 

        pos = self._displayCtx.location.xyz

        try:    ch = chr(key)
        except: ch = None

        if   key == wx.WXK_LEFT:  pos[canvas.xax] -= 2
        elif key == wx.WXK_RIGHT: pos[canvas.xax] += 2
        elif key == wx.WXK_UP:    pos[canvas.yax] += 2
        elif key == wx.WXK_DOWN:  pos[canvas.yax] -= 2
        elif ch  in ('-', '_'):   pos[canvas.zax] -= 2
        elif ch  in ('+', '='):   pos[canvas.zax] += 2

        self._displayCtx.location = pos

        
    ####################
    # Zoom mode handlers
    ####################

        
    def _zoomModeMouseWheel(self, canvas, wheel):
        """Mouse wheel motion in zoom mode increases/decreases the zoom level
        of the target canvas.
        """
        if   wheel > 0: wheel =  10
        elif wheel < 0: wheel = -10
        canvas.zoom += wheel

        
    def _zoomModeChar(self, canvas, key):
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

        
    def _zoomModeLeftMouseDrag(self, canvas, mousePos, canvasPos):
        """Left mouse drags in zoom mode draw a rectangle on the target
        canvas.

        When the user releases the mouse (see :meth:`_zoomModeLeftMouseUp`),
        the canvas will be zoomed in to the drawn rectangle.
        """

        mouseDownPos, canvasDownPos = self.getMouseDownLocation()

        corner = [canvasDownPos[canvas.xax], canvasDownPos[canvas.yax]]
        width  = canvasPos[canvas.xax] - corner[0]
        height = canvasPos[canvas.yax] - corner[1]

        self._lastRect = canvas.getAnnotations().rect(corner,
                                                      width,
                                                      height,
                                                      colour=(1, 1, 0))
        canvas.Refresh()

        
    def _zoomModeLeftMouseUp(self, canvas, mousePos, canvasPos):
        """When the left mouse is released in zoom mode, the target
        canvas is zoomed in to the rectangle region that was drawn by the
        user.
        """

        mouseDownPos, canvasDownPos = self.getMouseDownLocation()

        canvas.getAnnotations().dequeue(self._lastRect)

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
    
        
    def _panModeLeftMouseDrag(self, canvas, mousePos, canvasPos):
        """Left mouse drags in pan mode move the target canvas display about
        to follow the mouse.

        If the target canvas is not zoomed in, this has no effect.
        """
        
        mouseDownPos, canvasDownPos = self.getMouseDownLocation()

        xoff = canvasPos[canvas.xax] - canvasDownPos[canvas.xax]
        yoff = canvasPos[canvas.yax] - canvasDownPos[canvas.yax]

        canvas.panDisplayBy(-xoff, -yoff)

    
    def _panModeChar(self, canvas, key):
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
