#!/usr/bin/env python
#
# __init__.py - The fsl.scripts package.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The ``fsl.scripts`` package contains all of the executable scripts provided
by ``fslpy``, and other python-based FSL packages.

.. note:: The ``fsl.scripts`` namespace is a ``pkgutil``-style *namespace
          package* - it can be used across different projects - see
          https://packaging.python.org/guides/packaging-namespace-packages/ for
          details.
"""

__path__ = __import__('pkgutil').extend_path(__path__, __name__)  # noqa
