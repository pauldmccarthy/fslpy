#!/usr/bin/env python
#
# async.py - Run a function in a separate thread.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions and classes for running tasks
asynchronously, either in an idle loop, or on a separate thread.


.. note:: The *idle* functions in this module are intended to be run from
          within a ``wx`` application. However, they will still work without
          ``wx``, albeit with slightly modified behaviour.


Idle tasks
----------

.. autosummary::
   :nosignatures:

   idle
   idleWhen
   inIdle
   cancelIdle
   idleReset
   getIdleTimeout
   setIdleTimeout


The :func:`idle` function is a simple way to run a task on an ``wx``
``EVT_IDLE`` event handler. This effectively performs the same job as the
:func:`run` function, but is more suitable for short tasks which do not
warrant running in a separate thread.


The ``EVT_IDLE`` event is generated automatically by ``wx``. However, there
are some circumstances in which ``EVT_IDLE`` will not be generated, and
pending events may be left on the queue. For this reason, the
:func:`_wxIdleLoop` will occasionally use a ``wx.Timer`` to ensure that it
continues to be called. The time-out used by this ``Timer`` can be queried
and set via the :func:`getIdleTimeout` and :func:`setIdleTimeout` functions.


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
completed.  This therefore gives us a simple way to run a computationally
intensitve task off the main GUI thread (preventing the GUI from locking up),
and to perform some clean up/refresh afterwards.


The :func:`wait` function is given one or more ``Thread`` instances, and a
task to run. It waits until all the threads have finished, and then runs
the task (via :func:`idle`).


The :class:`TaskThread` class is a simple thread which runs a queue of tasks.


Other facilities
----------------


The ``async`` module also defines the :func:`mutex` decorator, which is
intended to be used to mark the methods of a class as being mutually exclusive.
The ``mutex`` decorator uses the :class:`MutexFactory` class to do its work.
"""


import time
import atexit
import logging
import functools
import threading
import collections

try:    import queue
except: import Queue as queue


log = logging.getLogger(__name__)


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

    from fsl.utils.platform import platform as fslplatform

    if name is None:
        name = getattr(task, '__name__', '<unknown>')

    haveWX = fslplatform.haveGui

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

            log.warn('Task "{}" crashed'.format(name), exc_info=True)
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


_idleRegistered = False
"""Boolean flag indicating whether the :func:`_wxIdleLoop` function has
been registered as a ``wx.EVT_IDLE`` event handler. Checked and set
in the :func:`idle` function.
"""


_idleQueue = queue.Queue()
"""A ``Queue`` of functions which are to be run on the ``wx.EVT_IDLE``
loop.
"""


_idleQueueDict = {}
"""A ``dict`` containing the names of all named tasks which are
currently queued on the idle loop (see the ``name`` parameter to the
:func:`idle` function).
"""


_idleTimer = None
"""A ``wx.Timer`` instance which is used to periodically trigger the
:func:`_wxIdleLoop` in circumstances where ``wx.EVT_IDLE`` events may not
be generated. This is created in the first call to :func:`idle`.
"""


_idleCallRate = 200
"""Minimum time (in milliseconds) between consecutive calls to
:func:`_wxIdleLoop`. If ``wx.EVT_IDLE`` events are not being fired, the
:attr:`_idleTimer` is used to maintain the idle loop at this rate.
"""


def idleReset():
    """Reset the internal :func:`idle` queue state.

    In a normal execution environment, this function will never need to be
    called.  However, in an execution environment where multiple ``wx.App``
    instances are created, run, and destroyed sequentially, this function
    will need to be called after each ``wx.App`` has been destroyed.
    Otherwise the ``idle`` function will not work during exeution of
    subsequent ``wx.App`` instances.
    """
    global _idleRegistered
    global _idleQueue
    global _idleQueueDict
    global _idleTimer
    global _idleCallRate

    if _idleTimer is not None:
        _idleTimer.Stop()

    _idleRegistered = False
    _idleQueue      = queue.Queue()
    _idleQueueDict  = {}
    _idleTimer      = None
    _idleCallRate   = 200


# Call idleReset on exit, in
# case the idleTimer is active.
atexit.register(idleReset)


def getIdleTimeout():
    """Returns the current ``wx`` idle loop time out/call rate.
    """
    return _idleCallRate


def setIdleTimeout(timeout=None):
    """Set the ``wx`` idle loop time out/call rate. If ``timeout`` is not
    provided, or is set to ``None``, the timeout is set to 200 milliseconds.
    """

    global _idleCallRate

    if timeout is None:
        timeout = 200

    log.debug('Idle loop timeout changed to {}'.format(timeout))

    _idleCallRate = timeout


class IdleTask(object):
    """Container object used by the :func:`idle` and :func:`_wxIdleLoop`
    functions.
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


def _wxIdleLoop(ev):
    """Function which is called on ``wx.EVT_IDLE`` events, and occasionally
    on ``wx.EVT_TIMER` events via the :attr:`_idleTimer`. If there
    is a function on the :attr:`_idleQueue`, it is popped and called.

    .. note:: The ``wx.EVT_IDLE`` event is only triggered on user interaction
              (e.g. mouse movement). This means that a situation may arise
              whereby a function is queued via the :func:`idle` function, but
              no ``EVT_IDLE`` event gets generated. Therefore, the
              :attr:`_idleTimer` object is occasionally used to call this
              function as well.
    """

    import wx
    global _idleQueue
    global _idleQueueDict
    global _idleTimer
    global _idleCallRate

    ev.Skip()

    try:
        task = _idleQueue.get_nowait()

    except queue.Empty:

        # Make sure that we get called periodically,
        # if EVT_IDLE decides to stop firing. If
        # _idleTimer is None, then idleReset has
        # probably been called.
        if _idleTimer is not None:
            _idleTimer.Start(_idleCallRate, wx.TIMER_ONE_SHOT)
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
    # _idleCallRate millisecs.
    if elapsed < task.after:
        log.debug('Re-queueing function ({}) on wx idle loop'.format(taskName))
        _idleQueue.put_nowait(task)
        queueSizeOffset = 1

    # Has the task timed out?
    elif task.timeout == 0 or (elapsed < task.timeout):

        log.debug('Running function ({}) on wx idle loop'.format(taskName))

        try:
            task.task(*task.args, **task.kwargs)
        except Exception as e:
            log.warning('Idle task {} crashed - {}: {}'.format(
                taskName, type(e).__name__, str(e)), exc_info=True)

        if task.name is not None:
            try:             _idleQueueDict.pop(task.name)
            except KeyError: pass

    # More tasks on the queue?
    # Request anotherd event
    if _idleQueue.qsize() > queueSizeOffset:
        ev.RequestMore()

    # Otherwise use the idle
    # timer to make sure that
    # the loop keeps ticking
    # over
    else:
        _idleTimer.Start(_idleCallRate, wx.TIMER_ONE_SHOT)


def inIdle(taskName):
    """Returns ``True`` if a task with the given name is queued on the
    idle loop (or is currently running), ``False`` otherwise.
    """
    global _idleQueueDict
    return taskName in _idleQueueDict


def cancelIdle(taskName):
    """If a task with the given ``taskName`` is in the idle queue, it
    is cancelled. If the task is already running, it cannot be cancelled.

    A ``KeyError`` is raised if no task called ``taskName`` exists.
    """

    global _idleQueueDict
    _idleQueueDict[taskName].timeout = -1


def idle(task, *args, **kwargs):
    """Run the given task on a ``wx.EVT_IDLE`` event.

    :arg task:         The task to run.

    :arg name:         Optional. If provided, must be provided as a keyword
                       argument. Specifies a name that can be used to query
                       the state of this task via the :func:`inIdle` function.

    :arg after:        Optional. If provided, must be provided as a keyword
                       argument. A time, in seconds, which specifies the
                       amount of time to wait before running this task after
                       it has been scheduled.

    :arg timeout:      Optional. If provided, must be provided as a keyword
                       argument. Specifies a time out, in seconds. If this
                       amount of time passes before the function gets
                       scheduled to be called on the idle loop, the function
                       is not called, and is dropped from the queue.

    :arg dropIfQueued: Optional. If provided, must be provided as a keyword
                       argument. If ``True``, and a task with the given
                       ``name`` is already enqueud, that function is dropped
                       from the queue, and the new task is enqueued. Defaults
                       to ``False``. This argument takes precedence over the
                       ``skipIfQueued`` argument.

    :arg skipIfQueued: Optional. If provided, must be provided as a keyword
                       argument. If ``True``, and a task with the given
                       ``name`` is already enqueud, (or is running), the
                       function is not called. Defaults to ``False``.

    :arg alwaysQueue:  Optional. If provided, must be provided as a keyword
                       argument. If ``True``, and a ``wx.MainLoop`` is not
                       running, the task is enqueued anyway, under the
                       assumption that a ``wx.MainLoop`` will be started in
                       the future. Note that, if ``wx.App`` has not yet been
                       created, another  call to ``idle`` must be made after
                       the app has been created for the original task to be
                       executed. If ``wx`` is not available, this parameter
                       will be ignored, and the task executed directly.


    All other arguments are passed through to the task function.


    If a ``wx.App`` is not running, the ``timeout``, ``name`` and
    ``skipIfQueued`` arguments are ignored. Instead, the call will sleep for
    ``after`` seconds, and then the ``task`` is called directly.


    .. note:: If the ``after`` argument is used, there is no guarantee that
              the task will be executed in the order that it is scheduled.
              This is because, if the required time has not elapsed when
              the task is popped from the queue, it will be re-queued.

    .. note:: If you schedule multiple tasks with the same ``name``, and you
              do not use the ``skipIfQueued`` or ``dropIfQueued`` arguments,
              all of those tasks will be executed, but you will only be able
              to query/cancel the most recently enqueued task.

    .. note:: You will run into difficulties if you schedule a function that
              expects/accepts its own keyword arguments called ``name``,
              ``skipIfQueued``, ``dropIfQueued``, ``after``, ``timeout``, or
              ``alwaysQueue``.
    """

    from fsl.utils.platform import platform as fslplatform

    global _idleRegistered
    global _idleTimer
    global _idleQueue
    global _idleQueueDict

    schedtime    = time.time()
    timeout      = kwargs.pop('timeout',      0)
    after        = kwargs.pop('after',        0)
    name         = kwargs.pop('name',         None)
    dropIfQueued = kwargs.pop('dropIfQueued', False)
    skipIfQueued = kwargs.pop('skipIfQueued', False)
    alwaysQueue  = kwargs.pop('alwaysQueue',  False)

    canHaveGui = fslplatform.canHaveGui
    haveGui    = fslplatform.haveGui

    # If there is no possibility of a
    # gui being available in the future,
    # then alwaysQueue is ignored.
    if haveGui or (alwaysQueue and canHaveGui):

        import wx
        app = wx.GetApp()

        # Register on the idle event
        # if an app is available
        #
        # n.b. The 'app is not None' test will
        # potentially fail in scenarios where
        # multiple wx.Apps have been instantiated,
        # as it may return a previously created
        # app.
        if (not _idleRegistered) and (app is not None):

            log.debug('Registering async idle loop')

            app.Bind(wx.EVT_IDLE, _wxIdleLoop)

            _idleTimer      = wx.Timer(app)
            _idleRegistered = True

            _idleTimer.Bind(wx.EVT_TIMER, _wxIdleLoop)

        if name is not None and inIdle(name):

            if dropIfQueued:

                # The cancelIdle function sets the old
                # task timeout to -1, so it won't get
                # executed. But the task is left in the
                # _idleQueue, and in the _idleQueueDict.
                # In the latter, the old task gets
                # overwritten with the new task below.
                cancelIdle(name)
                log.debug('Idle task ({}) is already queued - '
                          'dropping the old task'.format(name))

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

        _idleQueue.put_nowait(idleTask)

        if name is not None:
            _idleQueueDict[name] = idleTask

    else:
        time.sleep(after)
        log.debug('Running idle task directly')
        task(*args, **kwargs)


def idleWhen(func, condition, *args, **kwargs):
    """Poll the ``condition`` function periodically, and schedule ``func`` on
    :func:`idle` when it returns ``True``.

    :arg func:      Function to call.

    :arg condition: Function which returns ``True`` or ``False``. The ``func``
                    function is only called when the ``condition`` function
                    returns ``True``.

    :arg pollTime:  Must be passed as a keyword argument. Time (in seconds) to
                    wait between successive calls to ``when``. Defaults to
                    ``0.2``.
    """

    pollTime = kwargs.get('pollTime', 0.2)

    if not condition():
        idle(idleWhen, func, condition, after=pollTime, *args, **dict(kwargs))
    else:
        kwargs.pop('pollTime', None)
        idle(func, *args, **kwargs)


def wait(threads, task, *args, **kwargs):
    """Creates and starts a new ``Thread`` which waits for all of the ``Thread``
    instances to finsih (by ``join``ing them), and then runs the given
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

    from fsl.utils.platform import platform as fslplatform

    direct = kwargs.pop('wait_direct', False)

    if not isinstance(threads, collections.Sequence):
        threads = [threads]

    haveWX = fslplatform.haveGui

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


class Task(object):
    """Container object which encapsulates a task that is run by a
    :class:`TaskThread`.
    """
    def __init__(self, name, func, onFinish, args, kwargs):
        self.name     = name
        self.func     = func
        self.onFinish = onFinish
        self.args     = args
        self.kwargs   = kwargs
        self.enabled  = True


class TaskThreadVeto(Exception):
    """Task functions which are added to a :class:`TaskThread` may raise
    a ``TaskThreadVeto`` error to skip processing of the task's ``onFinish``
    handler (if one has been specified). See the :meth:`TaskThread.enqueue`
    method for more details.
    """
    pass


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
                       a keyword argument. If the ``func`` raises a
                       :class`TaskThreadVeto` error, this function will not
                       be called.

        All other arguments are passed through to the task function when it is
        executed.

        .. note:: If the specified ``taskName`` is not unique (i.e. another
                  task with the same name may already be enqueued), the
                  :meth:`isQueued` method will probably return invalid
                  results.

        .. warning:: Make sure that your task function is not expecting keyword
                     arguments called ``taskName`` or ``onFinish``!
        """

        name     = kwargs.pop('taskName', None)
        onFinish = kwargs.pop('onFinish', None)

        log.debug('Enqueueing task: {} [{}]'.format(
            name, getattr(func, '__name__', '<unknown>')))

        t = Task(name, func, onFinish, args, kwargs)
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
            except:
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


class MutexFactory(object):
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

        # Get the lock object, creating if it necessary
        lock = getattr(instance, '_async_mutex_lock', None)
        if lock is None:
            lock                       = threading.Lock()
            instance._async_mutex_lock = lock

        # The true decorator function:
        #    - Acquire the lock (blocking until it has been released)
        #    - Run the decorated method
        #    - Release the lock
        def decorator(*args, **kwargs):
            lock.acquire()
            try:
                return self.__func(instance, *args, **kwargs)
            finally:
                lock.release()

        # Replace this MutexFactory with
        # the decorator on the instance
        decorator = functools.update_wrapper(decorator, self.__func)
        setattr(instance, self.__func.__name__, decorator)
        return decorator
