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

import props

import fsl.utils.async as async


log = logging.getLogger(__name__)


DEFAULT_TOPIC = 'default'
"""Topic used when the caller does not specify one when registering,
deregistering, or notifying listeners.
"""


class _Listener(object):
    """This class is used internally by the :class:`.Notifier` class to
    store references to callback functions.
    """

    def __init__(self, name, callback, topic, runOnIdle):

        self.name = name

        # We use a WeakFunctionRef so we can refer to
        # both functions and class/instance methods
        self.__callback = props.WeakFunctionRef(callback)
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
              registered callback functions, using the :class:`WeakFunctionRef`
              class, provided by the :mod:`props` package.
    """


    def __new__(cls, *args, **kwargs):
        """Initialises a dictionary of listeners on a new ``Notifier``
        instance.
        """
        new             = object.__new__(cls)
        new.__listeners = collections.defaultdict(collections.OrderedDict)

        if isinstance(new, props.HasProperties):
            log.warning('Warning: {} is a sub-class of both '
                        'Notifier and props.HasProperties!')

        return new

        
    def register(self, name, callback, topic=None, runOnIdle=False):
        """Register a listener with this ``Notifier``.

        :arg name:      A unique name for the listener.

        :arg callback:  The function to call - must accept two positional
                        arguments:

                          - this ``Notifier`` instance.

                          - A value, which may be ``None`` - see
                            :meth:`notify`.

        :arg topic:     Optional topic on which to listen for notifications.

        :arg runOnIdle: If ``True``, this listener will be called on the main
                        thread, via the :func:`.async.idle` function.
                        Otherwise this function will be called directly by the
                        :meth:`notify` method. Defaults to ``False``.
        """

        if topic is None:
            topic = DEFAULT_TOPIC

        listener = _Listener(name, callback, topic, runOnIdle)
        self.__listeners[topic][name] = listener

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
        
        log.debug('{}: De-registered listener {}'.format(
            type(self).__name__, listener))


    def enable(self, name, topic=None):
        """Enables the specified listener. """
        if topic is None:
            topic = DEFAULT_TOPIC

        self.__listeners[topic][name].enabled = True


    def disable(self, name, topic=None):
        """Disables the specified listener. """
        if topic is None:
            topic = DEFAULT_TOPIC

        self.__listeners[topic][name].enabled = False


    def isEnabled(self, name, topic=None):
        """Returns ``True`` if the specified listener is enabled, ``False``
        otherwise.
        """
        if topic is None:
            topic = DEFAULT_TOPIC

        return self.__listeners[topic][name].enabled


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
        """

        state = self.isEnabled(name, topic)
        self.disable(name, topic)

        try:
            yield

        finally:
            if state: self.enable( name, topic)
            else:     self.disable(name, topic)
        

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
                  via :func:`async.idle`. Other listeners are called directly.
                  See :meth:`register`.
        """

        topic     = kwargs.get('topic', DEFAULT_TOPIC)
        value     = kwargs.get('value', None)
        listeners = [self.__listeners[topic]]

        if topic != DEFAULT_TOPIC:
            listeners.append(self.__listeners[DEFAULT_TOPIC])

        if sum(map(len, listeners)) == 0:
            return

        if log.getEffectiveLevel() >= logging.DEBUG:
            stack = inspect.stack()
            frame = stack[1]

            srcMod  = '...{}'.format(frame[1][-20:])
            srcLine = frame[2] 

            log.debug('{}: Notifying {} listeners (topic: {}) [{}:{}]'.format(
                type(self).__name__,
                sum(map(len, listeners)),
                topic,
                srcMod,
                srcLine))

        for ldict in listeners:
            for name, listener in list(ldict.items()):
                
                callback = listener.callback

                # The callback, or the owner of the
                # callback function may have been
                # gc'd - remove it if this is the case.
                if callback is None:
                    log.debug('Listener {} has been gc\'d - '
                              'removing from list'.format(name))
                    ldict.pop(name)

                elif not listener.enabled:
                    continue
                    
                elif listener.runOnIdle: async.idle(callback, self, value)
                else:                    callback(            self, value)
