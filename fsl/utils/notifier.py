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
import collections

import props

import fsl.utils.async as async


log = logging.getLogger(__name__)


DEFAULT_TOPIC = 'default'
"""Topic used when the caller does not specify one when registering,
deregistering, or notifying listeners.
"""


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

        # We use a WeakFunctionRef so we can refer to
        # both functions and class/instance methods
        self.__listeners[topic][name] = (props.WeakFunctionRef(callback),
                                         runOnIdle)

        log.debug('{}: Registered listener {} '
                  '[topic: {}] (function: {})'.format(
                      type(self).__name__,
                      name,
                      topic, 
                      getattr(callback, '__name__', '<callable>')))

        
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

        callback, _ = listeners.pop(name, (None, None))

        # Silently absorb invalid names - the
        # notify function may have removed gc'd
        # listeners, so they will no longer exist
        # in the dictionary.
        if callback is None:
            return

        # No more listeners for this topic
        if len(listeners) == 0:
            self.__listeners.pop(topic)
        
        callback = callback.function()

        if callback is not None:
            cbName = getattr(callback, '__name__', '<callable>')
        else:
            cbName = '<deleted>'

        log.debug('{}: De-registered listener {} '
                  '[topic: {}] (function: {})'.format(
                      type(self).__name__,
                      name,
                      topic,
                      cbName)) 
        

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
            for name, (callback, runOnIdle) in list(ldict.items()):
                
                callback = callback.function()

                # The callback, or the owner of the
                # callback function may have been
                # gc'd - remove it if this is the case.
                if callback is None:
                    log.debug('Listener {} has been gc\'d - '
                              'removing from list'.format(name))
                    ldict.pop(name)
                    
                elif runOnIdle: async.idle(callback, self, value)
                else:           callback(            self, value)
