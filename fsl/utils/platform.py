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

import fsl.utils.notifier   as notifier
import fsl.utils.deprecated as deprecated

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
       fsldevdir
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

        # initialise fsldir - see fsldir.setter
        self.fsldir = self.fsldir

        # These are all initialised on first access
        self.__glVersion    = None
        self.__glRenderer   = None
        self.__glIsSoftware = None
        self.__fslVersion   = None
        self.__canHaveGui   = None

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
    @deprecated.deprecated(
        '3.6.0',
        '4.0.0',
        'Equivalent functionality is available in fsleyes-widgets.')
    def frozen(self):
        """``True`` if we are running in a compiled/frozen application,
        ``False`` otherwise.
        """
        return getattr(sys, 'frozen', False)


    @property
    @deprecated.deprecated(
        '3.6.0',
        '4.0.0',
        'Equivalent functionality is available in fsleyes-widgets.')
    def haveGui(self):
        """``True`` if we are running with a GUI, ``False`` otherwise.

        This currently equates to testing whether a display is available
        (see :meth:`canHaveGui`) and whether a ``wx.App`` exists. It
        previously also tested whether an event loop was running, but this
        is not compatible with execution from IPython/Jupyter notebook, where
        the event loop is called periodically, and so is not always running.
        """
        try:
            import wx  # pylint: disable=import-outside-toplevel
            app = wx.GetApp()

            # TODO Previously this conditional
            #      also used app.IsMainLoopRunning()
            #      to check that the wx main loop
            #      was running. But this doesn't
            #      suit situations where a non-main
            #      event loop is running, or where
            #      the mainloop is periodically
            #      started and stopped (e.g. when
            #      the event loop is being run by
            #      IPython).
            #
            #      In c++ wx, there is the
            #      wx.App.UsesEventLoop method, but
            #      this is not presently exposed to
            #      Python code (and wouldn't help
            #      to detect the loop start/stop
            #      scenario).
            #
            #      So this constraint has been
            #      (hopefully) temporarily relaxed
            #      until I can think of a better
            #      solution.
            return (self.canHaveGui and
                    app is not None)

        except ImportError:
            return False


    @property
    @deprecated.deprecated(
        '3.6.0',
        '4.0.0',
        'Equivalent functionality is available in fsleyes-widgets.')
    def canHaveGui(self):
        """``True`` if it is possible to create a GUI, ``False`` otherwise. """

        # Determine if a display is available. Note that
        # calling the IsDisplayAvailable function will
        # cause the application to steal focus under OSX!
        if self.__canHaveGui is None:
            try:
                import wx  # pylint: disable=import-outside-toplevel
                self.__canHaveGui = wx.App.IsDisplayAvailable()
            except ImportError:
                self.__canHaveGui = False

        return self.__canHaveGui


    @property
    @deprecated.deprecated(
        '3.6.0',
        '4.0.0',
        'Equivalent functionality is available in fsleyes-widgets.')
    def inSSHSession(self):
        """``True`` if this application is running over an SSH session,
        ``False`` otherwise.
        """
        return self.__inSSHSession


    @property
    @deprecated.deprecated(
        '3.6.0',
        '4.0.0',
        'Equivalent functionality is available in fsleyes-widgets.')
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
    @deprecated.deprecated(
        '3.6.0',
        '4.0.0',
        'Equivalent functionality is available in fsleyes-widgets.')
    def wxPlatform(self):
        """One of :data:`WX_UNKNOWN`, :data:`WX_MAC_COCOA`,
        :data:`WX_MAC_CARBON`, or :data:`WX_GTK`, indicating the wx platform.
        """

        if not self.canHaveGui:
            return WX_UNKNOWN

        import wx  # pylint: disable=import-outside-toplevel

        pi = [t.lower() for t in wx.PlatformInfo]

        if   any('cocoa'  in p for p in pi): plat = WX_MAC_COCOA
        elif any('carbon' in p for p in pi): plat = WX_MAC_CARBON
        elif any('gtk'    in p for p in pi): plat = WX_GTK
        else:                                plat = WX_UNKNOWN

        if plat is WX_UNKNOWN:
            log.warning('Could not determine wx platform from '
                        'information: {}'.format(pi))

        return plat


    @property
    @deprecated.deprecated(
        '3.6.0',
        '4.0.0',
        'Equivalent functionality is available in fsleyes-widgets.')
    def wxFlavour(self):
        """One of :data:`WX_UNKNOWN`, :data:`WX_PYTHON` or :data:`WX_PHOENIX`,
        indicating the wx flavour.
        """

        if not self.canHaveGui:
            return WX_UNKNOWN

        import wx  # pylint: disable=import-outside-toplevel

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
        return os.environ.get('FSLDIR', None)


    @property
    def fsldevdir(self):
        """The FSL development directory location. """
        return os.environ.get('FSLDEVDIR', None)


    @property
    def fslwsl(self):
        """Boolean flag indicating whether FSL is installed in Windows
        Subsystem for Linux
        """
        return self.fsldir is not None and self.fsldir.startswith("\\\\wsl$")


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

        if value is None:
            os.environ.pop('FSLDIR', None)
        else:
            os.environ['FSLDIR'] = value

            # Set the FSL version field if we can
            versionFile = op.join(value, 'etc', 'fslversion')

            if op.exists(versionFile):
                with open(versionFile, 'rt') as f:
                    # split string at colon for new hash style versions
                    # first object in list is the non-hashed version string
                    # (e.g. 6.0.2) if no ":hash:" then standard FSL version
                    # string is still returned
                    self.__fslVersion = f.read().strip().split(":")[0]

        self.notify(value=value)


    @fsldevdir.setter
    def fsldevdir(self, value):
        """Changes the value of the :attr:`fsldevdir` property, and notifies
        any registered listeners.
        """

        if value is not None:
            value = value.strip()

        if   value is None:        pass
        elif value == '':          value = None
        elif not op.exists(value): value = None
        elif not op.isdir(value):  value = None

        if value is None:
            os.environ.pop('FSLDEVDIR', None)
        else:
            os.environ['FSLDEVDIR'] = value


    @property
    def fslVersion(self):
        """Returns the FSL version as a string, e.g. ``'5.0.9'``. Returns
        ``None`` if a FSL installation could not be found.
        """
        return self.__fslVersion


    @property
    @deprecated.deprecated(
        '3.6.0',
        '4.0.0',
        'Equivalent functionality is available in fsleyes-widgets.')
    def glVersion(self):
        """Returns the available OpenGL version, or ``None`` if it has not
        been set.
        """
        return self.__glVersion


    @glVersion.setter
    @deprecated.deprecated(
        '3.6.0',
        '4.0.0',
        'Equivalent functionality is available in fsleyes-widgets.')
    def glVersion(self, value):
        """Set the available OpenGL version. """
        self.__glVersion = value


    @property
    @deprecated.deprecated(
        '3.6.0',
        '4.0.0',
        'Equivalent functionality is available in fsleyes-widgets.')
    def glRenderer(self):
        """Returns the available OpenGL renderer, or ``None`` if it has not
        been set.
        """
        return self.__glRenderer


    @glRenderer.setter
    @deprecated.deprecated(
        '3.6.0',
        '4.0.0',
        'Equivalent functionality is available in fsleyes-widgets.')
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
    @deprecated.deprecated(
        '3.6.0',
        '4.0.0',
        'Equivalent functionality is available in fsleyes-widgets.')
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
