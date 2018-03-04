#!/usr/bin/env python
#
# __init__.py - The fslpy library.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The :mod:`fsl` package is a library which contains convenience classes
and functions for use by FSL python tools. It is broadly split into the
following sub-packages:

.. autosummary::

   fsl.data
   fsl.utils
   fsl.scripts
   fsl.version
   fsl.wrappers

.. note:: The ``fsl`` namespace is a ``pkgutil``-style *namespace package* -
          it can be used across different projects - see
          https://packaging.python.org/guides/packaging-namespace-packages/
          for details.
"""

__path__ = __import__('pkgutil').extend_path(__path__, __name__)
