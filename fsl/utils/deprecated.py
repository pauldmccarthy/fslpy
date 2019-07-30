#!/usr/bin/env python
#
# deprecated.py - Decorator for deprecating things.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :func:`deprecated` function, a simple decorator
for deprecating functions and methods.

The :func:`warn` function can also be called directly, to emit a
``DeprecationWarning``
"""


import functools as ft
import              inspect
import              warnings


_warned_cache = set()
"""Used by to keep track of whether a warning has already been emitted for the
use of a deprecated item.
"""


def resetWarningCache():
    """Clears the internal warning cache, so that the same line of code
    may emit another deprecation warning.
    """
    _warned_cache.clear()


def _buildMessageFormat(vin=None, rin=None, msg=None):
    """Builds a deprecation warning message from the arguments.

    :arg vin: Optional version - the warning message will mention that the
              function is deprecated from this version.

    :arg rin: Optional version - the warning message will mention that the
              function will be removed in this version.

    :arg msg: Optional message to use in the warning.

    :returns: A format string which needs to be formatted with a ``{name}``.
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

    return msgfmt


def _buildWarningSourceIdentity(stacklevel=2):
    """Creates a string to be used as an identifier for the calling code.

    :arg stacklevel: How far up the calling stack the calling code is.
    :returns:        A string which can be used as an identifier for the
                     calling code.
    """
    frame = inspect.stack()[stacklevel]
    ident = '{}:{}'.format(frame.filename, frame.lineno)
    return ident


def warn(name, vin=None, rin=None, msg=None, stacklevel=1):
    """Emit a deprecation warning.

    :arg name:       Name of the thing (class, function, module, etc) that is
                     deprecated.

    :arg vin:        Optional version - the warning message will mention that
                     the function is deprecated from this version.

    :arg rin:        Optional version - the warning message will mention that
                     the function will be removed in this version.

    :arg msg:        Optional message to use in the warning.

    :arg stacklevel: How far up the stack the calling code is.
    """

    msgfmt = _buildMessageFormat(vin=vin, rin=rin, msg=msg)
    ident  = _buildWarningSourceIdentity()
    if ident not in _warned_cache:
        warnings.warn(msgfmt.format(name=name),
                      category=DeprecationWarning,
                      stacklevel=stacklevel + 1)
        _warned_cache.add(ident)


def deprecated(vin=None, rin=None, msg=None):
    """Decorator to mark a function or method as deprecated. A
    ``DeprecationWarning`` is raised via the standard ``warnings`` module.

    :arg vin: Optional version - the warning message will mention that the
              function is deprecated from this version.

    :arg rin: Optional version - the warning message will mention that the
              function will be removed in this version.

    :arg msg: Optional message to use in the warning.
    """
    def wrapper(thing):
        def decorator(*args, **kwargs):
            warn(thing.__name__, vin=vin, rin=rin, msg=msg, stacklevel=2)
            return thing(*args, **kwargs)
        return ft.update_wrapper(decorator, thing)
    return wrapper
