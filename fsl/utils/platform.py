#!/usr/bin/env python
#
# platform.py - Platform information
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Platform` class, which is a container
of information about the current platform we are running on. A single
``Platform`` instance is created when this module is first imported, and
is available as a module attribute called :attr:`platform`.
"""


import logging

import os
import sys
import platform as builtin_platform

import fsl.utils.notifier as notifier


log = logging.getLogger(__name__)


WX_PYTHON  = 1
"""Identifier for the :attr:`Platform.wxFlavour` property, indicating that
we are running standard wx Python.
"""


WX_PHOENIX = 2
"""Identifier for the :attr:`Platform.wxFlavour` property, indicating that we 
are running wx Python/Phoenix.
"""


WX_MAC_COCOA = 1
"""Identifier for the :attr:`Platform.wxFlavour` property, indicating that we
are running the OSX cocoa wx build.
"""


WX_MAC_CARBON = 2
"""Identifier for the :attr:`Platform.wxFlavour` property, indicating that we
are running the OSX carbon wx build.
"""


WX_GTK = 3
"""Identifier for the :attr:`Platform.wxFlavour` property, indicating that we
are running the Linux/GTK wx build.
"""


class Platform(notifier.Notifier):
    """The ``Platform`` class contains a handful of properties which contain
    information about the platform we are running on.

    .. note:: The values of the :attr:`glVersion` and :attr:`glRenderer`
              properties are not automatically set - they will only contain
              a value if one is assigned to them. *FSLeyes* does this during
              startup, in the :func:`fsleyes.gl.bootstrap` function.

    .. autosummary::

       os
       frozen
       fsldir
       haveGui
       wxPlatform
       wxFlavour
       glVersion
       glRenderer
    """

    
    def __init__(self):
        """Create a ``Platform`` instance. """

        # For things which 'from fsl.utils.platform import platform',
        # these identifiers are available on the platform instance
        self.WX_PYTHON     = WX_PYTHON
        self.WX_PHOENIX    = WX_PHOENIX
        self.WX_MAC_COCOA  = WX_MAC_COCOA
        self.WX_MAC_CARBON = WX_MAC_CARBON
        self.WX_GTK        = WX_GTK

        self.__fsldir     = os.environ.get('FSLDIR', None)
        self.__haveGui    = False
        self.__wxFlavour  = None
        self.__wxPlatform = None
        self.__glVersion  = None
        self.__glRenderer = None

        try:
            import wx
            self.__haveGui = True

        except ImportError:
            pass

        if self.__haveGui:

            pi        = [t.lower() for t in wx.PlatformInfo]
            isPhoenix = False

            for tag in pi:
                if 'phoenix' in tag: 
                    isPhoenix = True
                    break

            if isPhoenix: self.__wxFlavour = WX_PHOENIX
            else:         self.__wxFlavour = WX_PYTHON

            if   any(['cocoa'  in p for p in pi]): platform = WX_MAC_COCOA
            elif any(['carbon' in p for p in pi]): platform = WX_MAC_CARBON
            elif any(['gtk'    in p for p in pi]): platform = WX_GTK
            else:                                  platform = None

            self.__wxPlatform = platform

            if self.__wxPlatform is None:
                log.warning('Could not determine wx platform from '
                            'information: {}'.format(pi))

                
    @property
    def os(self):
        """The operating system name. Whatever is returned by the built-in
        ``platform.system`` function.
        """
        return builtin_platform.system()

    
    @property
    def frozen(self):
        """``True`` if we are running in a compiled/frozen application,
        ``False`` otherwise.
        """
        return getattr(sys, 'frozen', False)


    @property
    def haveGui(self):
        """``True`` if we are running with a GUI, ``False`` otherwise. """
        return self.__haveGui

    
    @property
    def wxPlatform(self):
        """One of :data:`WX_MAC_COCOA`, :data:`WX_MAC_CARBON`, or
        :data:`WX_GTK`, indicating the wx platform.
        """
        return self.__wxPlatform

    
    @property
    def wxFlavour(self):
        """One of :data:`WX_PYTHON` or :data:`WX_PHOENIX`, indicating the wx
        flavour.
        """
        return self.__wxFlavour


    @property
    def fsldir(self):
        """The FSL installation location.

        .. note:: The ``fsldir`` property can be updated - when it is changed,
                  any registered listeners are notified via the
                  :class:`.Notifier` interface.
        """
        return self.__fsldir


    @fsldir.setter
    def fsldir(self, value):
        """Changes the value of the :attr:`fsldir` property, and notifies any
        registered listeners.
        """
        self.__fsldir = value
        self.notify()

        
    @property
    def glVersion(self):
        """Returns the available OpenGL version, or ``None`` if it has not
        been set.
        """
        return self.__glVersion

    
    @glVersion.setter
    def glVersion(self, value):
        """Set the available OpenGL version. """
        self.__glVersion = value


    @property
    def glRenderer(self):
        """Returns the available OpenGL renderer, or ``None`` if it has not
        been set.
        """
        return self.__glRenderer


    @glRenderer.setter
    def glRenderer(self, value):
        """Set the available OpenGL renderer. """
        self.__glRenderer = value


platform = Platform()
"""An instance of the :class:`Platform` class. Feel free to create your own
instance, but be aware that if you do so you will not be updated of changes
to the :attr:`Platform.fsldir` property.
"""
