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

    config = wx.Config('fslview')
    
    value = config.Read(name)

    if value == '': return default
    else:           return value


def write(name, value):

    try:    import wx
    except: return None    

    value  = str(value)
    config = wx.Config('fslview')

    log.debug('Saving {}: {}'.format(name, value))

    config.Write(name, value)
