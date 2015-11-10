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
   :nosignatures:

   isMelodicDir
   getMelodicDir
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

import props

import fsl.data.image       as fslimage
import fsl.data.featresults as featresults


log = logging.getLogger(__name__)


def isMelodicDir(path):
    """Returns ``True`` if the given path looks like it is contained within
    a MELODIC directory, ``False`` otherwise. 
    """

    # Must be named *.ica or *.gica
    return getMelodicDir(path) is not None

    
def getMelodicDir(path):
    """Returns the MELODIC directory in which the given path is contained,
    or ``None`` if it is not contained within a MELODIC directory. A melodic
    directory:

      - Must be named ``*.ica`` or ``*.gica``
      - Must contain a file called ``melodic_IC.nii.gz``
      - Must contain a file called ``melodic_mix``.
    """

    # TODO This code is identical to featresults.getFEATDir.
    # Can you generalise it and put it somewhere in fsl.utils?

    path     = op.abspath(path)

    sufs     = ['.ica', '.gica']
    idxs     = [(path.rfind(s), s) for s in sufs]
    idx, suf = max(idxs, key=lambda (i, s): i)

    if idx == -1:
        return None

    idx  += len(suf)
    path  = path[:idx].rstrip(op.sep)

    if not path.endswith(suf):
        return None

    # Must contain an image file called melodic_IC
    try:
        fslimage.addExt(op.join(path, 'melodic_IC'), mustExist=True)
    except ValueError:
        return None

    # Must contain files called
    # melodic_mix and melodic_FTmix
    if not op.exists(op.join(path, 'melodic_mix')):   return None
    if not op.exists(op.join(path, 'melodic_FTmix')): return None
                                           
    return path


def getTopLevelAnalysisDir(path):
    """If the given path is a MELODIC directory, and it is contained within
    a FEAT directory, or another MELODIC directory, the path to the latter
    directory is returned. Otherwise, ``None`` is returned.
    """

    meldir = getMelodicDir(path)
    sufs   =  ['.feat', '.gfeat', '.ica', '.gica']
    
    if meldir is None:
        return None

    if featresults.isFEATDir(meldir):
        return featresults.getFEATDir(meldir)

    parentDir = op.dirname(meldir)
    parentDir = parentDir.rstrip(op.sep)

    if not any([parentDir.endswith(s) for s in sufs]):
        return None

    # Must contain a file called filtered_func_data.nii.gz
    dataFile = op.join(parentDir, 'filtered_func_data')

    try:
        dataFile = fslimage.addExt(dataFile, mustExist=True)
    except ValueError:
        return None

    return parentDir

    
def getDataFile(meldir):
    """If the given melodic directory is contained within another analysis
    directory, the path to the data file is returned. Otherwise ``None`` is
    returned.
    """

    topDir = getTopLevelAnalysisDir(meldir)

    if topDir is None:
        return None

    dataFile = op.join(topDir, 'filtered_func_data')

    try:
        return fslimage.addExt(dataFile, mustExist=True)
    except ValueError:
        return None


def getICFile(meldir):
    """Returns the path to the melodic IC image. """
    return fslimage.addExt(op.join(meldir, 'melodic_IC'))


def getMixFile(meldir):
    """Returns the path to the melodic mix file. """
    return op.join(meldir, 'melodic_mix')


def getFTMixFile(meldir):
    """Returns the path to the melodic FT mix file. """
    return op.join(meldir, 'melodic_FTmix')


def getReportFile(meldir):
    pass


def getNumComponents(meldir):
    """Returns the number of components generated in the melodic analysis
    contained in the given directrory.
    """

    icImg = fslimage.Image(getICFile(meldir), loadData=False)
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



class MelodicClassification(props.HasProperties):
    """The ``MelodicClassification`` class is a convenience class for managing
    a collection of component classification labels.


    .. autosummary::
       :nosignatures:

       addLabel
       addComponent
       removeLabel
       removeComponent
       clearLabels
       clearComponents
    

    .. warning:: Do not modify the :attr:`labels` list directly - use the
                 methods listed above. A ``MelodicClassification`` needs to
                 manage some internal state whenever the component labels
                 change, so directly modifying the ``labels`` list will corrupt
                 this internal state.
    """

    
    labels = props.List()

    
    def __init__(self, ncomps):
        """Create a ``MelodicClassification`` instance.
        """

        self.__ncomps     = ncomps
        self.__components = {}
        self.labels       = [[] for i in range(ncomps)]
        

    def load(self, filename):
        pass

    
    def save(self, filename):
        pass 


    def getLabels(self, component):
        return list(self.labels[component])


    def hasLabel(self, component, label):
        return label in self.labels[component]
    

    def addLabel(self, component, label):

        labels = list(self.labels[component])
        comps  = list(self.__components.get(label, []))
        
        if label in labels:
            return 

        labels.append(label)
        comps .append(component)

        self.labels[      component] = labels
        self.__components[label]     = comps

        log.debug('Label added to component: {} <-> {}'.format(component,
                                                               label))
 

    def removeLabel(self, component, label):

        labels = list(self.labels[component])
        comps  = list(self.__components.get(label, []))

        if label not in labels:
            return

        labels.remove(label)
        comps .remove(component)
        
        self.labels[      component] = labels
        self.__components[label]     = comps

        log.debug('Label removed from component: {} <-> {}'.format(component,
                                                                   label))

    
    def clearLabels(self, component):
        
        labels = self.getLabels(component)

        self.disableNotification('labels')
        
        for l in labels:
            self.removeLabel(component, l)
            
        self.enableNotification('labels')
        self.notify('labels')

        log.debug('Labels cleared from component: {}'.format(component))

    
    def getComponents(self, label):
        return list(self.__components.get(label, []))

    
    def hasComponent(self, label, component):
        return component in self.getComponents(label)

    
    def addComponent(self, label, component):
        self.addLabel(component, label)


    def removeComponent(self, label, component):
        self.removeLabel(component, label)

    
    def clearComponents(self, label):
        
        components = self.getComponents(label)

        self.disableNotification('labels') 

        for c in components:
            self.removeComponent(label, c)
            
        self.enableNotification('labels')
        self.notify('labels')
