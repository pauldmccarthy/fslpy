#!/usr/bin/env python
#
# webpage.py - Convenience functions for opening a URL in a web browser.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Convenience functions for opening a URL in a web browser."""

import os
import webbrowser

import wx


def openPage(url):
    """Opens the given URL in the system-default web browser."""
    webbrowser.open(url)

    
def openFSLHelp(toolName):
    """Attempts to open the FSL help documentation for the given FSL tool.
    If the ``$FSLDIR`` environment variable is not set, pops up a warning
    message instead.
    """

    fsldir = os.environ.get('FSLDIR', None)
    url    = 'file://{}/doc/redirects/{}.html'.format(fsldir, toolName)

    if fsldir is not None:
        openPage(url)

    else:

        msg = 'The FSLDIR environment variable is not set - I don\'t '\
            'know where to find the FSL documentation.'

        wx.MessageDialog(
            None,
            message=msg,
            style=wx.OK | wx.ICON_ERROR).ShowModal()
