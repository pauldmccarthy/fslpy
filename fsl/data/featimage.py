#!/usr/bin/env python
#
# featimage.py - An Image subclass which has some FEAT-specific functionality.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`FEATImage` class, a subclass of
:class:`.Image` designed to encapsulate data from a FEAT analysis.
This module also provides the :func:`modelFit` function.
"""


import os.path      as op

import numpy        as np

from . import image as fslimage
from . import          featanalysis


class FEATImage(fslimage.Image):
    """An ``Image`` which contains the input data from a FEAT analysis.

    The :class:`FEATImage` class makes use of the functions defined in the
    :mod:`.featanalysis` module.


    An example of using the ``FEATImage`` class::

        import fsl.data.featimage as featimage

        # You can pass in the name of the
        # .feat directory, or the filtered_func_data
        # file contained within that directory.
        img = featimage.FEATImage('myanalysis.feat/filtered_func_data.nii.gz')

        # Query information about the FEAT analysis
        print(img.numEVs())
        print(img.contrastNames())
        print(img.numPoints())

        # Get the model fit residuals
        res4d = img.getResiduals()

        # Get the full model fit for voxel
        # [23, 30, 42] (in this example, we
        # have 4 EVs - the first argument
        # is a contrast vector).
        img.fit([1, 1, 1, 1], [23, 30, 42], fullModel=True)
    """


    def __init__(self, path, **kwargs):
        """Create a ``FEATImage`` instance.

        :arg path:   A FEAT analysis directory, or the input data image file
                     contained within such a directory.

        :arg kwargs: Passed to the :class:`.Image` constructor.
        """

        if op.isdir(path):
            path = op.join(path, 'filtered_func_data')

        if not featanalysis.isFEATImage(path):
            raise ValueError('{} does not appear to be data '
                             'from a FEAT analysis'.format(path))

        featDir     = op.dirname(path)
        settings    = featanalysis.loadSettings( featDir)

        if featanalysis.hasStats(featDir):
            design      = featanalysis.loadDesign(   featDir, settings)
            names, cons = featanalysis.loadContrasts(featDir)
        else:
            design      = None
            names, cons = [], []

        fslimage.Image.__init__(self, path, **kwargs)

        self.__analysisName  = op.splitext(op.basename(featDir))[0]
        self.__featDir       = featDir
        self.__design        = design
        self.__contrastNames = names
        self.__contrasts     = cons
        self.__settings      = settings

        self.__residuals     =  None
        self.__pes           = [None] * self.numEVs()
        self.__copes         = [None] * self.numContrasts()
        self.__zstats        = [None] * self.numContrasts()
        self.__clustMasks    = [None] * self.numContrasts()

        if 'name' not in kwargs:
            self.name = '{}: {}'.format(self.__analysisName, self.name)


    def __del__(self):
        """Clears references to any loaded images."""
        self.__design     = None
        self.__residuals  = None
        self.__pes        = None
        self.__copes      = None
        self.__zstats     = None
        self.__clustMasks = None


    def getFEATDir(self):
        """Returns the FEAT directory this image is contained in."""
        return self.__featDir


    def getAnalysisName(self):
        """Returns the FEAT analysis name, which is the FEAT directory
        name, minus the ``.feat`` / ``.gfeat`` suffix.
        """
        return self.__analysisName


    def isFirstLevelAnalysis(self):
        """Returns ``True`` if the FEAT analysis described by ``settings``
        is a first level analysis, ``False`` otherwise.
        """
        return featanalysis.isFirstLevelAnalysis(self.__settings)


    def getTopLevelAnalysisDir(self):
        """Returns the path to the higher level analysis directory of
        which this FEAT analysis is a part, or ``None`` if this analysis
        is not part of another analysis.
        """
        return featanalysis.getTopLevelAnalysisDir(self.__featDir)


    def getReportFile(self):
        """Returns the path to the FEAT report - see
        :func:`.featanalysis.getReportFile`.
        """
        return featanalysis.getReportFile(self.__featDir)


    def hasStats(self):
        """Returns ``True`` if the analysis for this ``FEATImage`` contains
        a statistical analysis.
        """
        return self.__design is not None


    def getDesign(self, voxel=None):
        """Returns the analysis design matrix as a :mod:`numpy` array
        with shape :math:`numPoints\\times numEVs`.
        See :meth:`.FEATFSFDesign.getDesign`.
        """

        if self.__design is None:
            return None

        return self.__design.getDesign(voxel)


    def numPoints(self):
        """Returns the number of points (e.g. time points, number of
        subjects, etc) in the analysis.
        """
        if self.__design is None:
            return 0

        return self.__design.getDesign().shape[0]


    def numEVs(self):
        """Returns the number of explanatory variables (EVs) in the analysis.
        """
        if self.__design is None:
            return 0

        return len(self.__design.getEVs())


    def evNames(self):
        """Returns a list containing the name of each EV in the analysis."""

        if self.__design is None:
            return []

        return [ev.title for ev in self.__design.getEVs()]


    def numContrasts(self):
        """Returns the number of contrasts in the analysis."""
        return len(self.__contrasts)


    def contrastNames(self):
        """Returns a list containing the name of each contrast in the analysis.
        """
        return list(self.__contrastNames)


    def contrasts(self):
        """Returns a list containing the analysis contrast vectors.

        See :func:`.featanalysis.loadContrasts`

        """
        return [list(c) for c in self.__contrasts]


    def thresholds(self):
        """Returns the statistical thresholds used in the analysis.

        See :func:`.featanalysis.getThresholds`
        """
        return featanalysis.getThresholds(self.__settings)


    def clusterResults(self, contrast):
        """Returns the clusters found in the analysis.

        See :func:.featanalysis.loadClusterResults`
        """
        return featanalysis.loadClusterResults(self.__featDir,
                                               self.__settings,
                                               contrast)


    def getPE(self, ev):
        """Returns the PE image for the given EV (0-indexed). """

        if self.__pes[ev] is None:
            pefile = featanalysis.getPEFile(self.__featDir, ev)
            self.__pes[ev] = fslimage.Image(
                pefile,
                name='{}: PE{} ({})'.format(
                    self.__analysisName,
                    ev + 1,
                    self.evNames()[ev]))

        return self.__pes[ev]


    def getResiduals(self):
        """Returns the residuals of the full model fit. """

        if self.__residuals is None:
            resfile = featanalysis.getResidualFile(self.__featDir)
            self.__residuals = fslimage.Image(
                resfile,
                name='{}: residuals'.format(self.__analysisName))

        return self.__residuals


    def getCOPE(self, con):
        """Returns the COPE image for the given contrast (0-indexed). """

        if self.__copes[con] is None:
            copefile = featanalysis.getCOPEFile(self.__featDir, con)
            self.__copes[con] = fslimage.Image(
                copefile,
                name='{}: COPE{} ({})'.format(
                    self.__analysisName,
                    con + 1,
                    self.contrastNames()[con]))
        return self.__copes[con]


    def getZStats(self, con):
        """Returns the Z statistic image for the given contrast (0-indexed).
        """

        if self.__zstats[con] is None:
            zfile = featanalysis.getZStatFile(self.__featDir, con)

            self.__zstats[con] = fslimage.Image(
                zfile,
                name='{}: zstat{} ({})'.format(
                    self.__analysisName,
                    con + 1,
                    self.contrastNames()[con]))

        return self.__zstats[con]


    def getClusterMask(self, con):
        """Returns the cluster mask image for the given contrast (0-indexed).
        """

        if self.__clustMasks[con] is None:
            mfile = featanalysis.getClusterMaskFile(self.__featDir, con)

            self.__clustMasks[con] = fslimage.Image(
                mfile,
                name='{}: cluster mask for zstat{} ({})'.format(
                    self.__analysisName,
                    con + 1,
                    self.contrastNames()[con]))

        return self.__clustMasks[con]


    def fit(self, contrast, xyz):
        """Calculates the model fit for the given contrast vector
        at the given voxel. See the :func:`modelFit` function.

        :arg contrast:  The contrast vector (pass all 1s for a full model
                        fit).

        :arg xyz:       Coordinates of the voxel to calculate the model fit
                        for.
        """

        if self.__design is None:
            raise RuntimeError('No design')

        x, y, z    = xyz
        firstLevel = self.isFirstLevelAnalysis()
        numEVs     = self.numEVs()

        if len(contrast) != numEVs:
            raise ValueError('Contrast is wrong length')

        design = self.getDesign(xyz)
        data   = self[x, y, z, :]
        pes    = [self.getPE(i)[x, y, z] for i in range(numEVs)]

        return modelFit(data, design, contrast, pes, firstLevel)


    def partialFit(self, contrast, xyz):
        """Calculates and returns the partial model fit for the specified
        contrast vector at the specified voxel.

        See :meth:`fit` for details on the arguments.
        """

        x, y, z   = xyz
        residuals = self.getResiduals()[x, y, z, :]
        modelfit  = self.fit(contrast, xyz)

        return residuals + modelfit


def modelFit(data, design, contrast, pes, firstLevel=True):
    """Calculates the model fit to the given data for the given contrast
    vector.

    :arg data:       The input data

    :arg design:     The design matrix

    :arg contrast:   The contrast vector (pass all 1s for a full model
                     fit)

    :arg pes:        Parameter estimates for each EV in the design matrix

    :arg firstLevel: If ``True`` (the default), the mean of the input
                     data is added to the result.

    :returns: The best fit of the model to the data.
    """

    # Here we are basically trying to
    # replicate the behaviour of tsplot.
    # There are some differences though -
    # by default, tsplot weights the
    # data by Z statistics. We're not
    # doing that here.

    # Normalise the contrast vector.
    # The scaling factor is arbitrary,
    # but should result in a visually
    # sensible scaling of the model fit.
    # For a vector of all 1's (i.e. a
    # full model fit) this is a no-op.
    #
    # We also take the absolute value
    # of the values in the contrast
    # vector, as the parameter estimates
    # should be appropriately signed,
    # so we don't want negative contrast
    # vector values to invert them.
    contrast = np.array(contrast)
    nevs     = len(contrast)
    nonzero  = sum(~np.isclose(contrast, 0))
    contrast = contrast / np.sqrt((contrast ** 2).sum())
    contrast = np.abs(contrast * np.sqrt(nonzero))

    modelfit = np.zeros(len(data))

    for i in range(nevs):

        ev        = design[:, i]
        pe        = pes[i]
        modelfit += ev * pe * contrast[i]

    # Make sure the model fit has an
    # appropriate mean.  The data in
    # first level analyses is demeaned
    # before model fitting, so we need
    # to add it back in.
    if firstLevel: return modelfit + data.mean()
    else:          return modelfit
