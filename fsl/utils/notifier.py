#!/usr/bin/env python
#
# notify.py - The Notifier mixin class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Notifier` class, intended to be used
as a mixin for providing a simple notification API.
"""

import collections


class Notifier(object):
    """The ``Notifier`` class is a mixin which provides simple notification
    capability. Listeners can be registered/deregistered via the
    :meth:`register` and :meth:`deregister` methods, and notified via
    the :meth:`notify` method.
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
        self.__listeners[name] = callback

        
    def deregister(self, name):
        """De-register a listener that has been previously registered with
        this ``Notifier``.

        :arg name: Name of the listener to de-register.
        """
        self.__listeners.pop(name)
        

    def notify(self):
        """Notify all registered listeners of this ``Notifier``. """
        for name, callback in self.__listeners.items():
            callback(self)
