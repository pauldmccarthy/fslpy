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

import fsl.fslview.strings as strings
import fsl.fslview.actions as actions


class Profile(actions.ActionProvider):
    """A :class:`Profile` class implements keyboard/mouse interaction behaviour
    for a :class:`~fsl.fslview.views.canvaspanel.CanvasPanel` instance.

    Subclasses should specify at least one 'mode' of operation, which defines
    a sort of sub-profile. The user is able to change the mode via the
    :attr:`mode` property. Subclasses must also override the
    :meth:`getEventTargets` method, to return the :mod:`wx` objects that
    are to be the targets for mouse/keyboard interaction.

    In order to receive mouse or keyboard events, subclasses simply need to
    implement methods which handle the events of interest for the relevant
    mode, and name them appropriately. The name of a method handler must be 
    of the form ``_[modeName]Mode[eventName]``, where ``modeName`` is an
    identifier for the profile mode (see the :meth:`__init__` method), and
    ``eventName`` is one of the following:
    
      - ``LeftMouseMove``
      - ``LeftMouseDown``
      - ``LeftMouseDrag``
      - ``LeftMouseUp``
      - ``RightMouseMove``
      - ``RightMouseDown``
      - ``RightMouseDrag``
      - ``RightMouseUp`` 
      - ``MiddleMouseMove``
      - ``MiddleMouseDown``
      - ``MiddleMouseDrag``
      - ``MiddleMouseUp``
      - ``MouseWheel``
      - ``Char``

    For example, if a particular profile has defined a mode called ``nav``,
    and is interested in left clicks, the profile class must provide a method
    called `_navModeLeftMouseDown`. Then, whenever the profile is in the
    ``nav`` mode, this method will be called on left mouse clicks.

    The :mod:`~fsl.fslview.profilemap` module contains a ``tempModeMap``
    which, for each profile and each mode, defines a keyboard modifier which
    may be used to temporarily redirect mouse/keyboard events to the handlers
    for a different mode. For example, if while in ``nav`` mode, you would
    like the user to be able to switch to ``zoom`` mode with the control key,
    you can add a temporary mode map in the
    :attr:`~fsl.fslview.profilemap.tempModeMap`


    The :mod:`~fsl.fslview.profilemap` contains another dictionary, called
    the ``altHandlerMap``. This dictionary allows you to re-use event
    handlers that have been defined for one mode in another mode. For example,
    if you would like right clicks in ``zoom`` mode to behave like left clicks
    in ``nav`` mode, you can set up such a mapping using the
    :attr:`~fsl.fslview.profilemap.altHandlerMap`` dictionary.
    
    As the :class:`Profile` class derives from the
    :class:`~fsl.fslview.actions.ActionProvider` class, :class:`Profile`
    subclasses may define properties and actions for the user to configure
    the profile behaviour, and/or to perform any relevant actions. 
    """


    mode = props.Choice()
    """The current profile mode - by default this is empty, but subclasses
    may specify the choice options in the :class:`__init__` method.
    """
    

    def __init__(self,
                 canvasPanel,
                 imageList,
                 displayCtx,
                 modes=None,
                 actionz=None):
        """Create a :class:`Profile` instance.

        :arg canvasPanel: The
                          :class:`~fsl.fslview.views.canvaspanel.CanvasPanel`
                          instance for which this :class:`Profile` instance
                          defines mouse/keyboard interaction behaviour.

        :arg imageList:   The :class:`~fsl.data.image.ImageList` instance
                          which contains the list of images being displayed.

        :arg displayCtx:  The
                          :class:`~fsl.fslview.displaycontext.DisplayContext`
                          instance which defines how the images are to be
                          displayed.

        :arg modes:       A sequence of strings, containing the mode
                          identifiers for this profile.

        :arg actionz:     A dictionary of ``{name : function}`` mappings
                          defining any actions provided by this instance; see
                          the :class:`~fsl.fslview.actions.ActionProvider`
                          class.
        """

        if actionz is not None:
            for name, func in actionz.items():
                def wrap(f=func):
                    f()
                    canvasPanel.Refresh()
                actionz[name] = wrap

        actions.ActionProvider.__init__(self, imageList, displayCtx, actionz)
        
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
        
        for mode in modes:
            modeProp.addChoice(mode, strings.labels[self, mode], self)

        if len(modes) > 0:
            self.mode = modes[0]

        # Configure temporary modes and alternate
        # event handlers - see the profilemap
        # module
        import fsl.fslview.profilemap as profilemap
        
        for cls in inspect.getmro(self.__class__):
            
            tempModes   = profilemap.tempModeMap  .get(cls, {})
            altHandlers = profilemap.altHandlerMap.get(cls, {})

            for (mode, keymod), tempMode in tempModes.items():
                self.addTempMode(mode, keymod, tempMode)

            for (mode, handler), (altMode, altHandler) in altHandlers.items():
                self.addAltHandler(mode, handler, altMode, altHandler)


    def getEventTargets(self):
        """Must be overridden by subclasses, to return a sequence of
        :mod:`wx` objects that are the targets of mouse/keyboard interaction.

        It is assumed that all of the objects in the sequence derive from the
        :class:`~fsl.fslview.gl.slicecanvas.SliceCanvas` class.
        """
        raise NotImplementedError('Profile subclasses must implement '
                                  'the getEventTargets method')


    def getMouseDownLocation(self):
        """If the mouse is currently down, returns a 2-tuple containing the
        x/y mouse coordinates, and the corresponding 3D display space
        coordinates, of the mouse down event. Otherwise, returns
        ``(None, None)``.
        """
        return self.__mouseDownPos, self.__canvasDownPos

    
    def getLastMouseLocation(self):
        """Returns a 2-tuple containing the most recent x/y mouse coordinates,
        and the corresponding 3D display space coordinates. 
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
        """This method must be called to register this :class:`Profile`
        instance as the target for mouse/keyboard events.
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
        """This method de-registers this :class:`Profile` instance from
        receiving mouse/keybouard events.
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
        """Checks the temporary mode map to see if a temporary mode should
        be applied. Returns the mode identifier, or ``None`` if no temporary
        mode is applicable.
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
        given :class:`wx.MouseEvent`, and the second contains the
        corresponding x/y/z display space coordinates.
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
        """Returns a reference to a method of this :class:`Profile`
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

        handler(ev, canvas, wheel, mouseLoc, canvasLoc)
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

        handler(ev, canvas, mouseLoc, canvasLoc)
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

        handler(ev, canvas, mouseLoc, canvasLoc)
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

        handler(ev, canvas, mouseLoc, canvasLoc)
        self._canvasPanel.Refresh()

        self.__lastMousePos  = mouseLoc
        self.__lastCanvasPos = canvasLoc        

    
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

        handler(ev, canvas, mouseLoc, canvasLoc)
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

        handler(ev, canvas, key)
        self._canvasPanel.Refresh()


class ProfileManager(object):
    """Manages creation/registration/de-regsistration of
    :class:`Profile` instances for a
    :class:`~fsl.fslview.views.canvaspanel.CanvasPanel` instance.

    A :class:`ProfileManager` instance is created and used by every
    :class:~fsl.fslview.views.canvaspanel.CanvasPanel` instance. The
    :mod:`~fsl.fslview.profilemap` defines the :class:`Profile` types
    which should be used for specific
    :class:`~fsl.fslview.views.canvaspanel.CanvasPanel` types.
    """


    def __init__(self, canvasPanel, imageList, displayCtx):
        """Create a :class:`ProfileManager`.

        :arg canvasPanel: The 
                          :class:`~fsl.fslview.views.canvaspanel.CanvasPanel`
                          instance which this :class:`ProfileManager` is
                          to manage.
        
        :arg imageList:   The :class:`~fsl.data.image.ImageList` instance
                          containing the images that are being displayed.
        
        :arg displayCtx:  The
                          :class:`~fsl.fslview.displaycontext.DisplayContext`
                          instance which defines how images are being
                          displayed.
        """
        self._canvasPanel    = canvasPanel
        self._canvasCls      = canvasPanel.__class__
        self._imageList      = imageList
        self._displayCtx     = displayCtx
        self._currentProfile = None


    def getCurrentProfile(self):
        """Returns the :class:`Profile` instance currently in use."""
        return self._currentProfile

        
    def changeProfile(self, profile):
        """Deregisters the current :class:`Profile` instance (if necessary),
        and creates a new one corresponding to the named profile.
        """

        import fsl.fslview.profilemap as profilemap

        profileCls = profilemap.profiles[self._canvasCls, profile]

        # the current profile is the requested profile
        if (self._currentProfile is not None) and \
           (self._currentProfile.__class__ is profileCls):
            return

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
