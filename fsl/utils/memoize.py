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

    memoizeMD5
"""

import hashlib


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

        for arg in args:
            hashobj.update(str(arg))

        digest = hashobj.hexdigest()
        cached = cache.get(digest)

        if cached is not None:
            return cached

        result = func(*args, **kwargs)

        cache[digest] = result

        return result

    return wrapper
