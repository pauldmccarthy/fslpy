#!/usr/bin/env python
#
# async.py - Run a function in a separate thread.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides a couple of functions for running tasks
asynchronously - :func:`run` and :func:`idle`.


.. note:: The functions in this module are intended to be run from within a
          ``wx`` application. However, they will still work without ``wx``,
          albeit with slightly modified behaviour.


The :func:`run` function simply runs a task in a separate thread.  This
doesn't seem like a worthy task to have a function of its own, but the
:func:`run` function additionally provides the ability to schedule another
function to run on the ``wx.MainLoop`` when the original function has
completed.  This therefore gives us a simple way to run a computationally
intensitve task off the main GUI thread (preventing the GUI from locking up),
and to perform some clean up/refresh afterwards.


The :func:`idle` function is a simple way to run a task on an ``wx``
``EVT_IDLE`` event handler. This effectively performs the same job as the
:func:`run` function, but is more suitable for short tasks which do not
warrant running in a separate thread.
"""

import Queue
import logging
import threading


log = logging.getLogger(__name__)


def _haveWX():
    """Returns ``True`` if wqe are running within a ``wx`` application,
    ``False`` otherwise.
    """
    
    try:
        import wx
        return wx.GetApp() is not None
    
    except ImportError:
        return False


def run(task, onFinish=None, name=None):
    """Run the given ``task`` in a separate thread.

    :arg task:     The function to run. Must accept no arguments.

    :arg onFinish: An optional function to schedule on the ``wx.MainLoop``
                   once the ``task`` has finished. 

    :arg name:     An optional name to use for this task in log statements.

    .. note:: If a ``wx`` application is not running, the ``onFinish``
              function is called directly from the task thread.
    """

    if name is None:
        name = 'async task'

    def wrapper():

        log.debug('Running task "{}"...'.format(name))
        task()

        log.debug('Task "{}" finished'.format(name))

        if onFinish is not None:

            if _haveWX():
                import wx

                log.debug('Scheduling task "{}" finish handler '
                          'on wx.MainLoop'.format(name))

                wx.CallAfter(onFinish)
            else:
                log.debug('Running task "{}" finish handler'.format(name)) 
                onFinish()
                

    thread = threading.Thread(target=wrapper)
    thread.start()

    return thread


_idleRegistered = False
"""Boolean flag indicating whether the :func:`wxIdleLoop` function has
been registered as a ``wx.EVT_IDLE`` event handler. Checked and set
in the :func:`idle` function.
"""


_idleQueue = Queue.Queue()
"""A ``Queue`` of functions which are to be run on the ``wx.EVT_IDLE``
loop.
"""


def _wxIdleLoop(ev):
    """Function which is called on ``wx.EVT_IDLE`` events. If there
    is a function on the :attr:`_idleQueue`, it is popped and called.
    """
        
    ev.Skip()

    try:                task, args, kwargs = _idleQueue.get_nowait()
    except Queue.Empty: return
        
    task(*args, **kwargs)

    if _idleQueue.qsize() > 0:
        ev.RequestMore()
    

def idle(task, *args, **kwargs):
    """Run the given task on a ``wx.EVT_IDLE`` event.

    :arg task: The task to run.

    All other arguments are passed through to the task function.
    """

    global _idleRegistered
    global _idleTasks

    if _haveWX():
        import wx

        if not _idleRegistered:
            wx.GetApp().Bind(wx.EVT_IDLE, _wxIdleLoop)
            _idleRegistered = True

        log.debug('Scheduling idle task on wx idle loop')

        _idleQueue.put_nowait((task, args, kwargs))
            
    else:
        log.debug('Running idle task directly') 
        task(*args, **kwargs)
