#!/usr/bin/env python
#
# version.py - fslpy version information.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The primary purpose of this module is as a container for the ``fslpy``
version number. A handful of convenience functions for managing version
numbers are also defined here.

.. autosummary::
   :nosignatures:

   __version__
   parseVersionString
   compareVersions
   patchVersion


The ``fslpy`` version number consists of three numbers, separated by a period,
roughly obeys the Semantic Versioning conventions (http://semver.org/), and
is compatible with PEP 440 (https://www.python.org/dev/peps/pep-0440/):


 1. The major release number. This gets updated for major/external releases.

 2. The minor release number. This gets updated for minor/internal releases,
    which involve new features, bug-fixes, and other updates.

 3. The point release number. This gets updated for minor/internal releases,
    which primarily involve bug-fixes and minor changes.


The sole exceptions to the above convention are:

  - development versions, where the point release number is followed by a
    development release identifier of the form ``'.devN'``, where ``N``
    denotes a specific development release.

  - Builds, where the version number ends in ``'+buildN'``, where ``N``
    denotes a specific build.
"""


import os.path as op
import            re
import            string


__version__ = '3.6.0'
"""Current version number, as a string. """


def parseVersionString(versionString):
    """Parses the given version string, and returns a tuple containing
    the individual components of the version number (see the description
    of the :attr:`__version__` attribute).

    An error is raised if the ``versionString`` is invalid.
    """

    # Ignore build if present
    versionString = versionString.split('+')[0]
    components    = versionString.split('.')

    # Truncate after three elements -
    # a development (unreleased version
    # number will end with '.dev', but
    # we ignore this for the purposes of
    # comparison.
    if len(components) == 4 and components[3].startswith('dev'):
        components = components[:3]

    # Major, minor, and point
    # version are always numeric
    major, minor, point = [c for c in components]

    # But early versions of FSLeyes
    # used a letter at the end
    # to denote a hotfix release.
    # Don't break if we get one
    # of these old version numbers.
    point = point.rstrip(string.ascii_letters)

    return [int(c) for c in [major, minor, point]]


def compareVersions(v1, v2, ignorePoint=False):
    """Compares the given ``fslpy`` version numbers.

    Both developemnt versions and build numbers are ignored in the comparison.

    :arg v1:          Version number to compare
    :arg v2:          Version number to compare
    :arg ignorePoint: Defaults to ``False``. If ``True``, the point release
                      numbers are ignored in the comparison.

    :returns: One of the following:

                - -1 if ``v1`` < ``v2`` (i.e. ``v1`` is older than ``v2``)
                -  0 if ``v1`` == ``v2``
                -  1 if ``v1`` > ``v2``
    """

    v1 = parseVersionString(v1)
    v2 = parseVersionString(v2)

    if ignorePoint:
        v1 = v1[:2]
        v2 = v2[:2]

    for p1, p2 in zip(v1, v2):

        if p1 > p2: return  1
        if p1 < p2: return -1

    return 0


def patchVersion(filename, newversion):
    """Patches the given ``filename``, in place, with the given
    ``newversion``. Searches for a line of the form::

        __version__ = '<oldversion>'

    and replaces ``<oldversion>`` with ``newversion``.
    """
    filename = op.abspath(filename)

    with open(filename, 'rt') as f:
        lines = f.readlines()

    pattern = re.compile(r'^__version__ *= *\'.*\' *$')

    for i, line in enumerate(lines):
        if pattern.match(line):
            lines[i] = '__version__ = \'{0}\'\n'.format(newversion)
            break

    with open(filename, 'wt') as f:
        lines = f.writelines(lines)
