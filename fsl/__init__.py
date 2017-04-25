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

.. note:: The ``fslpy`` version number (currently |version|) is set in a
          single place - the :mod:`fsl.version` module.
"""


import fsl.version


__version__ = fsl.version.__version__
"""The current ``fslpy`` version number. This information is stored in the
:mod:`fsl.version` module.
"""
