#!/usr/bin/env python
#
# status.py - A simple interface for displaying messages.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This is a little module which provides an interface for displaying a
message, or status update, to the user.  The ``status`` module provides the
following functions:

 .. autosummary::
    :nosignatures:

    setTarget
    update
    clear


The :func:`update` function may be used to display a message. By default, the
message is simply logged (via the ``logging`` module). However, if a status
target has been set via the :func:`setTarget` function, the message is also
passed to this target. 
"""


import            logging
import            inspect
import os.path as op

log = logging.getLogger(__name__)


statusUpdateTarget = None
"""A reference to the status update target - this is ``None`` by default, and
can be set via :func:`setTarget`.
"""


def setTarget(target):
    """Set a target function to receive status updates. The ``target`` must
    be a function which accepts a string as its sole parameter.
    """
    global statusUpdateTarget
    statusUpdateTarget = target


def update(message):
    """Display a status update to the user. The message is logged and,
    if a status update target has been set, passed to the target.
    """

    global statusUpdateTarget

    if log.getEffectiveLevel() == logging.DEBUG:
        
        frame   = inspect.stack()[1]
        module  = frame[1]
        linenum = frame[2]
        module  = op.basename(module)

        log.debug('[{}:{}] {}'.format(module, linenum, message))

    if statusUpdateTarget is None:
        return
        
    statusUpdateTarget(message)


def clear():
    """Clear the status. If a status update target has been set, it is passed
    the empty string.
    """ 
    if statusUpdateTarget is None:
        return
        
    statusUpdateTarget('') 
