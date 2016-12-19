#!/usr/bin/env python
#
# settings.py - Persistent application settings.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides a simple API to :func:`read`, :func:`write`, 
:func:`delete`, and :func:`clear` persistent application settings.

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

from .platform import platform as fslplatform


log = logging.getLogger(__name__)


_CONFIG_ID = 'uk.ac.ox.fmrib.fslpy'
"""The configuration identifier passed to ``wx.Config``. This identifier
should be the same as the identifier given to the OSX application bundle
(see https://git.fmrib.ox.ac.uk/paulmc/fslpy_build).
"""


def strToBool(s):
    """Currently the ``settings`` module is not type aware, so boolean
    values are saved as strings ``'True'`` or ``'False'``. This makes
    conversion back to boolean a bit annoying, as ``'False'`` evaluates
    to ``True``.

    This function may be used for a more sensible `str` -> `bool`
    conversion

    .. note:: In the future, the ``settings`` module will hopefully be 
              type-aware, so use of this function will no longer be necessary.
    """
    s = str(s).lower()
    if   s == 'true':  return True
    elif s == 'false': return False
    else:              return bool(s) 


def read(name, default=None):
    """Reads a setting with the given ``name``, return ``default`` if
    there is no setting called ``name``.
    """

    if not fslplatform.haveGui:
        return default

    import wx

    config = wx.Config(_CONFIG_ID)
    
    value = config.Read(name)

    
    log.debug('Read {}/{}: {}'.format(
        _CONFIG_ID,
        name,
        '(no value)' if value == '' else value))

    if value == '': return default
    else:           return value


def write(name, value):
    """Writes a setting with the given ``name`` and ``value``.""" 

    if not fslplatform.haveGui:
        return 

    import wx

    value  = str(value)
    config = wx.Config(_CONFIG_ID)

    log.debug('Writing {}/{}: {}'.format(_CONFIG_ID, name, value))

    config.Write(name, value)


def delete(name):
    """Delete the setting with the given ``name``. """

    if not fslplatform.haveGui:
        return 

    import wx 

    config = wx.Config(_CONFIG_ID)

    log.debug('Deleting {}/{}'.format(_CONFIG_ID, name))

    config.DeleteEntry(name)


def clear():
    """Delete all settings. """
    
    if not fslplatform.haveGui:
        return 

    import wx 

    config = wx.Config(_CONFIG_ID)

    log.debug('Clearing all settings in {}'.format(_CONFIG_ID))

    config.DeleteAll()
