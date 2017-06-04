#!/usr/bin/env python
#
# version.py - fslpy version information.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The primary purpose of this module is as a container for the ``fslpy``
version number. A couple of conveniense functions for comparing version
numbers are also defined here.

.. autosummary::
   :nosignatures:

   __version__
   parseVersionString
   compareVersions


The ``fslpy`` version number consists of three numbers, separated by a period,
which roughly obeys the Semantic Versioning conventions (http://semver.org/):

 1. The major release number. This gets updated for major/external releases.

 2. The minor release number. This gets updated for minor/internal releases,
    which involve new features, bug-fixes, and other updates.

 3. The point release number. This gets updated for minor/internal releases,
    which primarily involve bug-fixes and minor changes.
"""


import string


__version__ = '1.0.1'
"""Current version number, as a string. """


def parseVersionString(versionString):
    """Parses the given version string, and returns a tuple containing
    the individual components of the version number (see the description
    of the :attr:`__version__` attribute).

    An error is raised if the ``versionString`` is invalid.
    """

    if versionString == 'dev':
        return 9999, 9999, 9999

    components = versionString.split('.')

    # Major, minor, and point
    # version are always numeric
    major, minor, point = [c for c in components]

    # Early versions of FSLeyes
    # used a letter at the end
    # to denote a hotfix release.
    # Don't break if we get one
    # of these old version numbers.
    point = point.strip(string.ascii_letters)

    return [int(c) for c in [major, minor, point]]


def compareVersions(v1, v2, ignorePoint=False):
    """Compares the given ``fslpy`` version numbers.

    :arg v1:          Version number to compare
    :arg v2:          Version number to compare
    :arg ignorePoint: Defaults to ``False``. If ``True``, the point release
                      numbers are ignored in the comparison.

    :returns: One of the following:

                - -1 if ``v1`` < ``v2`` (i.e. ``v1`` is older than ``v2``)
                -  0 if ``v1`` == ``v2``
                -  0 if ``v1`` > ``v2``
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
