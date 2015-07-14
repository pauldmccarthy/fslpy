#!/usr/bin/env python
#
# featimage.py - An Image subclass which has some FEAT-specific functionality.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`FEATImage` class, a subclass of
:class:`.Image` designed for the ``filtered_func_data`` file of a FEAT
analysis.
"""

import os.path as op

import numpy   as np

import image   as fslimage
import            featresults


class FEATImage(fslimage.Image):

    def __init__(self, path, **kwargs):
        """
        The specified ``path`` may be a FEAT analysis directory, or the model
        data input file (e.g. ``analysis.feat/filtered_func_data.nii.gz``).
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
        return self.__featDir


    def getAnalysisName(self):
        return self.__analysisName
        

    def getDesign(self):
        return np.array(self.__design)
        
    
    def numPoints(self):
        return self.__design.shape[0] 

    
    def numEVs(self):
        return self.__design.shape[1]


    def evNames(self):
        return list(self.__evNames)

    
    def numContrasts(self):
        return len(self.__contrasts)

    
    def contrastNames(self):
        return list(self.__contrastNames)


    def contrasts(self):
        return [list(c) for c in self.__contrasts]


    def thresholds(self):
        return featresults.getThresholds(self.__settings)


    def clusterResults(self, contrast):

        return featresults.loadClusterResults(self.__featDir,
                                              self.__settings,
                                              contrast)


    def getPE(self, ev):

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
        
        if self.__residuals is None:
            resfile = featresults.getResidualFile(self.__featDir)
            self.__residuals = FEATImage(
                resfile,
                name='{}: residuals'.format(self.__analysisName))
        
        return self.__residuals

    
    def getCOPE(self, con):
        
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
        """

        Passing in a contrast of all 1s, and ``fullmodel=True`` will
        get you the full model fit. Pass in ``fullmodel=False`` for
        all other contrasts, otherwise the model fit values will not
        be scaled correctly.
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


    def reducedData(self, xyz, contrast, fullmodel=False):
        """

        Passing in a contrast of all 1s, and ``fullmodel=True`` will
        get you the model fit residuals.
        """

        x, y, z   = xyz
        residuals = self.getResiduals().data[x, y, z, :]
        modelfit  = self.fit(contrast, xyz, fullmodel)

        return residuals + modelfit
