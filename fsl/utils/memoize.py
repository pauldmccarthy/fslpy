#!/usr/bin/env python
#
# memoize.py - Memoization decorators.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides a handful of decorators which may be used to memoize
a function:

 .. autosummary::
    :nosignatures:

    memoize
    Memoize
    Instanceify
    memoizeMD5
    skipUnchanged
"""


import logging
import hashlib
import functools

log = logging.getLogger(__name__)


def memoize(func=None):
    """Memoize the given function by the value of the input arguments.

    This function simply returns a :class:`Memoize` instance.
    """

    return Memoize(func)


class Memoize(object):
    """Decorator which can be used to memoize a function or method. Use like
    so::

        @memoize
        def myfunc(*a, **kwa):
            ...

        @memoize()
        def otherfunc(*a, **kwax):
            ...

    A ``Memoize`` instance maintains a cache which contains ``{args : value}``
    mappings, where ``args`` are the input arguments to the function, and
    ``value`` is the value that the function returned for those arguments.
    When a memoized function is called with arguments that are present in the
    cache, the cached values are returned, and the function itself is not
    called.


    The :meth:`invalidate` method may be used to clear the internal cache.


    Note that the arguments used for memoization must be hashable, as they are
    used as keys in a dictionary.
    """


    def __init__(self, *args, **kwargs):
        """Create a ``Memoize`` object.
        """

        self.__cache      = {}
        self.__func       = None
        self.__defaultKey = '_memoize_noargs_'

        self.__setFunction(*args, **kwargs)


    def invalidate(self, *args, **kwargs):
        """Clears the internal cache. If no arguments are given, the entire
        cache is cleared. Otherwise, only the cached value for the provided
        arguments is cleared.
        """

        if len(args) + len(kwargs) == 0:
            self.__cache = {}

        else:
            key = self.__makeKey(*args, **kwargs)

            try:
                self.__cache.pop(key)
            except KeyError:
                pass


    def __setFunction(self, *args, **kwargs):
        """Used internally to set the memoized function. """

        if self.__func is not None:
            return False

        # A no-brackets style
        # decorator was used
        isfunc = (len(kwargs) == 0 and len(args) == 1 and callable(args[0]))

        if isfunc:
            self.__func = args[0]

        return isfunc


    def __makeKey(self, *a, **kwa):
        """Constructs a key for use with the cache from the given arguments.
        """
        key = []

        if a   is not None: key += list(a)
        if kwa is not None: key += [kwa[k] for k in sorted(kwa.keys())]

        # This decorator was created without
        # any arguments specified - use the
        # default cache key.
        if len(key) == 0:
            key = [self.__defaultKey]

        return tuple(key)


    def __call__(self, *a, **kwa):
        """Checks the cache against the given arguments. If a cached value
        is present, it is returned. Otherwise the memoized function is called,
        and its value is cached and returned.
        """

        if self.__setFunction(*a, **kwa):
            return self

        key = self.__makeKey(*a, **kwa)

        try:
            result = self.__cache[key]

            log.debug(u'Retrieved from cache[{}]: {}'.format(key, result))

        except KeyError:

            result            = self.__func(*a, **kwa)
            self.__cache[key] = result

            log.debug(u'Adding to cache[{}]: {}'.format(key, result))

        return result


def memoizeMD5(func):
    """Memoize the given function. Whenever the function is called, an
    md5 digest of its arguments is calculated - if the digest has been
    previously cached, the previous value calculated by the function is
    returned.
    """

    cache = {}

    def wrapper(*args, **kwargs):
        args = list(args) + list(kwargs.values())

        hashobj = hashlib.md5()

        # Convert each arg to a string
        # representation, then encode
        # it into a sequence of (utf-8
        # compatible) bytes , and take
        # the hash of those bytes.
        for arg in args:
            if not isinstance(arg, str):
                arg = str(arg)
            arg = arg.encode('utf-8')
            hashobj.update(arg)

        digest = hashobj.hexdigest()
        cached = cache.get(digest)

        if cached is not None:
            return cached

        result = func(*args, **kwargs)

        log.debug(u'Adding to MD5 cache[{}]: {}'.format(
            digest, result))

        cache[digest] = result

        return result

    return wrapper


def skipUnchanged(func):
    """This decorator is intended for use with *setter* functions - a function
    which accepts a name and a value, and is intended to set some named
    attribute to the given value.

    This decorator keeps a cache of name-value pairs. When the decorator is
    called with a specific name and value, the cache is checked and, if the
    given value is the same as the cached value, the decorated function is
    *not* called. If the given value is different from the cached value (or
    there is no value), the decorated function is called.


    The ``invalidate`` method may be called on a ``skipUnchanged``-decorated
    function to clear the internal cache. For example::

        @skipUnchanged
        def setval(name, value):
            # ...

        # ...

        setval.invalidate()

    .. note:: This decorator ignores the return value of the decorated
              function.

    :returns: ``True`` if the underlying setter function was called, ``False``
              otherwise.
    """

    import numpy as np

    cache = {}

    # TODO merge skipUnchanged and Memoize somehow
    def invalidate():
        cache.clear()

    def wrapper(name, value, *args, **kwargs):

        oldVal = cache.get(name, None)

        if oldVal is not None:

            oldIsArray = isinstance(oldVal, np.ndarray)
            newIsArray = isinstance(value,  np.ndarray)
            isarray    = oldIsArray or newIsArray

            if isarray:
                a = np.array(oldVal, copy=False)
                b = np.array(value,  copy=False)

                nochange = (a.shape == b.shape) and np.allclose(a, b)
            else:
                nochange = oldVal == value

            if nochange:
                return False

        func(name, value, *args, **kwargs)

        cache[name] = value

        return True

    wrapper.invalidate = invalidate

    return wrapper


class Instanceify(object):
    """This class is intended to be used to decorate other decorators, so they
    can be applied to instance methods. For example, say we have the following
    class::

        class Container(object):

            def __init__(self):
                self.__items = {}

            @skipUnchanged
            def set(self, name, value):
                self.__items[name] = value


    Given this definition, a single :func:`skipUnchanged` decorator will be
    created and shared amongst all ``Container`` instances. This is not ideal,
    as the value cache created by the :func:`skipUnchanged` decorator should
    be associated with a single ``Container`` instance.


    By redefining the ``Container`` class definition like so::


        class Container(object):

            def __init__(self):
                self.__items = {}

            @Instanceify(skipUnchanged)
            def set(self, name, value):
                self.__items[name] = value


    a separate :func:`skipUnchanged` decorator is created for, and associated
    with, every ``Container`` instance.


    This is achieved because an ``Instanceify`` instance is a descriptor. When
    first accessed as an instance attribute, an ``Instanceify`` instance will
    create the real decorator function, and replace itself on the instance.
    """


    def __init__(self, realDecorator):
        """Create an ``Instanceify`` decorator.

        :arg realDecorator: A reference to the decorator that is to be
                            *instance-ified*.
        """

        self.__realDecorator = realDecorator
        self.__func          = None


    def __call__(self, func):
        """Called immediately after :meth:`__init__`, and passed the method
        that is to be decorated.
        """
        self.__func = func
        return self


    def __get__(self, instance, cls):
        """When an ``Instanceify`` instance is accessed as an attribute of
        another object, it will create the real (instance-ified) decorator,
        and replace itself on the instance with the real decorator.
        """

        if instance is None:
            return self.__func

        method    = functools.partial(self.__func, instance)
        decMethod = self.__realDecorator(method)

        setattr(instance, self.__func.__name__, decMethod)
        return functools.update_wrapper(decMethod, self.__func)
