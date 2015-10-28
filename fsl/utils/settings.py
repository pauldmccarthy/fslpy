#!/usr/bin/env python
#
# settings.py - Persistent application settings.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides a simple API to :func:`read` and :func:`write`
persistent application settings.

 .. note:: Currently the configuration management API provided by :mod:`wx`
           (http://docs.wxwidgets.org/trunk/overview_config.html) is used for
           storing application settings.  This means that it is not possible
           to persist settings from a non-GUI application.

           But that's the whole point of this module, to abstract away the
           underlying persistence method. In the future I will replace
           ``wx.Config`` with something that does not rely upon the presence
           of ``wx``.
"""


import logging


log = logging.getLogger(__name__)


_CONFIG_ID = 'uk.ac.ox.fmrib.fslpy'
"""The configuration identifier passed to ``wx.Config``. This identifier
should be the same as the identifier given to the OSX application bundle
(see https://git.fmrib.ox.ac.uk/paulmc/fslpy_build).
"""


def read(name, default=None):
    """Reads a setting with the given ``name``, return ``default`` if
    there is no setting called ``name``.
    """

    try:    import wx
    except: return None

    if wx.GetApp() is None:
        return None

    config = wx.Config(_CONFIG_ID)
    
    value = config.Read(name)

    log.debug('Read {}: {}'.format(
        name, '(no value)' if value == '' else value))

    if value == '': return default
    else:           return value


def write(name, value):
    """Writes a setting with the given ``name`` and ``value``.""" 

    try:    import wx
    except: return

    if wx.GetApp() is None:
        return 

    value  = str(value)
    config = wx.Config(_CONFIG_ID)

    log.debug('Writing {}: {}'.format(name, value))

    config.Write(name, value)
