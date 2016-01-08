#!/usr/bin/env python
#
# async.py - Run a function in a separate thread.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides a single function, :func:`run`, which simply
runs a function in a separate thread.

This doesn't seem like a worthy task to have a module of its own, but the
:func:`run` function additionally provides the ability to schedule another
function to run on the ``wx.MainLoop`` when the original function has
completed.

This therefore gives us a simple way to run a computationally intensitve task
off the main GUI thread (preventing the GUI from locking up), and to perform
some clean up/refresh afterwards.
"""


import logging
import threading


log = logging.getLogger(__name__)


def run(task, onFinish=None, name=None):
    """Run the given ``task`` in a separate thread.

    :arg task:     The function to run. Must accept no arguments.

    :arg onFinish: An optional function to schedule on the ``wx.MainLoop``
                   once the ``task`` has finished. 

    :arg name:     An optional name to use for this task in log statements.
    """

    if name is None: name = 'async task'

    def wrapper():

        log.debug('Running task "{}"...'.format(name))
        task()

        log.debug('Task "{}" finished'.format(name))

        if onFinish is not None:
            import wx

            log.debug('Scheduling task "{}" finish handler '
                      'on wx.MainLoop'.format(name))

            wx.CallAfter(onFinish)

    thread = threading.Thread(target=wrapper)
    thread.start()

    return thread
