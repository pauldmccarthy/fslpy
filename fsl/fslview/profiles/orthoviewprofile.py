#!/usr/bin/env python
#
# orthoviewprofile.py - Mouse/keyboard user interaction for the OrthoPanel.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines a mouse/keyboard interaction 'view' profile for the
:class:`~fsl.fslview.views.orthopanel.OrthoPanel'` class.
"""

import logging
log = logging.getLogger(__name__)

from collections import OrderedDict

import wx

import props


def register(canvasPanel, imageList, displayCtx):
    return OrthoViewProfile(canvasPanel, imageList, displayCtx)


def deregister(orthoViewProf):
    orthoViewProf.deregister()


class OrthoViewProfile(props.HasProperties):

    mode = props.Choice(
        OrderedDict([
            ('loc',  'Location'),
            ('zoom', 'Zoom'),
            ('pan',  'Pan'),
            ('rect', 'Rectangle Zoom')]))

    def __init__(self, canvasPanel, imageList, displayCtx):
        self._canvasPanel = canvasPanel
        self._imageList   = imageList
        self._displayCtx  = displayCtx
        self._name        = '{}_{}'.format(self.__class__.__name__, id(self))

        self._xcanvas = canvasPanel.getXCanvas()
        self._ycanvas = canvasPanel.getYCanvas()
        self._zcanvas = canvasPanel.getZCanvas()

        self._lastMode      = self.mode
        self._inTempMode    = False
        self._lastMousePos  = None
        self._mouseDownPos  = None
        self._canvasDownPos = None

        self.register()

        
    def register(self):
        for c in [self._xcanvas, self._ycanvas, self._zcanvas]:
            c.Bind(wx.EVT_LEFT_DOWN,  self._onMouseDown)
            c.Bind(wx.EVT_RIGHT_DOWN, self._onMouseDown)
            c.Bind(wx.EVT_MOTION,     self._onMouseMove)
            c.Bind(wx.EVT_MOUSEWHEEL, self._onMouseWheel)
            c.Bind(wx.EVT_CHAR,       self._onChar)
            c.Bind(wx.EVT_KEY_DOWN,   self._onKeyDown)
            c.Bind(wx.EVT_KEY_UP,     self._onKeyUp)

            
    def deregister(self):
        for c in [self._xcanvas, self._ycanvas, self._zcanvas]:
            c.Bind(wx.EVT_LEFT_DOWN,  None)
            c.Bind(wx.EVT_RIGHT_DOWN, None)
            c.Bind(wx.EVT_MOTION,     None)
            c.Bind(wx.EVT_MOUSEWHEEL, None)
            c.Bind(wx.EVT_CHAR,       None)
            c.Bind(wx.EVT_KEY_DOWN,   None)
            c.Bind(wx.EVT_KEY_UP,     None)
            

    # When in a particular mode, keyboard modifiers can be
    # held down to temporarily switch to a different mode
    _keyModMap = {
        ('loc', wx.WXK_SHIFT)   : 'pan',
        ('loc', wx.WXK_CONTROL) : 'zoom',
        ('loc', wx.WXK_ALT)     : 'rect',
    }

            
    def _onKeyDown(self, ev):
        
        key      = ev.GetKeyCode()
        tempMode = self._keyModMap.get((self.mode, key), None)

        if self._inTempMode or (tempMode is None):
            ev.Skip()
        else:
            
            log.debug('Setting temporary mode from '
                      'keyboard modifier {} -> {}'.format(
                          self.mode, tempMode))
            
            self._inTempMode = True
            self._lastMode   = self.mode
            self.mode        = tempMode

    
    def _onKeyUp(self, ev):
        
        key      = ev.GetKeyCode()
        tempMode = self._keyModMap.get((self._lastMode, key), None)

        if (not self._inTempMode) or (tempMode is None):
            ev.Skip()
        else:
            
            log.debug('Clearing temporary mode from '
                      'keyboard modifier {} -> {}'.format(
                          self.mode, self._lastMode))
            
            self._inTempMode = False
            self.mode        = self._lastMode

        
    def _onMouseWheel(self, ev):
        
        handler = '_{}ModeWheelEvent'.format(self.mode)
        handler = getattr(self, handler, None)

        if handler is None:
            return

        canvas = ev.GetEventObject()
        wheel  = ev.GetWheelRotation()

        handler(canvas, wheel)

        
    def _onMouseDown(self, ev):
        
        mx, my  = ev.GetPositionTuple()
        canvas  = ev.GetEventObject()
        w, h    = canvas.GetClientSize()
        my      = h - my 
        
        xpos, ypos = canvas.canvasToWorld(mx, my)
        zpos = canvas.pos.z

        self._mouseDownPos  = (mx, my)
        self._canvasDownPos = (xpos, ypos, zpos)

        self._onMouseMove(ev)

    
    def _onMouseUp(self, ev):
        self._mouseDownPos  = None
        self._canvasDownPos = None

    
    def _onMouseMove(self, ev):
        """Called on mouse movement and left clicks. The currently
        displayed slices and cursor positions on each of the
        canvases follow mouse clicks and drags.
        """
        ev.Skip()


        if   ev.LeftIsDown():  button = 'Left'
        elif ev.RightIsDown(): button = 'Right' 
        else:                  return
        
        mx, my  = ev.GetPositionTuple()
        canvas  = ev.GetEventObject()
        w, h    = canvas.GetClientSize()
        my = h - my
        
        if self._lastMousePos is None:
            self._lastMousePos = (mx, my)
            
        handler = '_{}Mode{}MouseEvent'.format(self.mode, button)
        handler = getattr(self, handler, None)

        if handler is None:           return
        if len(self._imageList) == 0: return 

        xpos, ypos = canvas.canvasToWorld(mx, my)
        zpos = canvas.pos.z

        log.debug('Mouse event ({}, {}) on canvas '
                  '{} (location ({}, {}, {})'.format(
                      mx, my, canvas.name, xpos, ypos, zpos))

        handler(canvas, mx, my, xpos, ypos, zpos)

        self._lastMousePos = (mx, my)

        
    def _onChar(self, ev):

        canvas = ev.GetEventObject()
        key    = ev.GetKeyCode()

        handler = '_{}ModeCharEvent'.format(self.mode)
        handler = getattr(self, handler, None)
        
        if handler is None: return

        handler(canvas, key)


    def _locModeLeftMouseEvent(self, canvas, mx, my, xpos, ypos, zpos):
        if   canvas == self._xcanvas: pos = (zpos, xpos, ypos)
        elif canvas == self._ycanvas: pos = (xpos, zpos, ypos)
        elif canvas == self._zcanvas: pos = (xpos, ypos, zpos)
        self._displayCtx.location = pos

        
    def _locModeRightMouseEvent(self, canvas, mx, my, xpos, ypos, zpos):
        pass

    
    def _locModeCharEvent(self, canvas, key):

        pos = canvas.pos.xyz

        try:    ch = chr(key)
        except: ch = None

        if   key == wx.WXK_LEFT:  pos[0] -= 2
        elif key == wx.WXK_RIGHT: pos[0] += 2
        elif key == wx.WXK_UP:    pos[1] += 2
        elif key == wx.WXK_DOWN:  pos[1] -= 2
        elif ch  == '-':          pos[2] -= 2
        elif ch  in ('+', '='):   pos[2] += 2

        x, y, z = pos

        if   canvas == self._xcanvas: pos = (z, x, y)
        elif canvas == self._ycanvas: pos = (x, z, y)
        elif canvas == self._zcanvas: pos = (x, y, z)

        self._displayCtx.location = pos

        
    def _zoomModeLeftMouseEvent(self, canvas, mx, my, xpos, ypos, zpos):
        ydiff = my - self._lastMousePos[1]
        self._zoomModeWheelEvent(canvas, ydiff)
    

    def _zoomModeWheelEvent(self, canvas, wheel):
        if   wheel > 0: wheel =  10
        elif wheel < 0: wheel = -10
        canvas.zoom += wheel

    
    def _zoomModeCharEvent(self, canvas, key):

        try:    ch = chr(key)
        except: ch = None

        zoom = 0

        if   key == wx.WXK_DOWN: zoom = -1
        elif key == wx.WXK_UP:   zoom =  1
        elif ch  == '-':         zoom = -1
        elif ch  in ('=', '+'):  zoom =  1

        if zoom == 0:
            return

        self._zoomModeWheelEvent(canvas, zoom)


    def _panModeLeftMouseEvent(self, canvas, mx, my, xpos, ypos, zpos):

        xoff = xpos - self._canvasDownPos[0]
        yoff = ypos - self._canvasDownPos[1]

        canvas.panDisplayBy(-xoff, -yoff)

    
    def _panModeCharEvent(self, canvas, key):

        xoff = 0
        yoff = 0
        
        if   key == wx.WXK_DOWN:  yoff = -2
        elif key == wx.WXK_UP:    yoff =  2
        elif key == wx.WXK_LEFT:  xoff = -2
        elif key == wx.WXK_RIGHT: xoff =  2
        else:                     return

        canvas.panDisplayBy(xoff, yoff)
 
    
    # def _rectModeMouseEvent(self, canvas, mx, my, xpos, ypos):
    #     pass 

    # def _rectModeCharEvent(self, canvas, key):
    #     pass 
