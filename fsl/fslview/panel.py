#!/usr/bin/env python
#
# panel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides an important class - the :class:`FSLViewPanel`.

A :class:`FSLViewPanel` object is a :class:`wx.Panel` which provides some sort
of view of a collection of overlay objects, contained within an
:class:`.OverlayList`. 

``FSLViewPanel`` instances are also :class:`.ActionProvider` instances - any
actions which are specified during construction may (or may not ) be exposed
to the user. Furthermore, any display configuration options which should be
made available available to the user should be added as :class:`.PropertyBase`
attributes of the :class:`FSLViewPanel` subclass.

See the following for examples of :class:`FSLViewPanel` subclasses:

  - :class:`.OrthoPanel`
  - :class:`.LightBoxPanel`
  - :class:`.TimeSeriesPanel`
  - :class:`.OverlayListPanel`
  - :class:`.OverlayDisplayPanel`
  - :class:`.LocationPanel`
"""


import logging

import wx

import actions
import displaycontext


log = logging.getLogger(__name__)


class _FSLViewPanel(actions.ActionProvider):
    """Superclass for FSLView view panels.

    A :class:`ViewPanel` has the following attributes, intended to be
    used by subclasses:
    
      - :attr:`_overlayList`: A reference to the :class:`.OverlayList`
        instance which contains the images to be displayed.
    
      - :attr:`_displayCtx`: A reference to the
        :class:`~fsl.fslview.displaycontext.DisplayContext` instance, which
        contains display related properties about the :attr:`_overlayList`.
    
      - :attr:`_name`: A unique name for this :class:`ViewPanel`.


    TODO Important notes about:

      - :meth:`destroy`

      - :meth:`__del__`
    """ 

    
    def __init__(self,
                 overlayList,
                 displayCtx,
                 actionz=None):
        """Create a :class:`ViewPanel`.

        :arg overlayList: A :class:`.OverlayList` instance.
        
        :arg displayCtx:  A :class:`.DisplayContext` instance.

        :arg actionz:     A dictionary containing ``{name -> function}``
                          actions (see :class:`.ActionProvider`).
        """
        
        actions.ActionProvider.__init__(self, overlayList, displayCtx, actionz)

        if not isinstance(displayCtx, displaycontext.DisplayContext):
            raise TypeError(
                'displayCtx must be a '
                '{} instance'.format( displaycontext.DisplayContext.__name__))

        self._overlayList = overlayList
        self._displayCtx  = displayCtx
        self._name        = '{}_{}'.format(self.__class__.__name__, id(self))
        self.__destroyed  = False

        
    def destroy(self):
        """This method must be called by whatever is managing this
        :class:`FSLViewPanel` when it is to be closed/destroyed. It seems to
        be impossible to define a single handler (on either the
        :attr:`wx.EVT_CLOSE` and/or :attr:`wx.EVT_WINDOW_DESTROY` events)
        which handles both cases where the window is destroyed (in the
        process of destroying a parent window), and where the window is
        explicitly closed by the user (e.g. when embedded as a page in
        a Notebook). 

        This issue is probably caused by my use of the AUI framework for
        layout management, as the AUI manager/notebook classes do not seem to
        call close/destroy in all cases. Everything that I've tried, which
        relies upon EVT_CLOSE/EVT_WINDOW_DESTROY events, inevitably results in
        the event handlers not being called, or in segmentation faults
        (presumably due to double-frees at the C++ level).

        Subclasses which need to perform any cleaning up when they are closed
        may override this method, and should be able to assume that it will be
        called. So this method *must* be called by managing code when a panel
        is deleted.

        Overriding subclass implementations must call this base class
        method, otherwise memory leaks will probably occur, and warnings will
        probably be output to the log (see :meth:`__del__`).
        """
        self.__destroyed = True

    
    def __del__(self):
        """Sub-classes which implement ``__del__`` must call this
        implementation, otherwise memory leaks will occur.
        """
        actions.ActionProvider.__del__(self)

        self._overlayList = None
        self._displayCtx  = None

        if not self.__destroyed:
            log.warning('The {}.destroy() method has not been called '
                        '- unless the application is shutting down, '
                        'this is probably a bug!'.format(type(self).__name__))


class FSLViewPanel(_FSLViewPanel, wx.Panel):
    """
    """

    
    def __init__(self, parent, overlayList, displayCtx, actionz=None):
        wx.Panel.__init__(self, parent)
        _FSLViewPanel.__init__(self, overlayList, displayCtx, actionz)

        
    def __del__(self):
        wx.Panel     .__del__(self)
        _FSLViewPanel.__del__(self)
