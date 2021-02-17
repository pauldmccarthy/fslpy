#!/usr/bin/env python
#
# settings.py - Persistent application settings.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions for storing and retrieving persistent
configuration settings and data files.

The :func:`initialise` function must be called to initialise the module. Then,
the following functions can be called at the module-level:

.. autosummary::
   :nosignatures:

   Settings.read
   Settings.write
   Settings.delete
   Settings.readFile
   Settings.writeFile
   Settings.deleteFile
   Settings.filePath
   Settings.readAll
   Settings.listFiles
   Settings.clear


Some functions are also available to replace the module-level :class:`Settings`
instance:

.. autosummary::
   :nosignatures:

   set
   use


These functions will have no effect before :func:`initialise` is called.

Two types of configuration data are available:

  - Key-value pairs - access these via the ``read``, ``write`` and ``delete``
    functions. These are stored in a single file, via ``pickle``. Anything
    that can be pickled can be stored.

  - Separate files, either text or binary. Access these via the ``readFile``,
    ``writeFile``, and ``deleteFile`` functions.

Both of the above data types will be stored in a configuration directory.
The location of this directory differs from platform to platform, but is
likely to be either  `~/.fslpy/` or `~/.config/fslpy/`.
"""


from __future__ import absolute_import

import            os
import os.path as op
import            sys
import            copy
import            atexit
import            shutil
import            pickle
import            logging
import            fnmatch
import            tempfile
import            platform
import            contextlib


log = logging.getLogger(__name__)


_CONFIG_ID = 'fslpy'
"""The default configuration identifier, used as the directory name for
storing configuration files.
"""


def set(settings):
    """Set the module-level :class:`Settings` instance. """
    mod            = sys.modules[__name__]
    mod.settings   = settings
    mod.read       = settings.read
    mod.write      = settings.write
    mod.delete     = settings.delete
    mod.readFile   = settings.readFile
    mod.writeFile  = settings.writeFile
    mod.deleteFile = settings.deleteFile
    mod.filePath   = settings.filePath
    mod.readAll    = settings.readAll
    mod.listFiles  = settings.listFiles
    mod.clear      = settings.clear


def initialise(*args, **kwargs):
    """Initialise the ``settings`` module. This function creates a
    :class:`Settings` instance, and enables the module-level
    functions. All settings are passed through to :meth:`Settings.__init__`.
    """
    set(Settings(*args, **kwargs))


@contextlib.contextmanager
def use(settings):
    """Temporarily replace the module-level :class:`Settings` object
    with the given one.
    """

    mod = sys.modules[__name__]
    old = getattr(mod, 'settings', None)

    try:
        set(settings)
        yield
    finally:
        if old is not None:
            set(old)


# These are all overwritten by
# the initialise function.
def read(name, default=None):
    return default
def write(*args, **kwargs):
    pass
def delete(*args, **kwargs):
    pass
def readFile(*args, **kwargs):
    pass
@contextlib.contextmanager
def writeFile(*args, **kwargs):
    yield
def deleteFile(*args, **kwargs):
    pass
def filePath(*args, **kwargs):
    pass
def readAll(*args, **kwarg):
    return {}
def listFiles(*args, **kwarg):
    return []
def clear(*args, **kwarg):
    pass


class Settings(object):
    """The ``Settings`` class contains all of the logic provided by the
    ``settings`` module.  It is not meant to be instantiated directly
    (although you may do so if you wish).
    """


    def __init__(self, cfgid=_CONFIG_ID, cfgdir=None, writeOnExit=True):
        """Create a ``Settings`` instance.

        :arg cfgid:       Configuration ID, used as the name of the
                          configuration directory.

        :arg cfgdir:      Store configuration settings in this directory,
                          instead of the default.

        :arg writeOnExit: If ``True`` (the default), an ``atexit`` function
                          is registered, which calls :meth:`writeConfigFile`.
        """

        if cfgdir is None:
            cfgdir = self.__getConfigDir(cfgid)

        self.__configID  = cfgid
        self.__configDir = cfgdir
        self.__config    = self.__readConfigFile()

        if writeOnExit:
            atexit.register(self.writeConfigFile)


    @property
    def configID(self):
        """Returns the configuration identifier. """
        return self.__configID


    @property
    def configDir(self):
        """Returns the location of the configuration directory. """
        return self.__configDir


    def read(self, name, default=None):
        """Reads a setting with the given ``name``, return ``default`` if
        there is no setting called ``name``.
        """

        log.debug('Reading {}/{}'.format(self.__configID, name))
        return self.__config.get(name, default)


    def write(self, name, value):
        """Writes the given ``value`` to the given file ``path``. """

        log.debug('Writing {}/{}: {}'.format(self.__configID, name, value))
        self.__config[name] = value


    def delete(self, name):
        """Delete the setting with the given ``name``. """

        log.debug('Deleting {}/{}'.format(self.__configID, name))
        self.__config.pop(name, None)


    def readFile(self, path, mode='t'):
        """Reads and returns the contents of the given file ``path``.
        Returns ``None`` if the path does not exist.

        :arg mode: ``'t'`` for text mode, or ``'b'`` for binary.
        """

        mode = 'r' + mode
        path = self.filePath(path)

        if op.exists(path):
            with open(path, mode) as f:
                return f.read()
        else:
            return None


    @contextlib.contextmanager
    def writeFile(self, path, mode='t'):
        """Write to the given file ``path``. This function is intended
        to be used as a context manager. For example::


            with settings.writeFile('mydata.txt') as f:
                f.write('data\\n')


        An alternate method of writing to a file is via :meth:`filePath`,
        e.g.::


            fname = settings.filePath('mydata.txt')
            with open(fname, 'wt') as f:
                f.write('data\\n')


        However using ``writeFile`` has the advantage that any intermediate
        directories will be created if they don't already exist.
        """

        mode    = 'w' + mode
        path    = self.filePath(path)
        pathdir = op.dirname(path)

        if not op.exists(pathdir):
            os.makedirs(pathdir)

        with open(path, mode) as f:
            yield f


    def deleteFile(self, path):
        """Deletes the given file ``path``. """

        path = self.filePath(path)
        if op.exists(path):
            os.remove(path)


    def filePath(self, path):
        """Converts the given ``path`` to an absolute path.  Note that there
        is no guarantee that the returned file path (or its containing
        directory) exists.
        """

        path = self.__fixPath(path)
        path = op.join(self.__configDir, path)
        return path


    def readAll(self, pattern=None):
        """Returns all settings with names that match the given glob-style
        pattern.
        """
        if pattern is None:
            return copy.deepcopy(self.__config)

        keys = fnmatch.filter(self.__config.keys(), pattern)
        vals = [copy.deepcopy(self.__config[k]) for k in keys]

        return dict(zip(keys, vals))


    def listFiles(self, pattern=None):
        """Returns a list of all stored settings files which match the given
        glob-style pattern. If a pattern is not given, all files are returned.
        """
        allFiles = []

        if pattern is not None:
            pattern = self.__fixPath(pattern)

        for dirpath, dirnames, filenames in os.walk(self.__configDir):

            dirpath   = op.relpath(dirpath, self.__configDir)
            filenames = [op.join(dirpath, fn) for fn in filenames]

            if pattern is None:
                allFiles.extend(filenames)
            else:
                allFiles.extend(fnmatch.filter(filenames, pattern))

        return allFiles


    def clear(self):
        """Delete all configuration settings and files. """

        log.debug('Clearing all settings in {}'.format(self.__configID))

        self.__config = {}

        for path in os.listdir(self.__configDir):
            path = op.join(self.__configDir, path)
            if op.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)


    def __fixPath(self, path):
        """Ensures that the given path (passed into :meth:`readFile`,
        :meth:`writeFile`, or :meth:`deleteFile`) is cross-platform
        compatible. Only works for paths which use ``'/'`` as the path
        separator.
        """
        return op.join(*path.split('/'))


    def __getConfigDir(self, cid):
        """Returns a directory in which configuration files can be stored.

        .. note:: If, for whatever reason, a configuration directory could not
                  be located or created, a temporary directory will be used.
                  This means that all settings read during this session will
                  be lost on exit.
        """

        cfgdir  = None
        homedir = op.expanduser('~')

        # On linux, if $XDG_CONFIG_HOME is set, use $XDG_CONFIG_HOME/fslpy/
        # Otherwise, use $HOME/.config/fslpy/
        #
        # https://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html
        if platform.system().lower().startswith('linux'):

            basedir = os.environ.get('XDG_CONFIG_HOME')
            if basedir is None:
                basedir = op.join(homedir, '.config')

            cfgdir = op.join(basedir, cid)

        # On all other platforms, use $HOME/.fslpy/
        else:
            cfgdir = op.join(homedir, '.{}'.format(cid))

        # Try and create the config directory
        # tree if it does not exist
        if not op.exists(cfgdir):
            try:
                os.makedirs(cfgdir)
            except OSError:
                log.warning(
                    'Unable to create {} configuration '
                    'directory: {}'.format(cid, cfgdir),
                    exc_info=True)
                cfgdir = None

        # If dir creation failed, use a temporary
        # directory, and delete it on exit
        if cfgdir is None:
            cfgdir = tempfile.mkdtemp()
            atexit.register(shutil.rmtree, cfgdir, ignore_errors=True)

        log.debug('{} configuration directory: {}'.format(cid, cfgdir))

        return cfgdir


    def __readConfigFile(self):
        """Called by :meth:`__init__`. Reads any settings that were stored
        in a file, and returns them in a dictionary.
        """

        configFile = op.join(self.__configDir, 'config.pkl')

        log.debug('Reading {} configuration from: {}'.format(
            self.__configID, configFile))

        try:
            with open(configFile, 'rb') as f:
                return pickle.load(f)
        except (IOError, pickle.UnpicklingError, EOFError):
            log.debug('Unable to load stored {} configuration file '
                      '{}'.format(self.__configID, configFile),
                      exc_info=True)
            return {}


    def writeConfigFile(self):
        """Writes all settings to a file."""

        config     = self.__config
        configFile = op.join(self.__configDir, 'config.pkl')

        log.debug('Writing {} configuration to: {}'.format(
            self.__configID, configFile))

        try:
            with open(configFile, 'wb') as f:
                pickle.dump(config, f, protocol=2)
        except (IOError, pickle.PicklingError, EOFError, FileNotFoundError):
            log.warning('Unable to save {} configuration file '
                        '{}'.format(self.__configID, configFile),
                        exc_info=True)
