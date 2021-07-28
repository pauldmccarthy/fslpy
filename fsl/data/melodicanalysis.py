#!/usr/bin/env python
#
# melodicanalysis.py - Utility functions for loading/querying the contents of
# a MELODIC analysis directory.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides a set of functions for accessing the contents of a
MELODIC analysis directory. These functions are primarily intended to be used
by the :class:`.MELODICImage` class, but are available for other uses. The
following functions are provided:


.. autosummary::
   :nosignatures:

   isMelodicImage
   isMelodicDir
   getAnalysisDir
   getTopLevelAnalysisDir
   getDataFile
   getICFile
   getMixFile
   getFTMixFile
   getNumComponents
   getComponentTimeSeries
   getComponentPowerSpectra
"""


import logging

import os.path as op
import numpy   as np

import fsl.data.image        as fslimage
import fsl.data.featanalysis as featanalysis


log = logging.getLogger(__name__)


def isMelodicImage(path):
    """Returns ``True`` if the given path looks like it is a melodic
    component image file, ``False`` otherwise.
    """


    try:
        path = fslimage.addExt(path)
    except fslimage.PathError:
        return False

    dirname  = op.dirname( path)
    filename = op.basename(path)
    filename = fslimage.removeExt(filename)

    prefixes = ['melodic_IC',
                'melodic_oIC']

    return any([filename == p for p in prefixes]) and isMelodicDir(dirname)


def isMelodicDir(path):
    """Returns ``True`` if the given path looks like it is a MELODIC directory,
    ``False`` otherwise. A MELODIC directory:

      - Must contain a file called ``melodic_IC.nii.gz`` or
        ``melodic_oIC.nii.gz``.
      - Must contain a file called ``melodic_mix``.
      - Must contain a file called ``melodic_FTmix``.
    """

    path = op.abspath(path)

    if not op.isdir(path):
        return False

    # Must contain an image file called
    # melodic_IC or melodic_oIC
    prefixes = ['melodic_IC', 'melodic_oIC']
    for p in prefixes:
        try:
            fslimage.addExt(op.join(path, p))
            break
        except fslimage.PathError:
            pass
    else:
        return False

    # Must contain files called
    # melodic_mix and melodic_FTmix
    if not op.exists(op.join(path, 'melodic_mix')):   return False
    if not op.exists(op.join(path, 'melodic_FTmix')): return False

    return True


def getAnalysisDir(path):
    """If the given path is contained within a MELODIC directory, the path
    to that MELODIC directory is returned. Otherwise, ``None`` is returned.
    """

    if not op.isdir(path):
        path = op.dirname(path)

    while path not in (op.sep, ''):
        if isMelodicDir(path):
            return path
        path = op.dirname(path)

    return None


def getTopLevelAnalysisDir(path):
    """If the given path is contained within a hierarchy of FEAT or MELODIC
    directories, the path to the highest-level (i.e. the shallowest in the
    file system) directory is returned. Otherwise, ``None`` is returned.

    See :func:`.featanalysis.getTopLevelAnalysisDir`.
    """
    return featanalysis.getTopLevelAnalysisDir(path)


def getDataFile(meldir):
    """If the given melodic directory is contained within another analysis
    directory, the path to the data file is returned. Otherwise ``None`` is
    returned.
    """

    topDir = getTopLevelAnalysisDir(meldir)

    if topDir is None:
        return None

    # People often rename filtered_func_data.nii.gz
    # to something like filtered_func_data_clean.nii.gz,
    # because that is the recommended approach when
    # performing ICA-based denoising). So we try both.
    candidates = ['filtered_func_data', 'filtered_func_data_clean']

    for candidate in candidates:
        dataFile = op.join(topDir, candidate)
        try:                       return fslimage.addExt(dataFile)
        except fslimage.PathError: continue

    return None


def getMeanFile(meldir):
    """Return a path to the mean image of the meloidic input data. """
    return fslimage.addExt(op.join(meldir, 'mean'))


def getICFile(meldir):
    """Returns the path to the melodic IC image. """
    try:
        return fslimage.addExt(op.join(meldir, 'melodic_IC'))
    except fslimage.PathError:
        return fslimage.addExt(op.join(meldir, 'melodic_oIC'))


def getMixFile(meldir):
    """Returns the path to the melodic mix file. """

    mixfile = op.join(meldir, 'melodic_mix')
    if op.exists(mixfile): return mixfile
    else:                  return None


def getFTMixFile(meldir):
    """Returns the path to the melodic FT mix file. """

    ftmixfile = op.join(meldir, 'melodic_FTmix')
    if op.exists(ftmixfile): return ftmixfile
    else:                    return None


def getReportFile(meldir):
    """Returns the path to the MELODIC report index file, or ``None`` if there
    is no report.
    """

    report = op.join(meldir, '..', 'report.html')
    if op.exists(report): return report
    else:                 return None


def getNumComponents(meldir):
    """Returns the number of components generated in the melodic analysis
    contained in the given directrory.
    """

    icImg = fslimage.Image(getICFile(meldir), loadData=False, calcRange=False)
    return icImg.shape[3]


def getComponentTimeSeries(meldir):
    """Returns a ``numpy`` array containing the melodic mix for the given
    directory.
    """

    mixfile = getMixFile(meldir)
    return np.loadtxt(mixfile)


def getComponentPowerSpectra(meldir):
    """Returns a ``numpy`` array containing the melodic FT mix for the
    given directory.
    """
    ftmixfile = getFTMixFile(meldir)
    return np.loadtxt(ftmixfile)
