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
import os.path as op
import sys
import importlib
import deprecation

import fsl.utils.notifier as notifier

# An annoying consequence of using
# a system-module name for our own
# module is that we can't import
# it directly (as it will attempt
# to import itself, i.e. this module).
#
# This is only necessary in Python 2.x
# (as python 3 disallows relative
# imports).
builtin_platform = importlib.import_module('platform')


log = logging.getLogger(__name__)


WX_UNKNOWN = 0
"""Identifier for the :attr:`Platform.wxFlavour` and
:attr:`Platform.wxPlatform` properties indicating an unknown/undetermined
flavour/platform.
"""


WX_PYTHON  = 1
"""Identifier for the :attr:`Platform.wxFlavour` property, indicating that
we are running standard wx Python.
"""


WX_PHOENIX = 2
"""Identifier for the :attr:`Platform.wxFlavour` property, indicating that we
are running wx Python/Phoenix.
"""


WX_MAC_COCOA = 1
"""Identifier for the :attr:`Platform.wxPlatform` property, indicating that we
are running the OSX cocoa wx build.
"""


WX_MAC_CARBON = 2
"""Identifier for the :attr:`Platform.wxPlatform` property, indicating that we
are running the OSX carbon wx build.
"""


WX_GTK = 3
"""Identifier for the :attr:`Platform.wxPlatform` property, indicating that we
are running the Linux/GTK wx build.
"""


@deprecation.deprecated(deprecated_in='1.2.2',
                        removed_in='2.0.0',
                        details='Use fsleyes_widgets.isalive instead')
def isWidgetAlive(widget):
    """Returns ``True`` if the given ``wx.Window`` object is "alive" (i.e.
    has not been destroyed), ``False`` otherwise. Works in both wxPython
    and wxPython/Phoenix.

    .. warning:: Don't try to test whether a ``wx.MenuItem`` has been
                 destroyed, as it will probably result in segmentation
                 faults. Check the parent ``wx.Menu`` instead.
    """

    import wx


    if platform.wxFlavour == platform.WX_PHOENIX:
        excType = RuntimeError
    elif platform.wxFlavour == platform.WX_PYTHON:
        excType = wx.PyDeadObjectError

    try:
        widget.GetParent()
        return True

    except excType:
        return False


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
       canHaveGui
       inSSHSession
       wxPlatform
       wxFlavour
       glVersion
       glRenderer
       glIsSoftwareRenderer
    """


    def __init__(self):
        """Create a ``Platform`` instance. """

        # For things which 'from fsl.utils.platform import platform',
        # these identifiers are available on the platform instance
        self.WX_UNKNOWN    = WX_UNKNOWN
        self.WX_PYTHON     = WX_PYTHON
        self.WX_PHOENIX    = WX_PHOENIX
        self.WX_MAC_COCOA  = WX_MAC_COCOA
        self.WX_MAC_CARBON = WX_MAC_CARBON
        self.WX_GTK        = WX_GTK
        self.isWidgetAlive = isWidgetAlive

        self.__inSSHSession = False
        self.__inVNCSession = False
        self.__glVersion    = None
        self.__glRenderer   = None
        self.__glIsSoftware = None
        self.__fslVersion   = None
        self.__fsldir       = None
        self.fsldir         = os.environ.get('FSLDIR', None)

        # Determine if a display is available. We do
        # this once at init (instead of on-demand in
        # the canHaveGui method) because calling the
        # IsDisplayAvailable function will cause the
        # application to steal focus under OSX!
        try:
            import wx
            self.__canHaveGui = wx.App.IsDisplayAvailable()
        except ImportError:
            log.warning('Could not import wx', exc_info=True)
            self.__canHaveGui = False

        # If one of the SSH_/VNC environment
        # variables is set, then we're probably
        # running over SSH/VNC.
        sshVars = ['SSH_CLIENT', 'SSH_TTY']
        vncVars = ['VNCDESKTOP', 'X2GO_SESSION', 'NXSESSIONID']

        self.__inSSHSession = any(s in os.environ for s in sshVars)
        self.__inVNCSession = any(v in os.environ for v in vncVars)


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
        try:
            import wx
            app = wx.GetApp()
            return (self.canHaveGui and
                    app is not None and
                    app.IsMainLoopRunning())

        except ImportError:
            return False


    @property
    def canHaveGui(self):
        """``True`` if it is possible to create a GUI, ``False`` otherwise. """
        return self.__canHaveGui


    @property
    def inSSHSession(self):
        """``True`` if this application is running over an SSH session,
        ``False`` otherwise.
        """
        return self.__inSSHSession


    @property
    def inVNCSession(self):
        """``True`` if this application is running over a VNC (or similar)
        session, ``False`` otherwise. Currently, the following remote desktop
        environments are detected:

          - VNC
          - x2go
          - NoMachine
        """
        return self.__inVNCSession


    @property
    def wxPlatform(self):
        """One of :data:`WX_UNKNOWN`, :data:`WX_MAC_COCOA`,
        :data:`WX_MAC_CARBON`, or :data:`WX_GTK`, indicating the wx platform.
        """

        if not self.canHaveGui:
            return WX_UNKNOWN

        import wx

        pi = [t.lower() for t in wx.PlatformInfo]

        if   any(['cocoa'  in p for p in pi]): plat = WX_MAC_COCOA
        elif any(['carbon' in p for p in pi]): plat = WX_MAC_CARBON
        elif any(['gtk'    in p for p in pi]): plat = WX_GTK
        else:                                  plat = WX_UNKNOWN

        if plat is WX_UNKNOWN:
            log.warning('Could not determine wx platform from '
                        'information: {}'.format(pi))

        return plat


    @property
    def wxFlavour(self):
        """One of :data:`WX_UNKNOWN`, :data:`WX_PYTHON` or :data:`WX_PHOENIX`,
        indicating the wx flavour.
        """

        if not self.canHaveGui:
            return WX_UNKNOWN

        import wx

        pi        = [t.lower() for t in wx.PlatformInfo]
        isPhoenix = False

        for tag in pi:
            if 'phoenix' in tag:
                isPhoenix = True
                break

        if isPhoenix: return WX_PHOENIX
        else:         return WX_PYTHON


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

        if value is not None:
            value = value.strip()

        if   value is None:        pass
        elif value == '':          value = None
        elif not op.exists(value): value = None
        elif not op.isdir(value):  value = None

        self.__fsldir = value

        if value is not None:
            os.environ['FSLDIR'] = value

            # Set the FSL version field if we can
            versionFile = op.join(value, 'etc', 'fslversion')

            if op.exists(versionFile):
                with open(versionFile, 'rt') as f:
                    self.__fslVersion = f.read().strip()

        self.notify(value=value)


    @property
    def fslVersion(self):
        """Returns the FSL version as a string, e.g. ``'5.0.9'``. Returns
        ``None`` if a FSL installation could not be found.
        """
        return self.__fslVersion


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

        value = value.lower()

        # There doesn't seem to be any quantitative
        # method for determining whether we are using
        # software-based rendering, so a hack is
        # necessary.
        self.__glIsSoftware = any((
            'software' in value,
            'chromium' in value,
        ))


    @property
    def glIsSoftwareRenderer(self):
        """Returns ``True`` if the OpenGL renderer is software based,
        ``False`` otherwise, or ``None`` if the renderer has not yet been set.

        .. note:: This check is based on heuristics, ans is not guaranteed to
                  be correct.
        """
        return self.__glIsSoftware


platform = Platform()
"""An instance of the :class:`Platform` class. Feel free to create your own
instance, but be aware that if you do so you will not be updated of changes
to the :attr:`Platform.fsldir` property.
"""
