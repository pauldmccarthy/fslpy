#!/usr/bin/env python
#
# async.py - Run a function in a separate thread.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions for running tasks asynchronously.


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

The :func:`wait` function is given one or more ``Thread`` instances, and a
task to run. It waits until all the threads have finished, and then runs
the task (via :func:`idle`).
"""


import time
import Queue
import logging
import threading
import collections


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

    :returns: A reference to the ``Thread`` that was created.

    .. note:: If a ``wx`` application is not running, the ``task`` and
              ``onFinish`` functions will simply be called directly, and
             the return value will be ``None``.
    """

    if name is None:
        name = getattr(task, '__name__', '<unknown>')

    haveWX = _haveWX()

    def wrapper():

        log.debug('Running task "{}"...'.format(name))
        task()

        log.debug('Task "{}" finished'.format(name))

        if (onFinish is not None):

            import wx

            log.debug('Scheduling task "{}" finish handler '
                      'on wx.MainLoop'.format(name))

            # Should I use the idle function here?
            wx.CallAfter(onFinish)

    if haveWX:
        thread = threading.Thread(target=wrapper)
        thread.start()
        return thread
 
    else:
        log.debug('Running task "{}" directly'.format(name)) 
        task()
        log.debug('Running task "{}" finish handler'.format(name)) 
        onFinish()
        return None


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

    try:
        task, schedtime, timeout, args, kwargs = _idleQueue.get_nowait()
    except Queue.Empty:
        return

    name    = getattr(task, '__name__', '<unknown>')
    now     = time.time()
    elapsed = now - schedtime

    if timeout == 0 or (elapsed < timeout):
        log.debug('Running function ({}) on wx idle loop'.format(name))
        task(*args, **kwargs)

    if _idleQueue.qsize() > 0:
        ev.RequestMore()
    

def idle(task, *args, **kwargs):
    """Run the given task on a ``wx.EVT_IDLE`` event.

    :arg task: The task to run.

    :arg timeout: Optional. If provided, must be provided as a keyword
                  argument. Specifies a time out, in seconds. If this
                  amount of time passes before the function gets
                  scheduled to be called on the idle loop, the function
                  is not called, and is dropped from the queue.

    All other arguments are passed through to the task function.

    If a ``wx.App`` is not running, the task is called directly.
    """

    global _idleRegistered
    global _idleTasks

    schedtime = time.time()
    timeout   = kwargs.pop('timeout', 0)

    if _haveWX():
        import wx

        if not _idleRegistered:
            wx.GetApp().Bind(wx.EVT_IDLE, _wxIdleLoop)
            _idleRegistered = True

        name = getattr(task, '__name__', '<unknown>')
        log.debug('Scheduling idle task ({}) on wx idle loop'.format(name))

        _idleQueue.put_nowait((task, schedtime, timeout, args, kwargs))
            
    else:
        log.debug('Running idle task directly') 
        task(*args, **kwargs)


def wait(threads, task, *args, **kwargs):
    """Creates and starts a new ``Thread`` which waits for all of the ``Thread``
    instances to finsih (by ``join``ing them), and then runs the given
    ``task`` via :func:`idle`.

    If a ``wx.App`` is not running, this function ``join``s the threads
    directly instead of creating a new ``Thread`` to do so.

    :arg threads: A ``Thread``, or a sequence of ``Thread`` instances to
                  join. Elements in the sequence may be ``None``.

    :arg task:    The task to run.

    All other arguments are passed to the ``task`` function.
    """

    if not isinstance(threads, collections.Sequence):
        threads = [threads]
    
    haveWX = _haveWX()

    def joinAll():
        log.debug('Wait thread joining on all targets')
        for t in threads:
            if t is not None:
                t.join()

        log.debug('Wait thread scheduling task on idle loop')
        idle(task, *args, **kwargs)

    if haveWX:
        thread = threading.Thread(target=joinAll)
        thread.start()
        return thread
    
    else:
        joinAll()
        return None
