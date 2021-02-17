#!/usr/bin/env python
#
# idle.py - Run functions on an idle loop or in a separate thread.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions and classes for running tasks
asynchronously, either in an idle loop, or on a separate thread.


.. note:: The :class:`IdleLoop` functionality in this module is intended to be
          run from within a ``wx`` application. However, it will still work
          without ``wx``, albeit with slightly modified behaviour.


Idle tasks
----------

.. autosummary::
   :nosignatures:

   IdleLoop
   idle
   idleWhen
   block


The :class:`IdleLoop` class provides a simple way to run a task on an ``wx``
``EVT_IDLE`` event handler. A single ``IdleLoop`` instance is created when
this module is imported; it can be accessed via the :attr:`idleLoop` attribute,
and via the module-level :func:`idle` and :func:`idleWhen` functions.

The :meth:`IdleLoop.idle` method effectively performs the same job as the
:func:`run` function (described below), but is more suitable for short tasks
which do not warrant running in a separate thread.


Thread tasks
------------

.. autosummary::
   :nosignatures:

   run
   wait
   TaskThread


The :func:`run` function simply runs a task in a separate thread.  This
doesn't seem like a worthy task to have a function of its own, but the
:func:`run` function additionally provides the ability to schedule another
function to run on the ``wx.MainLoop`` when the original function has
completed (via :func:`idle`). This therefore gives us a simple way to run a
computationally intensitve task off the main GUI thread (preventing the GUI
from locking up), and to perform some clean up/refresh/notification
afterwards.


The :func:`wait` function is given one or more ``Thread`` instances, and a
task to run. It waits until all the threads have finished, and then runs
the task (via :func:`idle`).


The :class:`TaskThread` class is a simple thread which runs a queue of tasks.


Other facilities
----------------


The ``idle`` module also defines the :func:`mutex` decorator, which is
intended to be used to mark the methods of a class as being mutually exclusive.
The ``mutex`` decorator uses the :class:`MutexFactory` class to do its work.
"""


import time
import atexit
import logging
import functools
import threading
from   contextlib  import contextmanager
from   collections import abc

try:                import queue
except ImportError: import Queue as queue


log = logging.getLogger(__name__)


@functools.lru_cache()
def _canHaveGui():
    """Return ``True`` if wxPython is installed, and a display is available,
    ``False`` otherwise.
    """
    # Determine if a display is available. We do
    # this once at init (instead of on-demand in
    # the canHaveGui method) because calling the
    # IsDisplayAvailable function will cause the
    # application to steal focus under OSX!
    try:
        import wx
        return wx.App.IsDisplayAvailable()
    except ImportError:
        return False


def _haveGui():
    """Return ``True`` if wxPython is installed, a display is available, and
    a ``wx.App`` exists, ``False`` otherwise.
    """
    try:
        import wx
        return _canHaveGui() and (wx.GetApp() is not None)
    except ImportError:
        return False


class IdleTask:
    """Container object used by the :class:`IdleLoop` class.
    Used to encapsulate information about a queued task.
    """

    def __init__(self,
                 name,
                 task,
                 schedtime,
                 after,
                 timeout,
                 args,
                 kwargs):
        self.name      = name
        self.task      = task
        self.schedtime = schedtime
        self.after     = after
        self.timeout   = timeout
        self.args      = args
        self.kwargs    = kwargs


class IdleLoop:
    """This class contains logic for running tasks via ``wx.EVT_IDLE`` events.

    A single ``IdleLoop`` instance is created when this module is first
    imported - it is accessed via the module-level :attr:`idleLoop` attribute.

    In normal circumstances, this ``idleLoop`` instance should be treated as a
    singleton, although this is not enforced in any way.

    The ``EVT_IDLE`` event is generated automatically by ``wx`` during periods
    of inactivity. However, there are some circumstances in which ``EVT_IDLE``
    will not be generated, and pending events may be left on the queue. For
    this reason, the ``IdleLoop`` will occasionally use a ``wx.Timer`` to
    ensure that it continues to be called. The time-out used by this ``Timer``
    can be queried and set via the :meth:`callRate` property.
    """

    def __init__(self):
        """Create an ``IdleLoop``.

        This method does not do much - the real initialisation takes place
        on the first call to :meth:`idle`.
        """
        self.__registered  = False
        self.__queue       = queue.Queue()
        self.__queueDict   = {}
        self.__timer       = None
        self.__callRate    = 200
        self.__allowErrors = False
        self.__neverQueue  = False

        # Call reset on exit, in case
        # the idle.timer is active.
        atexit.register(self.reset)


    @property
    def registered(self):
        """Boolean flag indicating whether a handler has been registered on
        ``wx.EVT_IDLE`` events. Checked and set in the :meth:`idle` method.
        """
        return self.__registered


    @property
    def queue(self):
        """A ``Queue`` of functions which are to be run on the ``wx.EVT_IDLE``
        loop.
        """
        return self.__queue


    @property
    def queueDict(self):
        """A ``dict`` containing the names of all named tasks which are
        currently queued on the idle loop (see the ``name`` parameter to the
        :meth:`idle` method).
        """
        return self.__queueDict


    @property
    def timer(self):
        """A ``wx.Timer`` instance which is used to periodically trigger the
        :func:`_wxIdleLoop` in circumstances where ``wx.EVT_IDLE`` events may
        not be generated. This is created in the first call to :meth:`idle`.
        """
        return self.__timer


    @property
    def callRate(self):
        """Minimum time (in milliseconds) between consecutive calls to the idle
        loop (:meth:`__idleLoop`). If ``wx.EVT_IDLE`` events are not being
        fired, the :meth:`timer` is used to maintain the idle loop at this
        rate.
        """
        return self.__callRate


    @callRate.setter
    def callRate(self, rate):
        """Update the :meth:`callRate` to ``rate`` (specified in milliseconds).

        If ``rate is None``, it is set to the default of 200 milliseconds.
        """

        if rate is None:
            rate = 200

        log.debug('Idle loop timeout changed to {}'.format(rate))

        self.__callRate = rate


    @property
    def allowErrors(self):
        """Used for testing/debugging. If ``True``, and a function called on
        the idle loop raises an error, that error will not be caught, and the
        idle loop will stop.
        """
        return self.__allowErrors


    @allowErrors.setter
    def allowErrors(self, allow):
        """Update the ``allowErrors`` flag. """
        self.__allowErrors = allow


    @property
    def neverQueue(self):
        """If ``True``, tasks passed to :meth:`idle` will never be queued, and
        instead will always be executed directly/synchonously. See also the
        :meth:`synchronous` context manager.
        """
        return self.__neverQueue


    @neverQueue.setter
    def neverQueue(self, val):
        """Update the ``neverQueue`` flag. """
        self.__neverQueue = val


    @contextmanager
    def synchronous(self):
        """Context manager which can be used to tenporarily set :meth:`neverQueue` to
        ``True``, restoring its previous value afterwards.
        """

        oldval = self.__neverQueue
        self.__neverQueue = True

        try:
            yield
        finally:
            self.__neverQueue = oldval


    def reset(self):
        """Reset the internal idle loop state.

        In a normal execution environment, this method will never need to be
        called.  However, in an execution environment where multiple ``wx.App``
        instances are created, run, and destroyed sequentially, this function
        will need to be called after each ``wx.App`` has been destroyed.
        Otherwise the ``idle`` function will not work during exeution of
        subsequent ``wx.App`` instances.
        """

        if self.__timer is not None:
            self.__timer.Stop()

        # If we're atexit, the ref to
        # the queue module might have
        # been cleared, in which case
        # we don't want to create a
        # new one.
        if self.__queue is not None: newQueue = queue.Queue()
        else:                        newQueue = None

        self.__registered  = False
        self.__queue       = newQueue
        self.__queueDict   = {}
        self.__timer       = None
        self.__callRate    = 200
        self.__allowErrors = False
        self.__neverQueue  = False


    def inIdle(self, taskName):
        """Returns ``True`` if a task with the given name is queued on the
        idle loop (or is currently running), ``False`` otherwise.
        """
        return taskName in self.__queueDict


    def cancelIdle(self, taskName):
        """If a task with the given ``taskName`` is in the idle queue, it
        is cancelled. If the task is already running, it cannot be cancelled.

        A ``KeyError`` is raised if no task called ``taskName`` exists.
        """
        self.__queueDict[taskName].timeout = -1


    def idle(self, task, *args, **kwargs):
        """Run the given task on a ``wx.EVT_IDLE`` event.

        :arg task:         The task to run.

        :arg name:         Optional. If provided, must be provided as a keyword
                           argument. Specifies a name that can be used to
                           query the state of this task via :meth:`inIdle`.

        :arg after:        Optional. If provided, must be provided as a keyword
                           argument. A time, in seconds, which specifies the
                           amount of time to wait before running this task
                           after it has been scheduled.

        :arg timeout:      Optional. If provided, must be provided as a keyword
                           argument. Specifies a time out, in seconds. If this
                           amount of time passes before the function gets
                           scheduled to be called on the idle loop, the
                           function is not called, and is dropped from the
                           queue.

        :arg dropIfQueued: Optional. If provided, must be provided as a keyword
                           argument. If ``True``, and a task with the given
                           ``name`` is already enqueud, that function is
                           dropped from the queue, and the new task is
                           enqueued. Defaults to ``False``. This argument takes
                           precedence over the ``skipIfQueued`` argument.

        :arg skipIfQueued: Optional. If provided, must be provided as a keyword
                           argument. If ``True``, and a task with the given
                           ``name`` is already enqueud, (or is running), the
                           function is not called. Defaults to ``False``.

        :arg alwaysQueue:  Optional. If provided, must be provided as a keyword
                           argument. If ``True``, and a ``wx.MainLoop`` is not
                           running, the task is enqueued anyway, under the
                           assumption that a ``wx.MainLoop`` will be started in
                           the future. Note that, if ``wx.App`` has not yet
                           been created, another  call to ``idle`` must be made
                           after the app has been created for the original task
                           to be executed. If ``wx`` is not available, this
                           parameter will be ignored, and the task executed
                           directly.


        All other arguments are passed through to the task function.


        If a ``wx.App`` is not running, or :meth:`neverQueue` has been set to
        ``True``, the ``timeout``, ``name``, ``dropIfQueued``,
        ``skipIfQueued``, and ``alwaysQueue`` arguments are ignored. Instead,
        the call will sleep for ``after`` seconds, and then the ``task`` will
        be called directly.


        .. note:: If the ``after`` argument is used, there is no guarantee that
                  the task will be executed in the order that it is scheduled.
                  This is because, if the required time has not elapsed when
                  the task is popped from the queue, it will be re-queued.

        .. note:: If you schedule multiple tasks with the same ``name``, and
                  you do not use the ``skipIfQueued`` or ``dropIfQueued``
                  arguments, all of those tasks will be executed, but you will
                  only be able to query/cancel the most recently enqueued
                  task.

        .. note:: You will run into difficulties if you schedule a function
                  that expects/accepts its own keyword arguments called
                  ``name``, ``skipIfQueued``, ``dropIfQueued``, ``after``,
                  ``timeout``, or ``alwaysQueue``.
        """

        schedtime    = time.time()
        timeout      = kwargs.pop('timeout',      0)
        after        = kwargs.pop('after',        0)
        name         = kwargs.pop('name',         None)
        dropIfQueued = kwargs.pop('dropIfQueued', False)
        skipIfQueued = kwargs.pop('skipIfQueued', False)
        alwaysQueue  = kwargs.pop('alwaysQueue',  False)

        # If there is no possibility of a
        # gui being available in the future
        # (determined by _canHaveGui), then
        # alwaysQueue is ignored.
        alwaysQueue = alwaysQueue and _canHaveGui()

        # We don't have wx - run the task
        # directly/synchronously.
        if self.__neverQueue or not (_haveGui() or alwaysQueue):
            time.sleep(after)
            log.debug('Running idle task directly')
            task(*args, **kwargs)
            return

        import wx
        app = wx.GetApp()

        # Register on the idle event
        # if an app is available
        #
        # n.b. The 'app is not None' test will
        # potentially fail in scenarios where
        # multiple wx.Apps have been instantiated,
        # as it may return a previously created
        # app that is no longer active.
        if (not self.registered) and (app is not None):

            log.debug('Registering async idle loop')
            app.Bind(wx.EVT_IDLE, self.__idleLoop)

            # We also occasionally use a
            # timer to drive the loop, so
            # let's register that as well
            self.__timer = wx.Timer(app)
            self.__timer.Bind(wx.EVT_TIMER, self.__idleLoop)
            self.__registered = True

        # A task with the specified
        # name is already in the queue
        if name is not None and self.inIdle(name):

            # Drop the old task
            # with the same name
            if dropIfQueued:

                # The cancelIdle function sets the old
                # task timeout to -1, so it won't get
                # executed. But the task is left in the
                # queue, and in the queueDict.
                # In the latter, the old task gets
                # overwritten with the new task below.
                self.cancelIdle(name)
                log.debug('Idle task ({}) is already queued - '
                          'dropping the old task'.format(name))

            # Ignore the new task
            # with the same name
            elif skipIfQueued:
                log.debug('Idle task ({}) is already queued '
                          '- skipping it'.format(name))
                return

        log.debug('Scheduling idle task ({}) on wx idle '
                  'loop'.format(getattr(task, '__name__', '<unknown>')))

        idleTask = IdleTask(name,
                            task,
                            schedtime,
                            after,
                            timeout,
                            args,
                            kwargs)

        self.__queue.put_nowait(idleTask)

        if name is not None:
            self.__queueDict[name] = idleTask


    def idleWhen(self, func, condition, *args, **kwargs):
        """Poll the ``condition`` function periodically, and schedule ``func``
        on :meth:`idle` when it returns ``True``.

        :arg func:      Function to call.

        :arg condition: Function which returns ``True`` or ``False``. The
                        ``func`` function is only called when the
                        ``condition`` function returns ``True``.

        :arg pollTime:  Must be passed as a keyword argument. Time (in seconds)
                        to wait between successive calls to ``when``. Defaults
                        to ``0.2``.
        """

        pollTime = kwargs.get('pollTime', 0.2)

        if not condition():
            self.idle(self.idleWhen,
                      func,
                      condition,
                      after=pollTime,
                      *args,
                      **dict(kwargs))
        else:
            kwargs.pop('pollTime', None)
            self.idle(func, *args, **kwargs)


    def __idleLoop(self, ev):
        """This method is called on ``wx.EVT_IDLE`` events, and occasionally
        on ``wx.EVT_TIMER`` events via the :meth:`timer`. If there
        is a function on the :meth:`queue`, it is popped and called.

        .. note:: The ``wx.EVT_IDLE`` event is only triggered on user
                  interaction (e.g. mouse movement). This means that a
                  situation may arise whereby a function is queued via the
                  :meth:`idle` method, but no ``EVT_IDLE`` event gets
                  generated. Therefore, the :meth:`timer` object is
                  occasionally used to call this function as well.
        """

        import wx

        ev.Skip()

        try:
            task = self.__queue.get_nowait()

        except queue.Empty:

            # Make sure that we get called periodically,
            # if EVT_IDLE decides to stop firing. If
            # self.timer is None, then self.reset has
            # probably been called.
            if self.__timer is not None:
                self.__timer.Start(self.__callRate, wx.TIMER_ONE_SHOT)
            return

        now             = time.time()
        elapsed         = now - task.schedtime
        queueSizeOffset = 0
        taskName        = task.name
        funcName        = getattr(task.task, '__name__', '<unknown>')

        if taskName is None: taskName = funcName
        else:                taskName = '{} [{}]'.format(taskName, funcName)

        # Has enough time elapsed
        # since the task was scheduled?
        # If not, re-queue the task.
        # If this is the only task on the
        # queue, the idle loop will be
        # called again after
        # callRate millisecs.
        if elapsed < task.after:
            log.debug('Re-queueing function ({}) on '
                      'wx idle loop'.format(taskName))
            self.__queue.put_nowait(task)
            queueSizeOffset = 1

        # Has the task timed out?
        elif task.timeout == 0 or (elapsed < task.timeout):

            log.debug('Running function ({}) on wx '
                      'idle loop'.format(taskName))

            try:
                task.task(*task.args, **task.kwargs)
            except Exception as e:
                log.warning('Idle task {} crashed - {}: {}'.format(
                    taskName, type(e).__name__, str(e)), exc_info=True)

                if self.__allowErrors:
                    raise e

            if task.name is not None:
                try:             self.__queueDict.pop(task.name)
                except KeyError: pass

        # More tasks on the queue?
        # Request anotherd event
        if self.__queue.qsize() > queueSizeOffset:
            ev.RequestMore()

        # Otherwise use the idle
        # timer to make sure that
        # the loop keeps ticking
        # over
        else:
            self.__timer.Start(self.__callRate, wx.TIMER_ONE_SHOT)


idleLoop = IdleLoop()
"""A singleton :class:`IdleLoop` instance, created when this module is
imported.
"""


def idle(*args, **kwargs):
    """Equivalent to calling :meth:`IdleLoop.idle` on the ``idleLoop``
    singleton.
    """
    idleLoop.idle(*args, **kwargs)


def idleWhen(*args, **kwargs):
    """Equivalent to calling :meth:`IdleLoop.idleWhen` on the ``idleLoop``
    singleton.
    """
    idleLoop.idleWhen(*args, **kwargs)


def block(secs, delta=0.01, until=None):
    """Blocks for the specified number of seconds, yielding to the main ``wx``
    loop.

    If ``wx`` is not available, or a ``wx`` application is not running, this
    function is equivalent to ``time.sleep(secs)``.

    If ``until`` is provided, this function will block until ``until``
    returns ``True``, or ``secs`` have elapsed, whichever comes first.

    :arg secs:  Time in seconds to block
    :arg delta: Time in seconds to sleep between successive yields to ``wx``.
    :arg until: Function which returns ``True`` or ``False``, and which
                determins when calls to ``block`` will return.
    """

    havewx = _haveGui()

    def defaultUntil():
        return False

    def tick():
        if havewx:
            import wx
            wx.YieldIfNeeded()
        time.sleep(delta)

    if until is None:
        until = defaultUntil

    start = time.time()
    while (time.time() - start) < secs:
        tick()
        if until():
            break


def run(task, onFinish=None, onError=None, name=None):
    """Run the given ``task`` in a separate thread.

    :arg task:     The function to run. Must accept no arguments.

    :arg onFinish: An optional function to schedule (on the ``wx.MainLoop``,
                   via :func:`idle`) once the ``task`` has finished.

    :arg onError:  An optional function to be called (on the ``wx.MainLoop``,
                   via :func:`idle`) if the ``task`` raises an error. Passed
                   the ``Exception`` that was raised.

    :arg name:     An optional name to use for this task in log statements.

    :returns: A reference to the ``Thread`` that was created.

    .. note:: If a ``wx`` application is not running, the ``task`` and
              ``onFinish`` functions will simply be called directly, and
              the return value will be ``None``.
    """


    if name is None:
        name = getattr(task, '__name__', '<unknown>')

    haveWX = _haveGui()

    # Calls the onFinish or onError handler
    def callback(cb, *args, **kwargs):

        if cb is None:
            return

        if haveWX: idle(cb, *args, **kwargs)
        else:      cb(      *args, **kwargs)

    # Runs the task, and calls
    # callback functions as needed.
    def wrapper():

        try:
            task()
            log.debug('Task "{}" finished'.format(name))
            callback(onFinish)

        except Exception as e:

            log.warning('Task "{}" crashed'.format(name), exc_info=True)
            callback(onError, e)

    # If WX, run on a thread
    if haveWX:

        log.debug('Running task "{}" on thread'.format(name))

        thread = threading.Thread(target=wrapper)
        thread.start()
        return thread

    # Otherwise run directly
    else:
        log.debug('Running task "{}" directly'.format(name))
        wrapper()
        return None


def wait(threads, task, *args, **kwargs):
    """Creates and starts a new ``Thread`` which waits for all of the ``Thread``
    instances to finish (by ``join``ing them), and then runs the given
    ``task`` via :func:`idle`.

    If the ``direct`` parameter is ``True``, or a ``wx.App`` is not running,
    this function ``join``s the threads directly instead of creating a new
    ``Thread`` to do so.

    :arg threads:      A ``Thread``, or a sequence of ``Thread`` instances to
                       join. Elements in the sequence may be ``None``.

    :arg task:         The task to run once all ``threads`` have completed.

    :arg wait_direct:  Must be passed as a keyword argument.  If ``True``, this
                       function call will ``join`` all of the ``threads``, and
                       then call the ``task``. Otherwise (the default), this
                       function will create a new thread to ``join`` the
                       ``threads``, and will return immediately.


    All other arguments are passed to the ``task`` function.


    .. note:: This function will not support ``task`` functions which expect
              a keyword argument called ``wait_direct``.
    """

    direct = kwargs.pop('wait_direct', False)

    if not isinstance(threads, abc.Sequence):
        threads = [threads]

    haveWX = _haveGui()

    def joinAll():
        log.debug('Wait thread joining on all targets')
        for t in threads:
            if t is not None:
                t.join()

        log.debug('Wait thread scheduling task on idle loop')
        idle(task, *args, **kwargs)

    if haveWX and not direct:
        thread = threading.Thread(target=joinAll)
        thread.start()
        return thread

    else:
        joinAll()
        return None


class Task:
    """Container object which encapsulates a task that is run by a
    :class:`TaskThread`.
    """
    def __init__(self, name, func, onFinish, onError, args, kwargs):
        self.name     = name
        self.func     = func
        self.onFinish = onFinish
        self.onError  = onError
        self.args     = args
        self.kwargs   = kwargs
        self.enabled  = True


class TaskThreadVeto(Exception):
    """Task functions which are added to a :class:`TaskThread` may raise
    a ``TaskThreadVeto`` error to skip processing of the task's ``onFinish``
    handler (if one has been specified). See the :meth:`TaskThread.enqueue`
    method for more details.
    """


class TaskThread(threading.Thread):
    """The ``TaskThread`` is a simple thread which runs tasks. Tasks may be
    enqueued and dequeued.
    """


    def __init__(self, *args, **kwargs):
        """Create a ``TaskThread``. """

        threading.Thread.__init__(self, *args, **kwargs)

        self.__q        = queue.Queue()
        self.__enqueued = {}
        self.__stop     = False

        log.debug('New task thread')


    def enqueue(self, func, *args, **kwargs):
        """Enqueue a task to be executed.

        :arg func:     The task function.

        :arg taskName: Task name. Must be specified as a keyword
                       argument. Does not necessarily have to be a string, but
                       must be hashable. If you wish to use the :meth:`dequeue`
                       or :meth:`isQueued` methods, you must provide a task
                       name.

        :arg onFinish: An optional function to be called (via :func:`idle`)
                       when the task funtion has finished. Must be provided as
                       a keyword argument, and must itself accept no arguments.
                       If the ``func`` raises a :class`TaskThreadVeto` error,
                       this function will not be called.

        :arg onError:  An optional function to be called (via :func:`idle`)
                       if the task funtion raises an ``Exception``. Must be
                       provided as a keyword argument, and must itself accept
                       the raised ``Exception`` object as a single argument.
                       If the ``func`` raises a :class`TaskThreadVeto` error,
                       this function will not be called.

        All other arguments are passed through to the task function when it is
        executed.

        .. note:: If the specified ``taskName`` is not unique (i.e. another
                  task with the same name may already be enqueued), the
                  :meth:`isQueued` method will probably return invalid
                  results.

        .. warning:: Make sure that your task function is not expecting keyword
                     arguments called ``taskName``, ``onFinish``, or
                     ``onError``!
        """

        name     = kwargs.pop('taskName', None)
        onFinish = kwargs.pop('onFinish', None)
        onError  = kwargs.pop('onError',  None)

        log.debug('Enqueueing task: {} [{}]'.format(
            name, getattr(func, '__name__', '<unknown>')))

        t = Task(name, func, onFinish, onError, args, kwargs)
        self.__enqueued[name] = t
        self.__q.put(t)


    def isQueued(self, name):
        """Returns ``True`` if a task with the given name is enqueued,
        ``False`` otherwise.
        """
        return name  in self.__enqueued


    def dequeue(self, name):
        """Dequeues a previously enqueued task.

        :arg name: The task to dequeue.
        """
        task = self.__enqueued.get(name, None)
        if task is not None:

            log.debug('Dequeueing task: {}'.format(name))
            task.enabled = False


    def stop(self):
        """Stop the ``TaskThread`` after any currently running task has
        completed.
        """
        log.debug('Stopping task thread')
        self.__stop = True


    def waitUntilIdle(self):
        """Causes the calling thread to block until the task queue is empty.
        """
        self.__q.join()


    def run(self):
        """Run the ``TaskThread``. """

        while True:

            try:
                # Clear ref to previous task if any. This
                # is very important, because otherwise, if
                # no tasks get posted to the queue, this
                # loop will spin on queue.Empty exceptions,
                # and the previous Task object will preserve
                # a hanging ref to its function/method. Not
                # ideal if the ref is to a method of the
                # object which created this TaskThread, and
                # needs to be GC'd!
                task = None

                # An example: Without clearing the task
                # reference, the following code would
                # result in the TaskThread spinning on empty
                # forever, and would prevent the Blah
                # instance from being GC'd:
                #
                #     class Blah(object):
                #         def __init__(self):
                #             tt = TaskThraed()
                #             tt.enqueue(self.method)
                #             tt.start()
                #
                #     def method(self):
                #         pass
                #
                #     b = Blah()
                #     del b
                task = self.__q.get(timeout=1)

            except queue.Empty:
                continue

            # Any other error typically indicates
            # that this is a daemon thread, and
            # the TaskThread object has been GC'd
            except Exception:
                break

            finally:
                if self.__stop:
                    break

            self.__enqueued.pop(task.name, None)

            if not task.enabled:
                self.__q.task_done()
                continue

            log.debug('Running task: {} [{}]'.format(
                task.name,
                getattr(task.func, '__name__', '<unknown>')))

            try:
                task.func(*task.args, **task.kwargs)

                if task.onFinish is not None:
                    idle(task.onFinish)

                log.debug('Task completed: {} [{}]'.format(
                    task.name,
                    getattr(task.func, '__name__', '<unknown>')))

            # If the task raises a TaskThreadVeto error,
            # we just have to skip the onFinish handler
            except TaskThreadVeto:
                log.debug('Task completed (vetoed onFinish): {} [{}]'.format(
                    task.name,
                    getattr(task.func, '__name__', '<unknown>')))

            except Exception as e:
                log.warning('Task crashed: {} [{}]: {}: {}'.format(
                    task.name,
                    getattr(task.func, '__name__', '<unknown>'),
                    type(e).__name__,
                    str(e)),
                    exc_info=True)
                if task.onError is not None:
                    idle(task.onError, e)

            finally:
                self.__q.task_done()

        self.__q        = None
        self.__enqueued = None
        log.debug('Task thread finished')


def mutex(*args, **kwargs):
    """Decorator for use on methods of a class, which makes the method
    call mutually exclusive.

    If you define a class which has one or more methods that must only
    be accessed by one thread at a time, you can use the ``mutex`` decorator
    to enforce this restriction. As a contrived example::


        class Example(object):

            def __init__(self):
                self.__sharedData = []

            @mutex
            def dangerousMethod1(self, message):
                sefl.__sharedData.append(message)

            @mutex
            def dangerousMethod2(self):
                return sefl.__sharedData.pop()



    The ``@mutex`` decorator will ensure that, at any point in time, only
    one thread is running either of the ``dangerousMethod1`` or
    ``dangerousMethod2`` methods.

    See the :class:`MutexFactory``
    """
    return MutexFactory(*args, **kwargs)


class MutexFactory:
    """The ``MutexFactory`` is a placeholder for methods which have been
    decorated with the :func:`mutex` decorator. When the method of a class
    is decorated with ``@mutex``, a ``MutexFactory`` is created.

    Later on, when the method is accessed on an instance, the :meth:`__get__`
    method creates the true decorator function, and replaces the instance
    method with that decorator.

    .. note:: The ``MutexFactory`` adds an attribute called
              ``_async_mutex_lock`` to all instances that have
              ``@mutex``-decorated methods.
    """


    createLock = threading.Lock()
    """This lock is used by all ``MutexFactory`` instances when a decorated
    instance method is accessed for the first time.

    The first time that a mutexed method is accessed on an instance, a new
    ``threading.Lock`` is created, to be shared by all mutexed methods of that
    instance. The ``createLock`` is used to ensure that this can only occur
    once for each instance.
    """


    def __init__(self, function):
        """Create a ``MutexFactory``.
        """
        self.__func = function


    def __get__(self, instance, cls):
        """When this ``MutexFactory`` is accessed through an instance,
        a decorator function is created which enforces mutually exclusive
        access to the decorated method. A single ``threading.Lock`` object
        is shared between all ``@mutex``-decorated methods on a single
        instance.

        If this ``MutexFactory`` is accessed through a class, the
        decorated function is returned.
        """

        # Class-level access
        if instance is None:
            return self.__func

        # Get the lock object, creating if it necessary.
        # We use the createLock in case multiple threads
        # access a method at the same time, in which case
        # only one of them will be able to create the
        # instance lock.
        with MutexFactory.createLock:

            lock = getattr(instance, '_idle_mutex_lock', None)
            if lock is None:
                lock                      = threading.Lock()
                instance._idle_mutex_lock = lock

            # The true decorator function
            def decorator(*args, **kwargs):
                with instance._idle_mutex_lock:
                    return self.__func(instance, *args, **kwargs)

            # Replace this MutexFactory with
            # the decorator on the instance
            decorator = functools.update_wrapper(decorator, self.__func)
            setattr(instance, self.__func.__name__, decorator)
            return decorator
