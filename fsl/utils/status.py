#!/usr/bin/env python
#
# status.py - A simple interface for displaying messages.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This is a little module which provides an interface for displaying a
message, or status update, to the user.  The ``status`` module provides the
following functions:

 .. autosummary::
    :nosignatures:

    setTarget
    update
    clearStatus


The :func:`update` function may be used to display a message. By default, the
message is simply logged (via the ``logging`` module). However, if a status
target has been set via the :func:`setTarget` function, the message is also
passed to this target. 
"""


import            threading
import            logging
import            inspect
import os.path as op


log = logging.getLogger(__name__)


_statusUpdateTarget = None
"""A reference to the status update target - this is ``None`` by default, and
can be set via :func:`setTarget`.
"""


_clearThread = None
"""Reference to a :class:`ClearThread`, which is a daemon thread that clears
the status after the timeout passed to the :func:`update` function. 
"""


def setTarget(target):
    """Set a target function to receive status updates. The ``target`` must
    be a function which accepts a string as its sole parameter.
    """
    global _statusUpdateTarget
    _statusUpdateTarget = target


def update(message, timeout=1.0):
    """Display a status update to the user. The message is logged and,
    if a status update target has been set, passed to the target.

    :arg timeout: Timeout (in seconds) after which the status will be
                  cleared (via the :class:`ClearThread`). Pass in ``None``
                  to disable this behaviour.
    """

    global _clearThread
    global _statusUpdateTarget

    if log.getEffectiveLevel() == logging.DEBUG:
        
        frame   = inspect.stack()[1]
        module  = frame[1]
        linenum = frame[2]
        module  = op.basename(module)

        log.debug('[{}:{}] {}'.format(module, linenum, message))

    if _statusUpdateTarget is None:
        return

    _statusUpdateTarget(message)

    if timeout is not None:
        
        if _clearThread is None:
            _clearThread = ClearThread()
            _clearThread.start()

        _clearThread.clear(timeout)


def clearStatus():
    """Clear the status. If a status update target has been set, it is passed
    the empty string.
    """ 
    if _statusUpdateTarget is None:
        return
        
    _statusUpdateTarget('') 

    
class ClearThread(threading.Thread):
    """The ``ClearThread`` is a daemon thread used by the :func:`update`
    function. Only one ``ClearThread`` is ever started - it is started on the
    first call to ``update`` when a timeout is specified.

    The ``ClearThread`` waits until the :meth:`clear` method is called.
    It then waits for the specified timeout and, unless another call to
    :meth:`clear` has been made, clears the status via a call to
    :func:`clearStatus`.

    Apologies for the confusing naming.
    """

    
    def __init__(self):
        """Create a ``ClearThread``. """

        threading.Thread.__init__(self)

        self.daemon       = True
        self.__clearEvent = threading.Event()
        self.__timeout    = None

        
    def clear(self, timeout):
        """Clear the status after the specified timeout (in seconds). """
        
        self.__timeout = timeout
        self.__clearEvent.set()

        
    def run(self):
        """The ``ClearThread`` function. Infinite loop which waits until
        the :meth:`clear` method is called, and then clears the status
        (via a call to :func:`clearStatus`).
        """

        while True:

            self.__clearEvent.wait()
            self.__clearEvent.clear()

            if not self.__clearEvent.wait(self.__timeout):
                clearStatus()
