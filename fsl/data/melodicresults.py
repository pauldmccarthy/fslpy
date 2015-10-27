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

   isMelodicDir
   getMelodicDir
   getICFile
   getNumComponents
   getComponentTimeSeries
"""


import            os 
import os.path as op
import numpy   as np

import fsl.data.image as fslimage


def isMelodicDir(path):
    """
    """

    # Must be named *.ica or *.gica
    meldir = getMelodicDir(path)

    if meldir is None:
        return False

    # Must contain an image file called melodic_IC
    try:
        fslimage.addExt(op.join(meldir, 'melodic_IC'), mustExist=True)
    except ValueError:
        return False

    # Must contain a file called melodic_mix
    if not op.exists(op.join(meldir, 'melodic_mix')):
        return False

    return True

    
def getMelodicDir(path):
    """
    """

    # TODO This code is identical to featresults.getFEATDir.
    # Can you generalise it and put it somewhere in fsl.utils?

    sufs     = ['.ica', '.gica']
    idxs     = [(path.rfind(s), s) for s in sufs]
    idx, suf = max(idxs, key=lambda (i, s): i)

    if idx == -1:
        return None

    idx  += len(suf)
    path  = path[:idx]

    if path.endswith(suf) or path.endswith('{}{}'.format(suf, op.sep)):
        return path
                                           
    return None 


def getICFile(meldir):
    """
    """
    return fslimage.addExt(op.join(meldir, 'melodic_IC'))


def getMixFile(meldir):
    """
    """
    return op.join(meldir, 'melodic_mix')


def getNumComponents(meldir):
    """
    """

    icImg = fslimage.Image(getICFile(meldir), loadData=False)
    return icImg.shape[3]


def getComponentTimeSeries(meldir):
    """
    """

    mixfile = getMixFile(meldir)
    return np.loadtxt(mixfile)
