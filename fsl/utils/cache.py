#!/usr/bin/env python
#
# cache.py - A simple cache based on an OrderedDict.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`.Cache` class., a simple in-memory cache.
"""


import time
import collections


class Expired(Exception):
    """``Exception`` raised by the :meth:`Cache.get` metho when an attempt is
    made to access a cache item that has expired.
    """
    pass


class CacheItem(object):
    """Internal container class used to store :class:`Cache` items. """

    def __init__(self, key, value, expiry=0):
        self.key       = key
        self.value     = value
        self.expiry    = expiry
        self.storetime = time.time()


class Cache(object):
    """The ``Cache`` is a simple in-memory cache built on a
    ``collections.OrderedDict``. The ``Cache`` class has the following
    features:

       - When an item is added to a full cache, the oldest entry is
         automatically dropped.

       - Expiration times can be specified for individual items. If a request
         is made to access an expired item, an :class:`Expired` exception is
         raised.
    """

    def __init__(self, maxsize=100, lru=False):
        """Create a ``Cache``.

        :arg maxsize: Maximum number of items allowed in the ``Cache`` before
                      it starts dropping old items

        :arg lru:     (least recently used) If ``False`` (the default), items
                      are dropped according to their insertion time. Otherwise,
                      items are dropped according to their most recent access
                      time.
        """
        self.__cache   = collections.OrderedDict()
        self.__maxsize = maxsize
        self.__lru     = lru


    def put(self, key, value, expiry=0):
        """Put an item in the cache.

        :arg key:    Item identifier (must be hashable).

        :arg value:  The item to store.

        :arg expiry: Expiry time in seconds. An item with an expiry time of
                     ``0`` will not expire.
        """

        if len(self.__cache) == self.__maxsize and \
           key not in self.__cache:
            self.__cache.popitem(last=False)

        self.__cache[key] = CacheItem(key, value, expiry)


    def get(self, key, *args, **kwargs):
        """Get an item from the cache.

        :arg key:     Item identifier.
        :arg default: Default value to return if the item is not in the cache,
                      or has expired.
        """

        defaultSpecified, default = self.__parseDefault(*args, **kwargs)

        # Default value specified - return
        # it if the key is not in the cache
        if defaultSpecified:

            entry = self.__cache.get(key, None)

            if entry is None:
                return default

        # No default value specified -
        # allow KeyErrors to propagate
        else:
            entry = self.__cache[key]

        # Check to see if the entry
        # has expired
        now = time.time()

        if entry.expiry > 0:
            if now - entry.storetime > entry.expiry:

                self.__cache.pop(key)

                if defaultSpecified: return default
                else:                raise Expired(key)

        # If we are an lru cache, update
        # this entry's expiry, and update
        # its order in the cache dict
        if self.__lru:
            entry.storetime = now
            self.__cache.pop(key)
            self.__cache[key] = entry

        return entry.value


    def clear(self):
        """Remove all items from the cache. """
        self.__cache = collections.OrderedDict()


    def __len__(self):
        """Returns the number of items in the cache. """
        return len(self.__cache)


    def __getitem__(self, key):
        """Get an item from the cache. """
        return self.get(key)


    def __setitem__(self, key, value):
        """Add an item to the cache. """
        return self.put(key, value)


    def __contains__(self, key):
        """Check whether an item is in the cache. Note that the item may
        be in the cache, but it may be expired.
        """
        return key in self.__cache


    def __parseDefault(self, *args, **kwargs):
        """Used by the :meth:`get` method. Parses the ``default`` argument,
        which may be specified as either a positional or keyword argumnet.

        :returns: A tuple containing two values:

                    - ``True`` if a default argument was specified, ``False``
                      otherwise.

                    - The specified default value, or ``None`` if it wasn't
                      specified.
        """

        nargs = len(args) + len(kwargs)

        # Nothing specified (ok), or too
        # many arguments specified (not ok)
        if   nargs == 0: return False, None
        elif nargs != 1: raise ValueError()

        # The default value is either specified as a
        # positional argument, or as a keyword argument
        if   len(args)   == 1: return True, args[0]
        elif len(kwargs) == 1: return True, kwargs['default']
