#!/usr/bin/env python
#
# settings.py - Persistent application settings.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
import logging

log = logging.getLogger(__name__)


def read(name, default=None):

    try:    import wx
    except: return None

    if wx.GetApp() is None:
        return None

    config = wx.Config('uk.ac.ox.fmrib.fslpy')
    
    value = config.Read(name)

    log.debug('Read {}: {}'.format(
        name, '(no value)' if value == '' else value))

    if value == '': return default
    else:           return value


def write(name, value):

    try:    import wx
    except: return

    if wx.GetApp() is None:
        return 

    value  = str(value)
    config = wx.Config('uk.ac.ox.fmrib.fslpy')

    log.debug('Writing {}: {}'.format(name, value))

    config.Write(name, value)
