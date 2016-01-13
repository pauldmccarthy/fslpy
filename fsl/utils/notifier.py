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
import weakref
import collections


log = logging.getLogger(__name__)


class Notifier(object):
    """The ``Notifier`` class is a mixin which provides simple notification
    capability. Listeners can be registered/deregistered via the
    :meth:`register` and :meth:`deregister` methods, and notified via
    the :meth:`notify` method.

    .. note:: The ``Notifier`` class stores ``weakref`` references to
              registered callback functions.
    """

    def __new__(cls, *args, **kwargs):
        """Initialises a dictionary of listeners on a new ``Notifier``
        instance.
        """
        new             = object.__new__(cls, *args, **kwargs)
        new.__listeners = collections.OrderedDict()

        return new

        
    def register(self, name, callback):
        """Register a listener with this ``Notifier``.

        :arg name:     A unique name for the listener.
        :arg callback: The function to call - must accept this ``Notifier``
                       instance as its sole argument.
        """
        self.__listeners[name] = weakref.ref(callback)

        log.debug('{}: Registered listener {} (function: {})'.format(
            type(self).__name__,
            name,
            getattr(callback, '__name__', '<callable>')))

        
    def deregister(self, name):
        """De-register a listener that has been previously registered with
        this ``Notifier``.

        :arg name: Name of the listener to de-register.
        """

        callback = self.__listeners.pop(name, None)

        # Silently absorb invalid names - the
        # notify function may have removed gc'd
        # listeners, so they will no longer exist
        # in the dictionary.
        if callback is None:
            return
        
        callback = callback()

        if callback is not None:
            cbName = getattr(callback, '__name__', '<callable>')
        else:
            cbName = '<deleted>'

        log.debug('{}: De-registered listener {} (function: {})'.format(
            type(self).__name__, name, cbName)) 
        

    def notify(self):
        """Notify all registered listeners of this ``Notifier``. """
        
        log.debug('{}: Notifying listeners'.format(type(self).__name__))

        listeners = list(self.__listeners.items())
                
        for name, callback in listeners:

            callback = callback()

            # The callback, or the owner of the
            # callback function may have been
            # gc'd - remove it if this is the case.
            if callback is None: self.__listeners.pop(name)
            else:                callback(self)
