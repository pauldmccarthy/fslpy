#!/usr/bin/env python
#
# profilemap.py - This module defines couple of dictionaries which define
# temporary mouse/keyboard interaction modes, and alternate mode handlers
# for the profiles contained in the profiles package.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

from collections import OrderedDict

import wx

from fsl.fslview.profiles.orthoviewprofile import OrthoViewProfile
from fsl.fslview.profiles.orthoeditprofile import OrthoEditProfile


tempModeMap = {

    # Command/CTRL puts the
    # user in zoom mode
    OrthoViewProfile : OrderedDict((
        (('nav', wx.WXK_CONTROL), 'zoom'),
        (('pan', wx.WXK_CONTROL), 'zoom'))),

    # Command/CTRL puts the user in zoom mode,
    # Shift puts the user in navigate mode,
    # and alt switches between select/deselect
    OrthoEditProfile : OrderedDict((
        (('sel',    wx.WXK_ALT),     'desel'),
        (('selint', wx.WXK_ALT),     'desel'),
        (('desel',  wx.WXK_ALT),     'sel'),
        
        (('sel',    wx.WXK_SHIFT),   'nav'),
        (('desel',  wx.WXK_SHIFT),   'nav'),
        (('selint', wx.WXK_SHIFT),   'nav'),

        (('sel',    wx.WXK_CONTROL), 'zoom'),
        (('desel',  wx.WXK_CONTROL), 'zoom'),
        (('selint', wx.WXK_CONTROL), 'zoom')))
}

altHandlerMap = {

    OrthoViewProfile : OrderedDict((
        
        # in navigate mode, the left mouse button
        # navigates, the right mouse button draws
        # a zoom rectangle, and the middle button
        # pans 
        (('nav',  'LeftMouseDown'),   ('nav',  'LeftMouseDrag')),
        (('nav',  'MiddleMouseDown'), ('pan',  'LeftMouseDown')),
        (('nav',  'MiddleMouseDrag'), ('pan',  'LeftMouseDrag')),
        (('nav',  'RightMouseDown'),  ('zoom', 'LeftMouseDown')),
        (('nav',  'RightMouseDrag'),  ('zoom', 'LeftMouseDrag')),
        (('nav',  'RightMouseUp'),    ('zoom', 'LeftMouseUp')),

        # In pan mode, the left mouse button pans,
        # and right mouse button navigates
        (('pan',  'LeftMouseDown'),   ('pan',  'LeftMouseDrag')),
        (('pan',  'RightMouseDown'),  ('nav',  'LeftMouseDown')),
        (('pan',  'RightMouseDrag'),  ('nav',  'LeftMouseDrag')),

        # In zoom mode, the left mouse button
        # draws a zoom rectangle, the right mouse
        # button navigates, and the middle mouse
        # button pans 
        (('zoom', 'LeftMouseDown'),   ('zoom', 'LeftMouseDrag')),
        (('zoom', 'RightMouseDown'),  ('nav',  'LeftMouseDown')),
        (('zoom', 'RightMouseDrag'),  ('nav',  'LeftMouseDrag')),
        (('zoom', 'MiddleMouseDrag'), ('pan',  'LeftMouseDrag')))),

    OrthoEditProfile : OrderedDict((
        (('sel',    'RightMouseDown'),  ('desel',  'LeftMouseDown')),
        (('sel',    'RightMouseDrag'),  ('desel',  'LeftMouseDrag')),
        (('sel',    'RightMouseUp'),    ('desel',  'LeftMouseUp')),
        
        (('sel',    'MiddleMouseDown'), ('pan',    'LeftMouseDown')),
        (('sel',    'MiddleMouseDrag'), ('pan',    'LeftMouseDrag')),
        (('desel',  'MiddleMouseDrag'), ('pan',    'LeftMouseDrag')),
        (('selint', 'MiddleMouseDown'), ('pan',    'LeftMouseDown')),
        (('selint', 'MiddleMouseDrag'), ('pan',    'LeftMouseDrag')),
         
        (('desel',  'MouseMove'),       ('sel',    'MouseMove')),
        
        (('selint', 'RightMouseDown'),  ('desel',  'LeftMouseDown')),
        (('selint', 'RightMouseDrag'),  ('desel',  'LeftMouseDrag')),
        (('selint', 'RightMouseUp'),    ('desel',  'LeftMouseUp'))))
}
