#!/usr/bin/env python
#
# featimage.py - An Image subclass which has some FEAT-specific functionality.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`FeatImage` class, a subclass of
:class:`.Image` designed for the ``filtered_func_data`` file of a FEAT
analysis.
"""

import os.path as op
import            glob

import numpy   as np

import nibabel as nib

import image   as fslimage


def loadDesignMat(designmat):
    """Loads a FEAT ``design.mat`` file. Returns a ``numpy`` array
    containing the design matrix data, where the first dimension
    corresponds to the data points, and the second to the EVs.
    """

    matrix = None
    with open(designmat, 'rt') as f:

        while True:
            line = f.readline()
            if line.strip() == '/Matrix':
                break

        matrix = np.loadtxt(f)

    if matrix is None or matrix.size == 0:
        raise RuntimeError('{} does not appear to be a '
                           'valid design.mat file'.format(designmat))

    return matrix


def loadDesignCon(designcon):
    """Loads a FEAT ``design.con`` file. Returns a tuple containing:
    
      - A dictionary of ``{contrastnum : name}`` mappings
    
      - A list of contrast vectors (each of which is a list itself).
    """

    matrix       = None
    numContrasts = 0
    names        = {}
    with open(designcon, 'rt') as f:

        while True:
            line = f.readline().strip()

            if line.startswith('/ContrastName'):
                tkns       = line.split(None, 1)
                num        = [c for c in tkns[0] if c.isdigit()]
                num        = int(''.join(num))
                name       = tkns[1].strip()
                names[num] = name

            elif line.startswith('/NumContrasts'):
                numContrasts = int(line.split()[1])

            elif line == '/Matrix':
                break

        matrix = np.loadtxt(f)

    if matrix       is None             or \
       numContrasts != matrix.shape[0]:
        raise RuntimeError('{} does not appear to be a '
                           'valid design.con file'.format(designcon))

    # Fill in any missing contrast names
    if len(names) != numContrasts:
        for i in range(numContrasts):
            if i + 1 not in names:
                names[i + 1] = str(i + 1)

    names     = [names[c + 1] for c in range(numContrasts)]
    contrasts = []

    for row in matrix:
        contrasts.append(list(row))

    return names, contrasts


def loadDesignFsf(designfsf):
    """
    """

    settings = {}

    with open(designfsf, 'rt') as f:

        for line in f.readlines():
            line = line.strip()

            if not line.startswith('set '):
                continue

            tkns = line.split(None, 2)

            settings[tkns[1].strip()] = tkns[2]
    
    return settings


def isFEATData(path):
    
    keys = ['.feat{}filtered_func_data' .format(op.sep),
            '.gfeat{}filtered_func_data'.format(op.sep)]

    isfeatdir = any([k in path for k in keys])

    dirname   = op.dirname(path)
    hasdesfsf = op.exists(op.join(dirname, 'design.fsf'))
    hasdesmat = op.exists(op.join(dirname, 'design.mat'))
    hasdescon = op.exists(op.join(dirname, 'design.con'))

    isfeat    = (isfeatdir and
                 hasdesmat and
                 hasdescon and
                 hasdesfsf)
    
    return isfeat


class FEATImage(fslimage.Image):

    def __init__(self, image, **kwargs):
        fslimage.Image.__init__(self, image, **kwargs)

        if not isFEATData(self.dataSource):
            raise ValueError('{} does not appear to be data from a '
                             'FEAT analysis'.format(self.dataSource))

        featDir     = op.dirname(self.dataSource)
        settings    = loadDesignFsf(op.join(featDir, 'design.fsf'))
        design      = loadDesignMat(op.join(featDir, 'design.mat'))
        names, cons = loadDesignCon(op.join(featDir, 'design.con'))

        self.__featDir       = featDir
        self.__design        = design
        self.__contrastNames = names
        self.__contrasts     = cons
        self.__settings      = settings

        self.__residuals     =  None
        self.__pes           = [None] * self.numEVs()
        self.__copes         = [None] * self.numContrasts()

        

    def getDesign(self):
        return np.array(self.__design)
        
    
    def numPoints(self):
        return self.__design.shape[0] 

    
    def numEVs(self):
        return self.__design.shape[1]

    
    def numContrasts(self):
        return len(self.__contrasts)

    
    def contrastNames(self):
        return list(self.__contrastNames)


    def contrasts(self):
        return [list(c) for c in self.__contrasts]


    def __getStatsFile(self, prefix, ev=None):

        if ev is not None: prefix = '{}{}'.format(prefix, ev + 1)

        prefix = op.join(self.__featDir, 'stats', prefix)
        
        return glob.glob('{}.*'.format(prefix))[0]


    def getPE(self, ev):

        if self.__pes[ev] is None:
            pefile = self.__getStatsFile('pe', ev)
            self.__pes[ev] = nib.load(pefile).get_data()

        return self.__pes[ev]


    def getResiduals(self):
        
        if self.__residuals is None:
            resfile          = self.__getStatsFile('res4d')
            self.__residuals = nib.load(resfile).get_data()
        
        return self.__residuals

    
    def getCOPE(self, num):
        
        if self.__copes[num] is None:
            copefile = self.__getStatsFile('cope', num)
            self.__copes[num] = nib.load(copefile).get_data()

        return self.__copes[num] 
        

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

            pe        = self.getPE(i)[x, y, z]
            modelfit += X[:, i] * pe * contrast[i]

        return modelfit + data.mean()


    def reducedData(self, xyz, contrast, fullmodel=False):
        """

        Passing in a contrast of all 1s, and ``fullmodel=True`` will
        get you the model fit residuals.
        """

        x, y, z   = xyz
        residuals = self.getResiduals()[x, y, z, :]
        modelfit  = self.fit(contrast, xyz, fullmodel)

        return residuals + modelfit
