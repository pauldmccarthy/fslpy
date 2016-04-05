#!/usr/bin/env python
#
# webpage.py - Convenience functions for opening a URL in a web browser.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides convenience functions for opening a URL in a web
browser.

The following functions are provided:

.. autosummary::
   :nosignatures:

   fileToUrl
   openPage
   openFile
   localHelpUrl
   openLocalHelp
"""

import            os
import os.path as op
import            webbrowser


def fileToUrl(fileName):
    """Converts a file path to a URL. """
    
    import urlparse
    import urllib
    return urlparse.urljoin(
        'file:', urllib.pathname2url(fileName))



def openPage(url):
    """Opens the given URL in the system-default web browser."""
    webbrowser.open(url)


def openFile(fileName):
    """Opens the given file in the system-default web browser."""
    openPage(fileToUrl(fileName))


def localHelpUrl(toolName):
    """Checks the ``$FSLDIR`` to see if a local help page exists for the
    FSL tool with the specified name.
    """
    fsldir = os.environ.get('FSLDIR', None)

    if fsldir is None:
        return None

    toolName = toolName.lower()
    localUrl = op.join(fsldir, 'doc', 'redirects', '{}.html'.format(toolName))

    if op.exists(localUrl):
        return fileToUrl(localUrl)

    return None


def openLocalHelp(toolName):
    """Attempts to open the locally hosted FSL help documentation
    for the given FSL tool. If there is no help page for the
    given tool, attempts to open the FSL wiki.
    """

    localUrl = localHelpUrl(toolName)

    if localUrl is None:
        localUrl = "http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/"

    openPage(localUrl)
