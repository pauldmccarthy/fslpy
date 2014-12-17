#!/usr/bin/env python
#
# The profiles module contains logic for mouse-keyboard interaction.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The :mod:`profiles` module contains logic for mouse/keyboard interaction
with :class:`~fsl.fslview.views.canvaspanel.CanvasPanel` panels.

This logic is encapsulated in two classes:

 - The :class:`Profile` class is intended to be subclassed. A :class:`Profile`
   instance contains the mouse/keyboard event handlers for a particular type
   of ``CanvasPanel`` to allow the user to interact with the canvas in a
   particular way. For example, the
   :class:`~fsl.fslview.profiles.orthoviewprofile.OrthoViewProfile` class
   allows the user to navigate through the image space in an
   :class:`~fsl.fslview.views.orthopanel.OrthoPanel` canvas, wherease the
   :class:`~fsl.fslview.profiles.orthoeditprofile.OrthoEditProfile` class
   contains interaction logic for selecting and editing image voxels in an
   ``OrthoPanel``.


 - The :class:`ProfileManager` class is used by ``CanvasPanel`` instances to
   create and change the ``Profile`` instance currently in use.
"""

import logging
log = logging.getLogger(__name__)

import inspect
import wx
import props


class ActionProvider(props.HasProperties):

    def __init__(self, actions=None):

        if actions is None:
            actions = {}

        self.__actions = {}

        for name, func in actions.items():

            self.addProperty(
                self.__toggleName(name),
                props.Boolean(default=True))

            def wrap(n=name, f=func):
                if not self.isEnabled(n):
                    raise RuntimeError('{} is disabled'.format(name))
                f()

            self.__actions[name] = wrap


    def __toggleName(self, name):
        return '_toggle_{}'.format(name)


    def getActions(self):
        return dict(self.__actions)


    def isEnabled(self, name):
        return getattr(self, self.__toggleName(name))

    
    def enable(self, name):
        setattr(self, self.__toggleName(name))

        
    def disable(self, name):
        setattr(self, self.__toggleName(name))


    def toggle(self, name):
        name = self.__toggleName(name)
        setattr(self, name, not getattr(self, name))


    def run(self, name):
        self.__actions[name]()


class Profile(ActionProvider):
    """A :class:`Profile` class implements keyboard/mouse interaction behaviour
    for a :class:`~fsl.fslview.views.canvaspanel.CanvasPanel` instance.
    

    Things to discuss:
     - tempmodes
     - althandlers
     - actions
     - handler naming convention
    """


    mode = props.Choice()
    

    def __init__(self,
                 canvasPanel,
                 imageList,
                 displayCtx,
                 modes=None,
                 actions=None):

        if actions is not None:
            for name, func in actions.items():
                def wrap(f=func):
                    f()
                    canvasPanel.Refresh()
            actions[name] = wrap

        ActionProvider.__init__(self, actions)
        
        self._canvasPanel = canvasPanel
        self._imageList   = imageList
        self._displayCtx  = displayCtx
        self._name        = '{}_{}'.format(self.__class__.__name__, id(self))

        # Maps which define temporarymodes/alternate
        # handlers when keyboard modifiers are used,
        # or when a handler for a particular event
        # is not defined
        self.__tempModeMap   = {}
        self.__altHandlerMap = {}
        
        # some attributes to keep track
        # of mouse event locations
        self.__lastMousePos  = None
        self.__lastCanvasPos = None
        self.__mouseDownPos  = None
        self.__canvasDownPos = None

        # Add all of the provided modes
        # as options to the mode property
        if modes is None:
            modes = []

        modeProp = self.getProp('mode')

        import fsl.fslview.profilemap as profilemap
        import fsl.fslview.strings    as strings
        for mode in modes:
            modeProp.addChoice(
                mode,
                strings.profileModeTitles[self.__class__][mode],
                self)

        if len(modes) > 0:
            self.mode = modes[0]

        # Configure temporary modes and alternate
        # event handlers - see the profilemap
        # module
        for cls in inspect.getmro(self.__class__):
            
            tempModes   = profilemap.tempModeMap  .get(cls, {})
            altHandlers = profilemap.altHandlerMap.get(cls, {})

            for (mode, keymod), tempMode in tempModes.items():
                self.addTempMode(mode, keymod, tempMode)

            for (mode, handler), (altMode, altHandler) in altHandlers.items():
                self.addAltHandler(mode, handler, altMode, altHandler)


    def getEventTargets(self):
        """
        """
        raise NotImplementedError('Profile subclasses must implement '
                                  'the getEventTargets method')


    def getMouseDownLocation(self):
        """
        """
        return self.__mouseDownPos, self.__canvasDownPos

    
    def getLastMouseLocation(self):
        """
        """
        return self.__lastMousePos, self.__lastCanvasPos


    def addTempMode(self, mode, modifier, tempMode):
        """This map is used by the :meth:`_getTempMode` method to determine
        whether a temporary mode should be enabled, based on any keyboard
        modifier keys that are held down.
        """ 
        self.__tempModeMap[mode, modifier] = tempMode

        
    def addAltHandler(self, mode, event, altMode, altEvent):
        """If a handler is not present for a particular mouse event type, this
        map is checked to see an alternate handler has been defined.
        """
        self.__altHandlerMap[mode, event] = (altMode, altEvent)

    
    def register(self):
        """
        """
        for t in self.getEventTargets():
            t.Bind(wx.EVT_LEFT_DOWN,   self.__onMouseDown)
            t.Bind(wx.EVT_MIDDLE_DOWN, self.__onMouseDown)
            t.Bind(wx.EVT_RIGHT_DOWN,  self.__onMouseDown)
            t.Bind(wx.EVT_LEFT_UP,     self.__onMouseUp)
            t.Bind(wx.EVT_MIDDLE_UP,   self.__onMouseUp)
            t.Bind(wx.EVT_RIGHT_UP,    self.__onMouseUp)
            t.Bind(wx.EVT_MOTION,      self.__onMouseMove)
            t.Bind(wx.EVT_MOUSEWHEEL,  self.__onMouseWheel)
            t.Bind(wx.EVT_CHAR,        self.__onChar)

    
    def deregister(self):
        """
        """
        for t in self.getEventTargets():
            t.Bind(wx.EVT_LEFT_DOWN,  None)
            t.Bind(wx.EVT_MIDDLE_UP,  None)
            t.Bind(wx.EVT_RIGHT_DOWN, None)
            t.Bind(wx.EVT_LEFT_UP,    None)
            t.Bind(wx.EVT_MIDDLE_UP,  None)
            t.Bind(wx.EVT_RIGHT_UP,   None)
            t.Bind(wx.EVT_MOTION,     None)
            t.Bind(wx.EVT_MOUSEWHEEL, None)
            t.Bind(wx.EVT_CHAR,       None)
        self._canvasPanel.Refresh()

    
    def __getTempMode(self, ev):
        """When in a particular mode, keyboard modifier keys can be held
        down to temporarily switch to a different mode.
        """

        mode  = self.mode
        shift = ev.ShiftDown()
        ctrl  = ev.ControlDown()
        alt   = ev.AltDown()

        if shift: return self.__tempModeMap.get((mode, wx.WXK_SHIFT),   None)
        if ctrl:  return self.__tempModeMap.get((mode, wx.WXK_CONTROL), None)
        if alt:   return self.__tempModeMap.get((mode, wx.WXK_ALT),     None)
        
        return None

    
    def __getMouseLocation(self, ev):
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

        canvasPos = [None] * 3

        canvasPos[canvas.xax] = xpos
        canvasPos[canvas.yax] = ypos
        canvasPos[canvas.zax] = zpos
        
        return (mx, my), canvasPos
                                

    def __getMouseButton(self, ev):
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

        
    def __getEventType(self, ev):
        """Returns a string describing the given :class:`wx.MouseEvent` or
        :class:`wx.KeyEvent`.

        This string is then used by the :meth:`_getHandler` method to look up
        a method on this :class:`OrthoViewProfile` instance which can handle
        the event.
        """

        if isinstance(ev, wx.MouseEvent):
            
            btn = self.__getMouseButton(ev)
            if btn is None:
                btn = ''

            if   ev.ButtonUp():              evType = 'Up'
            elif ev.ButtonDown():            evType = 'Down'
            elif ev.Dragging():              evType = 'Drag'
            elif ev.GetWheelRotation() != 0: evType = 'Wheel'

            # Do I need to consider any other mouse event types?
            else:                            evType = 'Move'
            
            return '{}Mouse{}'.format(btn, evType)

        elif isinstance(ev, wx.KeyEvent):
            return 'Char'

        return None


    def __getHandler(self, ev, mode=None, evType=None):
        """Returns a reference to a method of this :class:`OrthoViewProfile`
        instance which can handle the given :class:`wx.MouseEvent` or
        :class:`wx.KeyEvent` (the ``ev`` argument).

        The ``mode`` and ``evType`` arguments may be used to force the lookup
        of a handler for the specified mode (see the :attr:`mode` property)
        or event type (see the :meth:`_getEventType` method).

        If a handler is not found, the :attr:`_altHandlerMap` map is checked
        to see if an alternate handler for the mode/event type has been
        specified.
        """

        tempMode = self.__getTempMode(ev)

        if mode is None:
            if tempMode is None: mode = self.mode
            else:                mode = tempMode
        
        if evType is None:
            evType = self.__getEventType(ev)

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
        alt = self.__altHandlerMap.get((mode, evType), None)

        # An alternate handler has
        # been specified - look it up
        if alt is not None:
            return self.__getHandler(ev, *alt)

        return None

        
    def __onMouseWheel(self, ev):
        """Called when the mouse wheel is moved.

        Delegates to a mode specific handler if one is present.
        """

        handler = self.__getHandler(ev)
        if handler is None:
            return

        mouseLoc, canvasLoc = self.__getMouseLocation(ev)
        canvas              = ev.GetEventObject()
        wheel               = ev.GetWheelRotation()

        log.debug('Mouse wheel event ({}) on canvas {}'.format(
            wheel, canvas.name))

        handler(canvas, wheel, mouseLoc, canvasLoc)
        self._canvasPanel.Refresh()

        
    def __onMouseDown(self, ev):
        """Called when any mouse button is pushed.

        Delegates to a mode specific handler if one is present.
        """
        
        mouseLoc, canvasLoc = self.__getMouseLocation(ev)
        canvas              = ev.GetEventObject()

        self.__mouseDownPos  = mouseLoc
        self.__canvasDownPos = canvasLoc

        if self.__lastMousePos  is None: self.__lastMousePos  = mouseLoc
        if self.__lastCanvasPos is None: self.__lastCanvasPos = canvasLoc

        handler = self.__getHandler(ev)
        if handler is None:
            return

        log.debug('Mouse down event ({}, {}) on canvas {}'.format(
            mouseLoc, canvasLoc, canvas.name))

        handler(canvas, mouseLoc, canvasLoc)
        self._canvasPanel.Refresh()

        self.__lastMousePos  = mouseLoc
        self.__lastCanvasPos = canvasLoc        

    
    def __onMouseUp(self, ev):
        """Called when any mouse button is released.

        Delegates to a mode specific handler if one is present.
        """
        
        handler = self.__getHandler(ev)

        if handler is None:
            self.__mouseDownPos  = None
            self.__canvasDownPos = None
            return

        canvas              = ev.GetEventObject()
        mouseLoc, canvasLoc = self.__getMouseLocation(ev)

        log.debug('Mouse up event ({}, {}) on canvas {}'.format(
            mouseLoc, canvasLoc, canvas.name))

        handler(canvas, mouseLoc, canvasLoc)
        self._canvasPanel.Refresh()
        self.__mouseDownPos  = None
        self.__canvasDownPos = None


    def __onMouseMove(self, ev):
        """Called on mouse motion. If a mouse button is down, delegates to
        :meth:`__onMouseDrag`.

        Otherwise, delegates to a mode specific handler if one is present.
        """

        if ev.Dragging():
            self.__onMouseDrag(ev)
            return

        handler = self.__getHandler(ev)

        if handler is None:
            return
        
        canvas              = ev.GetEventObject()
        mouseLoc, canvasLoc = self.__getMouseLocation(ev)

        log.debug('Mouse move event ({}, {}) on canvas {}'.format(
            mouseLoc, canvasLoc, canvas.name))

        handler(canvas, mouseLoc, canvasLoc)
        self._canvasPanel.Refresh()

    
    def __onMouseDrag(self, ev):
        """Called on mouse drags.
        
        Delegates to a mode specific handler if one is present.
        """
        ev.Skip()

        canvas              = ev.GetEventObject()
        mouseLoc, canvasLoc = self.__getMouseLocation(ev)

        handler = self.__getHandler(ev)
        if handler is None:
            return 

        log.debug('Mouse drag event ({}, {}) on canvas {}'.format(
            mouseLoc, canvasLoc, canvas.name))

        handler(canvas, mouseLoc, canvasLoc)
        self._canvasPanel.Refresh()

        self.__lastMousePos  = mouseLoc
        self.__lastCanvasPos = canvasLoc

        
    def __onChar(self, ev):
        """Called on keyboard key presses .

        Delegates to a mode specific handler if one is present.
        """

        handler = self.__getHandler(ev)
        if handler is None:
            return 

        canvas = ev.GetEventObject()
        key    = ev.GetKeyCode()

        log.debug('Keyboard event ({}) on canvas {}'.format(key, canvas.name))

        handler(canvas, key)
        self._canvasPanel.Refresh()


class ProfileManager(object):
    """
    """


    def __init__(self, canvasPanel, imageList, displayCtx):
        """
        """

        from fsl.fslview.views.orthopanel    import OrthoPanel
        from fsl.fslview.views.lightboxpanel import LightBoxPanel

        from orthoviewprofile    import OrthoViewProfile
        from orthoeditprofile    import OrthoEditProfile
        from lightboxviewprofile import LightBoxViewProfile
        # from lightboxeditprofile import LightBoxEditProfile

        self._profileMap = {
            ('view', OrthoPanel)    : OrthoViewProfile,
            ('edit', OrthoPanel)    : OrthoEditProfile,
            ('view', LightBoxPanel) : LightBoxViewProfile,
        }
                
        self._canvasPanel    = canvasPanel
        self._canvasCls      = canvasPanel.__class__
        self._imageList      = imageList
        self._displayCtx     = displayCtx
        self._currentProfile = None


    def getCurrentProfile(self):
        """
        """
        return self._currentProfile

        
    def changeProfile(self, profile):
        """
        """

        profileCls = self._profileMap[profile, self._canvasCls]

        if self._currentProfile is not None:
            log.debug('Deregistering {} profile from {}'.format(
                self._currentProfile.__class__.__name__,
                self._canvasCls.__name__))
            self._currentProfile.deregister()
               
        self._currentProfile = profileCls(self._canvasPanel,
                                          self._imageList,
                                          self._displayCtx)
        
        log.debug('Registering {} profile with {}'.format(
            self._currentProfile.__class__.__name__,
            self._canvasCls.__name__))
        
        self._currentProfile.register()
