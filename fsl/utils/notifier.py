#!/usr/bin/env python
#
# notify.py - The Notifier mixin class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Notifier` class, intended to be used
as a mixin for providing a simple notification API.
"""


import logging
import inspect
import contextlib
import collections

import fsl.utils.idle        as idle
import fsl.utils.weakfuncref as weakfuncref


log = logging.getLogger(__name__)


DEFAULT_TOPIC = 'default'
"""Topic used when the caller does not specify one when registering,
deregistering, or notifying listeners.
"""

class Registered(Exception):
    """``Exception`` raised by :meth:`Notifier.register` when an attempt is
    made to register a listener with a name that is already registered.
    """
    pass


class _Listener(object):
    """This class is used internally by the :class:`.Notifier` class to
    store references to callback functions.
    """

    def __init__(self, name, callback, topic, runOnIdle):

        self.name = name

        # We use a WeakFunctionRef so we can refer to
        # both functions and class/instance methods
        self.__callback = weakfuncref.WeakFunctionRef(callback)
        self.topic      = topic
        self.runOnIdle  = runOnIdle
        self.enabled    = True


    @property
    def callback(self):
        """Returns the callback function, or ``None`` if it has been
        garbage-collected.
        """
        return self.__callback.function()


    def __str__(self):

        cb = self.callback

        if cb is not None: cbName = getattr(cb, '__name__', '<callable>')
        else:              cbName = '<deleted>'

        return 'Listener {} [topic: {}] [function: {}]'.format(
            self.name, self.topic, cbName)


    def __repr__(self):
        return self.__str__()


class Notifier(object):
    """The ``Notifier`` class is a mixin which provides simple notification
    capability. Listeners can be registered/deregistered to listen via the
    :meth:`register` and :meth:`deregister` methods, and notified via the
    :meth:`notify` method. Listeners can optionally listen on a specific
    *topic*, or be notified for all topics.

    .. note:: The ``Notifier`` class stores ``weakref`` references to
              registered callback functions, using the
              :class:`.WeakFunctionRef` class.
    """


    def __new__(cls, *args, **kwargs):
        """Initialises a dictionary of listeners on a new ``Notifier``
        instance.
        """

        new = super(Notifier, cls).__new__(cls)

        # Listeners are stored in this
        #
        # { topic : { name : _Listener } }
        #
        # dictionary, with the inner
        # dictionaries ordered by
        # insertion time.
        new.__listeners = collections.defaultdict(collections.OrderedDict)

        # Notification can be enabled on a per-
        # topic basis. This dictionary contains
        # enable states for each topic, as
        # { topic : enabled } mappings.
        new.__enabled = {}

        return new


    def register(self, name, callback, topic=None, runOnIdle=False):
        """Register a listener with this ``Notifier``.

        :arg name:      A unique name for the listener.

        :arg callback:  The function to call - must accept two positional
                        arguments:

                          - this ``Notifier`` instance.

                          - The topic, which may be ``None`` - see
                            :meth:`notify`.

                          - A value, which may be ``None`` - see
                            :meth:`notify`.

        :arg topic:     Optional topic on which to listen for notifications.

        :arg runOnIdle: If ``True``, this listener will be called on the main
                        thread, via the :func:`.idle.idle` function.
                        Otherwise this function will be called directly by the
                        :meth:`notify` method. Defaults to ``False``.

        :raises: A :exc:`Registered` error if a listener with the given
                 ``name`` is already registered on the given ``topic``.
        """

        if topic is None:
            topic = DEFAULT_TOPIC

        listener = _Listener(name, callback, topic, runOnIdle)

        if name in self.__listeners[topic]:
            raise Registered('Listener {} is already registered'.format(name))

        self.__listeners[topic][name] = listener
        self.__enabled[  topic]       = self.__enabled.get(topic, True)

        log.debug('{}: Registered {}'.format(type(self).__name__, listener))


    def deregister(self, name, topic=None):
        """De-register a listener that has been previously registered with
        this ``Notifier``.

        :arg name:  Name of the listener to de-register.
        :arg topic: Topic on which the listener was registered.
        """

        if topic is None:
            topic = DEFAULT_TOPIC

        listeners = self.__listeners.get(topic, None)

        # Silently absorb invalid topics
        if listeners is None:
            return

        listener = listeners.pop(name, None)

        # Silently absorb invalid names - the
        # notify function may have removed gc'd
        # listeners, so they will no longer exist
        # in the dictionary.
        if listener is None:
            return

        # No more listeners for this topic
        if len(listeners) == 0:
            self.__listeners.pop(topic)
            self.__enabled  .pop(topic)

        log.debug('{}: De-registered listener {}'.format(
            type(self).__name__, listener))


    def enable(self, name, topic=None, enable=True):
        """Enables the specified listener. """
        if topic is None:
            topic = DEFAULT_TOPIC

        self.__listeners[topic][name].enabled = enable


    def disable(self, name, topic=None):
        """Disables the specified listener. """
        self.enable(name, topic, False)


    def isEnabled(self, name, topic=None):
        """Returns ``True`` if the specified listener is enabled, ``False``
        otherwise.
        """
        if topic is None:
            topic = DEFAULT_TOPIC

        try:             return self.__listeners[topic][name].enabled
        except KeyError: return False


    def enableAll(self, topic=None, state=True):
        """Enable/disable all listeners for the specified topic.

        :arg topic: Topic to enable/disable listeners on. If ``None``,
                    all listeners are enabled/disabled.

        :arg state: State to set listeners to.
        """

        if topic is not None: topics = [topic]
        else:                 topics = list(self.__enabled.keys())

        for topic in topics:
            if topic in self.__enabled:
                self.__enabled[topic] = state


    def disableAll(self, topic=None):
        """Disable all listeners for the specified topic (or ``None``
        to disable all listeners).
        """
        self.enableAll(topic, False)


    def isAllEnabled(self, topic=None):
        """Returns ``True`` if all listeners for the specified topic (or all
        listeners if ``topic=None``) are enabled, ``False`` otherwise.
        """
        if topic is None:
            topic = DEFAULT_TOPIC

        return self.__enabled.get(topic, False)


    @contextlib.contextmanager
    def skipAll(self, topic=None):
        """Context manager which disables all listeners for the
        specified topic, and restores their state before returning.

        :arg topic: Topic to skip listeners on. If ``None``, notification
                    is disabled for all topics.
        """

        if topic is not None: topics = [topic]
        else:                 topics = list(self.__enabled.keys())

        states = [self.isAllEnabled(t) for t in topics]

        for t in topics:
            self.disableAll(t)

        try:
            yield

        finally:
            for t, s in zip(topics, states):
                self.enableAll(t, s)


    @contextlib.contextmanager
    def skip(self, name, topic=None):
        """Context manager which disables the speciifed listener, and
        restores its state before returning.

        You can use this method if you have some code which triggers a
        notification, but you do not your own listener to be notified.
        For example::

            def __myListener(*a):
                pass

            notifier.register('myListener', __myListener)

            with notifier.skip('myListener'):
                # if a notification is triggered
                # by the code here, the __myListener
                # function will not be called.

        :arg name:  Name of the listener to skip

        :arg topic: Topic or topics that the listener is registered on.
        """

        if topic is None or isinstance(topic, str):
            topic = [topic]

        topics = topic
        states = [self.isEnabled(name, t) for t in topics]

        for topic in topics:
            self.disable(name, topic)

        try:
            yield

        finally:
            for topic, state in zip(topics, states):
                self.enable(name, topic, state)


    def notify(self, *args, **kwargs):
        """Notify all registered listeners of this ``Notifier``.

        The documented arguments must be passed as keyword arguments.

        :arg topic: The topic on which to notify. Default
                    listeners are always notified, regardless
                    of the specified topic.

        :arg value: A value passed through to the registered listener
                    functions. If not provided, listeners will be passed
                    a value of ``None``.

        All other arguments passed to this method are ignored.

        .. note:: Listeners registered with ``runOnIdle=True`` are called
                  via :func:`idle.idle`. Other listeners are called directly.
                  See :meth:`register`.
        """

        topic     = kwargs.get('topic', None)
        value     = kwargs.get('value', None)
        listeners = self.__getListeners(topic)

        if len(listeners) == 0:
            return

        if log.getEffectiveLevel() <= logging.DEBUG:
            stack   = inspect.stack()
            frame   = stack[1]
            srcMod  = '...{}'.format(frame[1][-20:])
            srcLine = frame[2]

            log.debug('{}: Notifying {} listeners (topic: {}) [{}:{}]'.format(
                type(self).__name__,
                len(listeners),
                topic,
                srcMod,
                srcLine))

        for listener in listeners:

            callback = listener.callback
            name     = listener.name

            # The callback, or the owner of the
            # callback function may have been
            # gc'd - remove it if this is the case.
            if callback is None:
                log.debug('Listener {} has been gc\'d - '
                          'removing from list'.format(name))
                self.__listeners[listener.topic].pop(name)

            elif not listener.enabled:
                continue

            elif listener.runOnIdle: idle.idle(callback, self, topic, value)
            else:                    callback(           self, topic, value)


    def __getListeners(self, topic):
        """Called by :meth:`notify`. Returns all listeners which should be
        notified for the specified ``topic``.
        """

        listeners = []

        # Default listeners are called on all topics
        # (unless the default topic is disabled)
        if self.__enabled.get(DEFAULT_TOPIC, False):
            listeners.extend(self.__listeners.get(DEFAULT_TOPIC, {}).values())

        if topic is None or topic == DEFAULT_TOPIC:
            return listeners

        if self.__enabled.get(topic, False):
            listeners.extend(self.__listeners.get(topic, {}).values())

        return listeners
