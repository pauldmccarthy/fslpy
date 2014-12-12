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
            c.Bind(wx.EVT_LEFT_DOWN,   self._onMouseDown)
            c.Bind(wx.EVT_MIDDLE_DOWN, self._onMouseDown)
            c.Bind(wx.EVT_RIGHT_DOWN,  self._onMouseDown)
            c.Bind(wx.EVT_LEFT_UP,     self._onMouseUp)
            c.Bind(wx.EVT_MIDDLE_UP,   self._onMouseUp)
            c.Bind(wx.EVT_RIGHT_UP,    self._onMouseUp) 
            c.Bind(wx.EVT_MOTION,      self._onMouseDrag)
            c.Bind(wx.EVT_MOUSEWHEEL,  self._onMouseWheel)
            c.Bind(wx.EVT_CHAR,        self._onChar)
            c.Bind(wx.EVT_KEY_DOWN,    self._onKeyDown)
            c.Bind(wx.EVT_KEY_UP,      self._onKeyUp)

            
    def deregister(self):
        for c in [self._xcanvas, self._ycanvas, self._zcanvas]:
            c.Bind(wx.EVT_LEFT_DOWN,  None)
            c.Bind(wx.EVT_MIDDLE_UP,  None)
            c.Bind(wx.EVT_RIGHT_DOWN, None)
            c.Bind(wx.EVT_LEFT_UP,    None)
            c.Bind(wx.EVT_MIDDLE_UP,  None)
            c.Bind(wx.EVT_RIGHT_UP,   None)
            c.Bind(wx.EVT_MOTION,     None)
            c.Bind(wx.EVT_MOUSEWHEEL, None)
            c.Bind(wx.EVT_CHAR,       None)
            c.Bind(wx.EVT_KEY_DOWN,   None)
            c.Bind(wx.EVT_KEY_UP,     None)
            

    _keyModMap = {
        ('loc', wx.WXK_SHIFT)   : 'pan',
        ('loc', wx.WXK_CONTROL) : 'zoom',
        ('loc', wx.WXK_ALT)     : 'rect',
    }
    """When in a particular mode, keyboard modifier keys can be held
    down to temporarily switch to a different mode.
    """
    

    _altModMap = {
        ('loc',  'RightMouseDrag')   : ('loc',  'LeftMouseDrag'),
        ('loc',  'MiddleMouseDrag')  : ('pan',  'LeftMouseDrag'),

        ('loc',  'RightMouseDown')   : ('loc',  'RightMouseDrag'),
        ('pan',  'RightMouseDown')   : ('pan',  'RightMouseDrag'),
        ('zoom', 'RightMouseDown')   : ('zoom', 'RightMouseDrag'),
        ('rect', 'RightMouseDown')   : ('rect', 'RightMouseDrag'),
        ('loc',  'LeftMouseDown')    : ('loc',  'LeftMouseDrag'),
        ('pan',  'LeftMouseDown')    : ('pan',  'LeftMouseDrag'),
        ('zoom', 'LeftMouseDown')    : ('zoom', 'LeftMouseDrag'),
        ('rect', 'LeftMouseDown')    : ('rect', 'LeftMouseDrag'),

        ('zoom', 'RightMouseDrag')   : ('loc',  'LeftMouseDrag'),
        ('zoom', 'MiddleMouseDrag')  : ('pan',  'LeftMouseDrag'),
    }
    """If a handler is not present for a particular mouse event type, this
    map is checked to see an alternate handler has been defined
    """


    def _getMouseLocation(self, ev):
        """Returns two tuples; the first contains the x/y coordinates of the
        given :class:`wx.MouseEvent`, and the second contains the x/y/z
        display system coordinates of the
        :class:`~fsl.fslview.gl.slicecanvas.SliceCanvas` associated with the
        event.
        """

        mx, my  = ev.GetPositionTuple()
        canvas  = ev.GetEventObject()
        w, h    = canvas.GetClientSize()
        my      = h - my

        xpos, ypos = canvas.canvasToWorld(mx, my)
        zpos       = canvas.pos.z 
        
        return (mx, my), (xpos, ypos, zpos)
                                

    def _getMouseButton(self, ev):
        """Returns a string describing the mouse button associated with the
        given :class:`wx.MouseEvent`.
        """
        
        btn = ev.GetButton()
        if   btn == wx.MOUSE_BTN_LEFT:   return 'Left'
        elif btn == wx.MOUSE_BTN_RIGHT:  return 'Right'
        elif btn == wx.MOUSE_BTN_MIDDLE: return 'Middle'
        elif ev.LeftIsDown():            return 'Left'  
        elif ev.RightIsDown():           return 'Right' 
        elif ev.MiddleIsDown():          return 'Middle'
        else:                            return  None

        
    def _getEventType(self, ev):
        """Returns a string describing the given :class:`wx.MouseEvent` or
        :class:`wx.KeyEvent`.

        This string is then used by the :meth:`_getHandler` method to look up
        a method on this :class:`OrthoViewProfile` instance which can handle
        the event.
        """

        if isinstance(ev, wx.MouseEvent):
            
            btn = self._getMouseButton(ev)
            if btn is None:
                btn = ''

            # mouse motion (without dragging)
            # is currently not supported
            if   ev.ButtonUp():              evType = 'Up'
            elif ev.ButtonDown():            evType = 'Down'
            elif ev.Dragging():              evType = 'Drag'
            elif ev.GetWheelRotation() != 0: evType = 'Wheel'
            else:                            return None
            
            return '{}Mouse{}'.format(btn, evType)

        elif isinstance(ev, wx.KeyEvent):
            return 'Char'

        return None

                
    def _getHandler(self, ev, mode=None, evType=None):
        """Returns a reference to a method of this :class:`OrthoViewProfile`
        instance which can handle the given :class:`wx.MouseEvent` or
        :class:`wx.KeyEvent` (the `ev` argument).

        The `mode` and `evType` arguments may be used to force the lookup
        of a handler for the specified mode (see the :attr:`mode` property)
        or event type (see the :meth:`_getEventType` method).

        If a handler is not found, the :attr:`_altModMap` map is checked to
        see if an alternate handler for the mode/event type has been
        specified.
        """

        if mode   is None: mode   = self.mode
        if evType is None: evType = self._getEventType(ev)

        # Search for a method which can
        # handle the specified mode/evtype
        handlerName = '_{}Mode{}'.format(mode, evType)
        handler     = getattr(self, handlerName, None)

        if handler is not None:
            log.debug('Handler found for mode {}, event {}'.format(mode,
                                                                   evType))
            return handler
        
        # No handler found - search 
        # the alternate handler map
        alt = self._altModMap.get((mode, evType), None)

        # An alternate handler has
        # been specified - look it up
        if alt is not None:
            return self._getHandler(ev, *alt)

        return None

            
    def _onKeyDown(self, ev):
        """Handles presses of modifier keys (e.g. SHIFT, CTRL).

        If a temporary mode has been specified in the :attr:`_keyModMap`, the
        :attr:`mode` property is changed to that mode (and then changed back
        when the modifier key is released - see the :meth:`_onKeyUp` method).
        """
        
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
        """Handles modifier key releases (e.g. SHIFT).

        If the :attr:`mode` has been temporarily changed to a different
        mode (see :meth:`_onKeyDown`), it is changed back to the previous
        mode.
        """
        
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
        """Called when the mouse wheel is moved."""

        handler = self._getHandler(ev)
        if handler is None:
            return

        canvas = ev.GetEventObject()
        wheel  = ev.GetWheelRotation()

        log.debug('Mouse wheel event ({}) on canvas {}'.format(
            wheel, canvas.name))

        handler(canvas, wheel)

        
    def _onMouseDown(self, ev):
        """Called when any mouse button is pushed. """
        
        mouseLoc, canvasLoc = self._getMouseLocation(ev)
        canvas              = ev.GetEventObject()

        self._mouseDownPos  = mouseLoc
        self._canvasDownPos = canvasLoc

        handler = self._getHandler(ev)
        if handler is None:
            return

        log.debug('Mouse down event ({}, {}) on canvas {}'.format(
            mouseLoc, canvasLoc, canvas.name))

        handler(canvas, mouseLoc, canvasLoc)

    
    def _onMouseUp(self, ev):
        """Called when any mouse button is released. """
        
        handler = self._getHandler(ev)

        if handler is None:
            self._mouseDownPos  = None
            self._canvasDownPos = None
            return

        canvas              = ev.GetEventObject()
        mouseLoc, canvasLoc = self._getMouseLocation(ev)

        log.debug('Mouse up event ({}, {}) on canvas {}'.format(
            mouseLoc, canvasLoc, canvas.name))

        handler(canvas, mouseLoc, canvasLoc)
        self._mouseDownPos  = None
        self._canvasDownPos = None 

    
    def _onMouseDrag(self, ev):
        """Called on mouse drags."""
        ev.Skip()

        canvas              = ev.GetEventObject()
        mouseLoc, canvasLoc = self._getMouseLocation(ev)
        
        if self._lastMousePos is None:
            self._lastMousePos = mouseLoc

        handler = self._getHandler(ev)
        if handler is None:
            return 

        log.debug('Mouse drag event ({}, {}) on canvas {}'.format(
            mouseLoc, canvasLoc, canvas.name))

        handler(canvas, mouseLoc, canvasLoc)

        self._lastMousePos = mouseLoc

        
    def _onChar(self, ev):
        """Called on keyboard key presses (modifier keys are handled by the
        :meth:`_onKeyDown` and :meth:`_onKeyUp` methods)."""

        handler = self._getHandler(ev)
        if handler is None:
            return 

        canvas = ev.GetEventObject()
        key    = ev.GetKeyCode()

        log.debug('Keyboard event ({}) on canvas {}'.format(key, canvas.name))

        handler(canvas, key)


    ########################
    # Location mode handlers
    ########################


    def _locModeLeftMouseDrag(self, canvas, (mx, my), (xpos, ypos, zpos)):
        if   canvas == self._xcanvas: pos = (zpos, xpos, ypos)
        elif canvas == self._ycanvas: pos = (xpos, zpos, ypos)
        elif canvas == self._zcanvas: pos = (xpos, ypos, zpos)
        self._displayCtx.location = pos

        
    def _locModeChar(self, canvas, key):

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

        
    ####################
    # Zoom mode handlers
    ####################

        
    def _zoomModeLeftMouseDrag(self, canvas, (mx, my), (xpos, ypos, zpos)):
        ydiff = my - self._lastMousePos[1]
        self._zoomModeMouseWheel(canvas, ydiff)

        
    def _zoomModeMouseWheel(self, canvas, wheel):
        if   wheel > 0: wheel =  10
        elif wheel < 0: wheel = -10
        canvas.zoom += wheel

    
    def _zoomModeChar(self, canvas, key):

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

        
    ###################
    # Pan mode handlers
    ###################
    
        
    def _panModeLeftMouseDrag(self, canvas, (mx, my), (xpos, ypos, zpos)):

        xoff = xpos - self._canvasDownPos[0]
        yoff = ypos - self._canvasDownPos[1]

        canvas.panDisplayBy(-xoff, -yoff)

    
    def _panModeChar(self, canvas, key):

        xoff = 0
        yoff = 0
        
        if   key == wx.WXK_DOWN:  yoff = -2
        elif key == wx.WXK_UP:    yoff =  2
        elif key == wx.WXK_LEFT:  xoff = -2
        elif key == wx.WXK_RIGHT: xoff =  2
        else:                     return

        canvas.panDisplayBy(xoff, yoff)


    #########################
    # Rectangle mode handlers
    #########################
        
    
    def _rectModeLeftMouseDrag(self, canvas, (mx, my), (xpos, ypos, zpos)):

        corner = [self._canvasDownPos[0],
                  self._canvasDownPos[1]]
        width  = xpos - corner[0]
        height = ypos - corner[1]

        self._lastRect = canvas.getAnnotations().rect(corner,
                                                      width,
                                                      height,
                                                      colour=(1, 1, 0))
        canvas.Refresh()

        
    def _rectModeLeftMouseUp(self, canvas, (mx, my), (xpos, ypos, zpos)):

        rectXlen = abs(xpos - self._canvasDownPos[0])
        rectYlen = abs(ypos - self._canvasDownPos[1])

        rectXmid = (xpos + self._canvasDownPos[0]) / 2.0
        rectYmid = (ypos + self._canvasDownPos[1]) / 2.0

        xlen = self._displayCtx.bounds.getLen(canvas.xax)
        ylen = self._displayCtx.bounds.getLen(canvas.yax)

        xzoom = xlen / rectXlen
        yzoom = ylen / rectYlen
        zoom  = min(xzoom, yzoom) * 100.0

        if zoom <= canvas.getConstraint('zoom', 'maxval'):
            canvas.zoom = zoom
            canvas.centreDisplayAt(rectXmid, rectYmid)

        canvas.getAnnotations().dequeue(self._lastRect)
        canvas.Refresh()
