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

A couple of other functions are also provided, for reporting error messages
to the user:

 .. autosummary::
    :nosignatures:

    reportError
    reportIfError
    reportErrorDecorator


The :func:`update` function may be used to display a message. By default, the
message is simply logged (via the ``logging`` module). However, if a status
target has been set via the :func:`setTarget` function, the message is also
passed to this target.


.. warning:: If the status update target is a ``wx`` GUI object, you must
             make sure that it is updated asynchronously (e.g. via
             ``wx.CallAfter``). 
"""


import            threading
import            contextlib
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


    .. note:: The ``timeout`` method only makes sense to use if the status
              target is a GUI widget of some sort.
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
        log.debug('timeout is not None - starting clear thread')
        
        if _clearThread is None:
            _clearThread = ClearThread()
            _clearThread.start()

        _clearThread.clear(timeout)
    else:
        if _clearThread is not None:
            _clearThread.veto()
            log.debug('No timeout - vetoing clear thread')


def clearStatus():
    """Clear the status. If a status update target has been set, it is passed
    the empty string.
    """ 
    if _statusUpdateTarget is None:
        return
        
    _statusUpdateTarget('')


def reportError(title, msg, err):
    """Reports an error to the user in a generic manner. If a GUI is available,
    (see the :meth.`.Platform.haveGui` attribute), a ``wx.MessageBox`` is
    shown. Otherwise a log message is generated.
    """

    from .platform import platform as fslplatform
    from .         import async

    if fslplatform.haveGui:
        msg = '{}\n\nDetails: {}'.format(msg, str(err))
        
        import wx
        async.idle(wx.MessageBox, msg, title, wx.ICON_ERROR | wx.OK)
    

@contextlib.contextmanager
def reportIfError(title, msg, raiseError=True, report=True):
    """A context manager which calls :func:`reportError` if the enclosed code
    raises an ``Exception``.

    :arg raiseError: If ``True``, the ``Exception`` which was raised is
                     propagated upwards.

    :arg report:     Defaults to ``True``. If ``False``, an error message
                     is logged, but :func:`reportError` is not called.
    """
    try:
        yield
        
    except Exception as e:

        log.error('{}: {}'.format(title, msg), exc_info=True)

        if report:
            reportError(title, msg, e)

        if raiseError:
            raise


def reportErrorDecorator(*args, **kwargs):
    """A decorator which wraps the decorated function with
    :func:`reportIfError`.
    """ 

    def decorator(func):
        def wrapper(*wargs, **wkwargs):
            with reportIfError(*args, **kwargs):
                func(*wargs, **wkwargs)

        return wrapper

    return decorator

    
class ClearThread(threading.Thread):
    """The ``ClearThread`` is a daemon thread used by the :func:`update`
    function. Only one ``ClearThread`` is ever started - it is started on the
    first call to ``update`` when a timeout is specified.

    The ``ClearThread`` waits until the :meth:`clear` method is called.
    It then waits for the specified timeout and, unless another call to
    :meth:`clear`, or a call to :meth:`veto` has been made, clears the
    status via a call to :func:`clearStatus`.
    """

    
    def __init__(self):
        """Create a ``ClearThread``. """

        threading.Thread.__init__(self)

        self.daemon       = True
        self.__clearEvent = threading.Event()
        self.__vetoEvent  = threading.Event()
        self.__timeout    = None

        
    def clear(self, timeout):
        """Clear the status after the specified timeout (in seconds). """
        
        self.__timeout = timeout
        self.__vetoEvent .clear()
        self.__clearEvent.set()


    def veto(self):
        """If this ``ClearThread`` is waiting on a timeout to clear
        the status, a call to ``veto`` will prevent it from doing so.
        """
        self.__vetoEvent.set()

        
    def run(self):
        """The ``ClearThread`` function. Infinite loop which waits until
        the :meth:`clear` method is called, and then clears the status
        (via a call to :func:`clearStatus`).
        """

        while True:

            self.__vetoEvent .clear()
            self.__clearEvent.wait()
            self.__clearEvent.clear()

            # http://bugs.python.org/issue14623
            #
            # When the main thread exits, daemon threads will
            # continue to run after the threading module is
            # destroyed. Calls to the Event methods can thus
            # result in errors.
            try:
                if not self.__clearEvent.wait(self.__timeout) and \
                   not self.__vetoEvent.isSet():

                    log.debug('Timeout - clearing status')
                    clearStatus()
                    
            except TypeError:
                return
