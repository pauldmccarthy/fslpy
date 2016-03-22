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

.. note:: The ``Platform`` class only contains information which is not
          already accessible from the built-in ``platform`` module
          (e.g. operating system information), or the ``six`` module (e.g.
          python 2 vs 3).
"""


import logging

import os

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

    .. autosummary::

       fsldir
       haveGui
       wxBuild
       wxFlavour
    """

    
    def __init__(self):
        """Create a ``Platform`` instance. """
        

        self.__fsldir     = os.environ.get('FSLDIR', None)
        self.__haveGui    = False
        self.__wxFlavour  = None
        self.__wxPlatform = None

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

            if   any(['cocoa'  in p for p in pi]): build = WX_MAC_COCOA
            elif any(['carbon' in p for p in pi]): build = WX_MAC_CARBON
            elif any(['gtk'    in p for p in pi]): build = WX_GTK
            else:                                  build = None

            self.__build = build

            if self.__build is None:
                log.warning('Could not determine wx build from '
                            'platform information: {}'.format(pi))


    @property
    def haveGui(self):
        """``True`` if we are running with a GUI, ``False`` otherwise. """
        return self.__haveGui

    
    @property
    def wxBuild(self):
        """One of :data:`WX_MAC_COCOA`, :data:`WX_MAC_CARBON`, or
        :data:`WX_GTK`, indicating the wx build.
        """
        return self.__wxBuild

    
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


platform = Platform()
"""An instance of the :class:`Platform` class. Feel free to create your own
instance, but be aware that if you do so you will not be updated of changes
to the :attr:`Platform.fsldir` property.
"""
