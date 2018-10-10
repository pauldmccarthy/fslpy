#!/usr/bin/env python
#
# deprecated.py - Decorator for deprecating things.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :func:`deprecated` function, a simple decorator
for deprecating functions and methods.
"""



import functools as ft
import              inspect
import              warnings


_warned_cache = set()
"""Used by the :func:`deprecated` function to keep track of whether a warning
has already been emitted for the use of a deprecated item.
"""


def deprecated(vin=None, rin=None, msg=None):
    """Decorator to mark a function or method as deprecated. A
    ``DeprecationWarning`` is raised via the standard ``warnings`` module.

    :arg vin: Optional version - the warning message will mention that the
              function is deprecated from this version.

    :arg rin: Optional version - the warning message will mention that the
              function will be removed in this version.

    :arg msg: Optional message to use in the warning.
    """


    if vin is not None and rin is not None:
        msgfmt = '{{name}} is deprecated from version {vin} and will be ' \
                 'removed in {rin}.'.format(vin=vin, rin=rin)
    elif vin is not None:
        msgfmt = '{{name}} is deprecated from version {vin}.'.format(vin=vin)
    elif rin is not None:
        msgfmt = '{{name}} is deprecated and will be removed in ' \
                 '{rin}.'.format(rin=rin)
    else:
        msgfmt = '{{name}} is deprecated.'

    if msg is not None:
        msgfmt = msgfmt + ' ' + msg

    def wrapper(thing):
        name = thing.__name__

        def decorator(*args, **kwargs):

            frame = inspect.stack()[1]
            ident = '{}:{}'.format(frame.filename, frame.lineno)

            if ident not in _warned_cache:
                warnings.warn(msgfmt.format(name=name),
                              category=DeprecationWarning,
                              stacklevel=2)
                _warned_cache.add(ident)

            return thing(*args, **kwargs)
        return ft.update_wrapper(decorator, thing)

    return wrapper
