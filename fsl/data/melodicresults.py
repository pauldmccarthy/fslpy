#!/usr/bin/env python
#
# melodicresults.py - Utility functions for loading/querying the contents of a
# MELODIC analysis directory.
# 
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides a set of functions for accessing the contents of a
MELODIC analysis directory. These functions are primarily intended to be used
by the :class:`.MELODICImage` class, but are available for other uses. The
following functions are provided:

.. autosummary::
   nosignatures:

   isMELODICDir
   getMELODICDir

   getICFile

   getNumComponents
   getComponentTimeSeries
"""


def isMELODICDir(path):
    """
    """

    # A MELODIC directory:
    #   - Must be called *.ica
    #   - Must contain melodic_IC.nii.gz
    #   - Must contain melodic_mix
