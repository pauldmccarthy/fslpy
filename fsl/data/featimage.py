#!/usr/bin/env python
#
# featimage.py - An Image subclass which has some FEAT-specific functionality.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`FEATImage` class, a subclass of
:class:`.Image` designed to encapsulate data from a FEAT analysis.
"""


import os.path as op

import numpy   as np

import image   as fslimage
import            featresults


class FEATImage(fslimage.Image):
    """An ``Image`` from a FEAT analysis.

    The :class:`FEATImage` class makes use of the functions defined in the
    :mod:`.featresults` module.


    An example of using the ``FEATImage`` class::

        import fsl.data.featimage as featimage

        # You can pass in the name of the
        # .feat/.gfeat directory, or any
        # file contained within that directory.
        img = featimage.FEATImage('myanalysis.feat/filtered_func_data.nii.gz')

        # Query information about the FEAT analysis
        print img.numEVs()
        print img.contrastNames()
        print img.numPoints()

        # Get the model fit residuals
        res4d = img.getResiduals()

        # Get the full model fit for voxel
        # [23, 30, 42] (in this example, we
        # have 4 EVs - the first argument
        # is a contrast vector).
        img.fit([1, 1, 1, 1], [23, 30, 42], fullmodel=True)
    """
    

    def __init__(self, path, **kwargs):
        """Create a ``FEATImage`` instance.

        :arg path:   A FEAT analysis directory, or an image file contained
                     within such a directory.

        :arg kwargs: Passed to the :class:`.Image` constructor.

        .. note:: If a FEAT directory is passed in for the ``path``
                  argument, this ``FEATImage`` instance will encapsulate
                  the model input data, typically called
                  ``<directory>.feat/filtered_func_data.nii.gz``.
        """

        featDir = featresults.getFEATDir(path)
        
        if featDir is None:
            raise ValueError('{} does not appear to be data from a '
                             'FEAT analysis'.format(path))

        if op.isdir(path):
            path = op.join(featDir, 'filtered_func_data')

        settings    = featresults.loadSettings( featDir)
        design      = featresults.loadDesign(   featDir)
        names, cons = featresults.loadContrasts(featDir)
        
        fslimage.Image.__init__(self, path, **kwargs)

        self.__analysisName  = op.splitext(op.basename(featDir))[0]
        self.__featDir       = featDir
        self.__design        = design
        self.__contrastNames = names
        self.__contrasts     = cons
        self.__settings      = settings
        self.__evNames       = featresults.getEVNames(settings)

        self.__residuals     =  None
        self.__pes           = [None] * self.numEVs()
        self.__copes         = [None] * self.numContrasts()
        self.__zstats        = [None] * self.numContrasts()
        self.__clustMasks    = [None] * self.numContrasts()

        if 'name' not in kwargs:
            self.name = '{}: {}'.format(self.__analysisName, self.name)


    def getFEATDir(self):
        """Returns the FEAT directory this image is contained in."""
        return self.__featDir


    def getAnalysisName(self):
        """Returns the FEAT analysis name, which is the FEAT directory
        name, minus the ``.feat`` / ``.gfeat`` suffix.
        """
        return self.__analysisName
        

    def getDesign(self):
        """Returns the analysis design matrix as a :mod:`numpy` array
        with shape :math:`numPoints\\times numEVs`.
        """
        return np.array(self.__design)
        
    
    def numPoints(self):
        """Returns the number of points (e.g. time points, number of
        subjects, etc) in the analysis.
        """
        return self.__design.shape[0] 

    
    def numEVs(self):
        """Returns the number of explanatory variables (EVs) in the analysis.
        """
        return self.__design.shape[1]


    def evNames(self):
        """Returns a list containing the name of each EV in the analysis."""
        return list(self.__evNames)

    
    def numContrasts(self):
        """Returns the number of contrasts in the analysis."""
        return len(self.__contrasts)

    
    def contrastNames(self):
        """Returns a list containing the name of each contrast in the analysis.
        """
        return list(self.__contrastNames)


    def contrasts(self):
        """Returns a list containing the analysis contrast vectors.

        See :func:`.featresults.loadContrasts`

        """
        return [list(c) for c in self.__contrasts]


    def thresholds(self):
        """Returns the statistical thresholds used in the analysis.

        See :func:`.featresults.getThresholds`
        """
        return featresults.getThresholds(self.__settings)


    def clusterResults(self, contrast):
        """Returns the clusters found in the analysis.

        See :func:.featresults.loadClusterResults`
        """
        return featresults.loadClusterResults(self.__featDir,
                                              self.__settings,
                                              contrast)


    def getPE(self, ev):
        """Returns the PE image for the given EV (0-indexed). """

        if self.__pes[ev] is None:
            pefile = featresults.getPEFile(self.__featDir, ev)
            self.__pes[ev] = FEATImage(
                pefile,
                name='{}: PE{} ({})'.format(
                    self.__analysisName,
                    ev + 1,
                    self.evNames()[ev]))

        return self.__pes[ev]


    def getResiduals(self):
        """Returns the residuals of the full model fit. """
        
        if self.__residuals is None:
            resfile = featresults.getResidualFile(self.__featDir)
            self.__residuals = FEATImage(
                resfile,
                name='{}: residuals'.format(self.__analysisName))
        
        return self.__residuals

    
    def getCOPE(self, con):
        """Returns the COPE image for the given contrast (0-indexed). """
        
        if self.__copes[con] is None:
            copefile = featresults.getPEFile(self.__featDir, con)
            self.__copes[con] = FEATImage(
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
            zfile = featresults.getZStatFile(self.__featDir, con)

            self.__zstats[con] = FEATImage(
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
            mfile = featresults.getClusterMaskFile(self.__featDir, con)

            self.__clustMasks[con] = FEATImage(
                mfile,
                name='{}: cluster mask for zstat{} ({})'.format(
                    self.__analysisName,
                    con + 1,
                    self.contrastNames()[con]))

        return self.__clustMasks[con] 
            

    def fit(self, contrast, xyz, fullmodel=False):
        """Calculates the model fit for the given contrast vector
        at the given voxel.

        Passing in a contrast of all 1s, and ``fullmodel=True`` will
        get you the full model fit. Pass in ``fullmodel=False`` for
        all other contrasts, otherwise the model fit values will not
        be scaled correctly.

        :arg contrast:  The contrast vector (pass all 1s for a full model
                        fit).

        :arg xyz:       Coordinates of the voxel to calculate the model fit
                        for.

        :arg fullmodel: Set to ``True`` for a full model fit, ``False``
                        otherwise.
        """

        if not fullmodel:
            contrast  = np.array(contrast)
            contrast /= np.sqrt((contrast ** 2).sum())

        x, y, z = xyz
        numEVs  = self.numEVs()

        if len(contrast) != numEVs:
            raise ValueError('Contrast is wrong length')
        
        X        = self.__design
        data     = self.data[x, y, z, :]
        modelfit = np.zeros(len(data))

        for i in range(numEVs):

            pe        = self.getPE(i).data[x, y, z]
            modelfit += X[:, i] * pe * contrast[i]

        return modelfit + data.mean()


    def partialFit(self, contrast, xyz, fullmodel=False):
        """Calculates and returns the partial model fit for the specified
        contrast vector at the specified voxel.

        See :meth:`fit` for details on the arguments.
        """

        x, y, z   = xyz
        residuals = self.getResiduals().data[x, y, z, :]
        modelfit  = self.fit(contrast, xyz, fullmodel)

        return residuals + modelfit
