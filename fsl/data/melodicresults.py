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

   isMelodicImage
   isMelodicDir
   getTopLevelAnalysisDir
   getDataFile
   getICFile
   getMixFile
   getFTMixFile
   getNumComponents
   getComponentTimeSeries
   getComponentPowerSpectra


The :class:`MelodicClassification` class is also defined in this module. This
class is used to manage component classifications of a :class:`.MelodicImage`.
"""


import logging

import os.path as op
import numpy   as np

import props

import fsl.data.image as fslimage


log = logging.getLogger(__name__)


def isMelodicImage(path):
    """Returns ``True`` if the given path looks like it is a melodic
    component image file, ``False`` otherwise. 
    """

    
    dirname  = op.dirname( path)
    filename = op.basename(path)

    return filename.startswith('melodic_IC') and isMelodicDir(dirname)
 

def isMelodicDir(path):
    """Returns ``True`` if the given path looks like it is contained within
    a MELODIC directory, ``False`` otherwise. A melodic directory:

      - Must be named ``*.ica``.
      - Must contain a file called ``melodic_IC.nii.gz``.
      - Must contain a file called ``melodic_mix``.
      - Must contain a file called ``melodic_FTmix``.
    """

    path = op.abspath(path)
    
    if op.isdir(path): dirname = path
    else:              dirname = op.dirname(path)

    if not dirname.endswith('.ica'):
        return False

    # Must contain an image file called melodic_IC
    try:
        fslimage.addExt(op.join(dirname, 'melodic_IC'), mustExist=True)
    except ValueError:
        return False

    # Must contain files called
    # melodic_mix and melodic_FTmix
    if not op.exists(op.join(dirname, 'melodic_mix')):   return False
    if not op.exists(op.join(dirname, 'melodic_FTmix')): return False
 
    return True


def getTopLevelAnalysisDir(path):
    """If the given path is a MELODIC directory, and it is contained within
    a FEAT directory, or another MELODIC directory, the path to the latter
    directory is returned. Otherwise, ``None`` is returned.
    """

    path = path.strip()

    # We've reached the root of the file system
    if path == op.sep or path == '':
        return None

    path   = path.rstrip(op.sep)
    parent = getTopLevelAnalysisDir(op.dirname(path))

    if parent is not None:
        return parent

    sufs = ['.ica', '.gica', '.feat', '.gfeat']

    if any([path.endswith(suf) for suf in sufs]):
        return path

    return None

    
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

       hasLabel
       hasComponent
       getLabels
       getComponents
       addLabel
       addComponent
       removeLabel
       removeComponent
       clearLabels
       clearComponents


    .. note::    All component labels are internally stored as lower case;
                 their cased version (whatever is initially used) is accssible
                 via the :meth:`getDisplayLabel` method.
    

    .. warning:: Do not modify the :attr:`labels` list directly - use the
                 methods listed above. A ``MelodicClassification`` needs to
                 manage some internal state whenever the component labels
                 change, so directly modifying the ``labels`` list will corrupt
                 this internal state.
    """

    
    labels = props.List()
    """A list of lists, one for each component, which contains the labels that
    have been added to that component. Do not modify this list directly.
    However, feel free to register a listener to be notified when this list
    changes.
    """

    
    def __init__(self, melimage):
        """Create a ``MelodicClassification`` instance.
        """

        self.__melimage      = melimage
        self.__ncomps        = melimage.numComponents()
        self.__displayLabels = {}

        self.clear()


    def getDisplayLabel(self, label):
        """Returns the display name for the given label. """
        return self.__displayLabels.get(label.lower(), label)


    def clear(self):
        """Removes all labels from all components. """

        notifState = self.getNotificationState('labels')
        self.disableNotification('labels')
        
        self.__components = {}
        self.labels       = [[] for i in range(self.__ncomps)]
        
        self.setNotificationState('labels', notifState)
        self.notify('labels')
        

    def load(self, filename):
        """Loads component labels from the specified file. The file is assuemd
        to be of the format generated by FIX or Melview; such a file should
        have a structure resembling the following::

            filtered_func_data.ica
            1, Signal, False
            2, Unclassified Noise, True
            3, Unknown, False
            4, Signal, False
            5, Unclassified Noise, True
            6, Unclassified Noise, True
            7, Unclassified Noise, True
            8, Signal, False
            [2, 5, 6, 7]

        The first line of the file contains the name of the melodic directory.
        Then, one line is present for each component, containing the following,
        separated by commas:
        
          - The component index (starting from 1).
          - One or more labels for the component (multiple labels must be
            comma-separated).
          - ``'True'`` if the component has been classified as *bad*,
            ``'False'`` otherwise.
            
        The last line of the file contains the index (starting from 1) of all
        *bad* components, i.e. those components which are not classified as
        signal or unknown.


        .. note:: This method adds to, but does not replace, any existing
                  component classifications stored by this
                  ``MelodicClassification``. Call the :meth:`clear` method,
                  before calling ``load``, if you want to discard any existing
                  classifications.
        """

        with open(filename, 'rt') as f:
            lines = f.readlines()

        if len(lines) < 3:
            raise InvalidFixFileError('Invalid FIX classification '
                                      'file - not enough lines')

        lines = [l.strip() for l in lines]

        # Ignore the first and last
        # lines - we're only interested
        # in the component labels
        compLines = lines[1:-1]

        if len(compLines) != self.__ncomps:
            raise InvalidFixFileError('Invalid FIX classification '
                                      'file - number of components '
                                      'do not match')

        # Parse the labels for every component
        # We dot not add the labels as we go
        # as, if something is wrong with the
        # file contents, we don't want this
        # MelodicClassification instance to
        # be modified. So we'll assign the
        # labels afterwards
        allLabels = []
        for i, compLine in enumerate(compLines):
            
            tokens = compLine.split(',')
            tokens = [t.strip() for t in tokens]
            
            if len(tokens) < 3:
                raise InvalidFixFileError('Invalid FIX classification '
                                          'file - component line {} does '
                                          'not have enough '
                                          'tokens'.format(i + 1))

            compIdx    = int(tokens[0])
            compLabels = tokens[1:-1]

            if compIdx != i + 1:
                raise InvalidFixFileError('Invalid FIX classification '
                                          'file - component line {} has '
                                          'wrong component number '
                                          '({})'.format(i, compIdx))

            allLabels.append(compLabels)

        # Now that all the labels are
        # read in, we can store them
        notifState = self.getNotificationState('labels')
        self.disableNotification('labels')

        for i, labels in enumerate(allLabels):
            for label in labels:
                self.addLabel(i, label)
                
        self.setNotificationState('labels', notifState)
        self.notify('labels')

    
    def save(self, filename):
        """Saves the component classifications stored by this
        ``MeloidicClassification`` to the specified file. The classifications
        are saved in the format described in the :meth:`load` method.

        .. TODO:: Accept a dictionary of ``{label : display label}`` mappings,
                  so we can output cased labels (e.g. ``'Signal'`` instead of
                  ``'signal'``).
        """

        lines    = []
        badComps = []
        image    = self.__melimage

        # The first line - the melodic directory name
        lines.append(op.basename(image.getMelodicDir()))

        # A line for each component
        for comp in range(self.__ncomps):
            
            noise  = not (self.hasLabel(comp, 'signal') or
                          self.hasLabel(comp, 'unknown'))

            # Make sure there are no
            # commas in any label names
            labels = [self.getDisplayLabel(l) for l in self.getLabels(comp)]
            labels = [l.replace(',', '_') for l in labels]
            
            tokens = [str(comp + 1)] + labels + [str(noise)]

            lines.append(', '.join(tokens))

            if noise:
                badComps.append(comp)

        # A line listing the bad components
        lines.append('[' + ', '.join([str(c + 1) for c in badComps]) + ']')

        with open(filename, 'wt') as f:
            f.write('\n'.join(lines) + '\n')


    def getLabels(self, component):
        """Returns all labels of the specified component. """
        return list(self.labels[component])


    def hasLabel(self, component, label):
        """Returns ``True`` if the specified component has the specified label,
        ``False`` otherwise.
        """
        label = label.lower()
        return label in self.labels[component]
    

    def addLabel(self, component, label):
        """Adds the given label to the given component. """

        display = label
        label   = label.lower()
        labels  = list(self.labels[component])
        comps   = list(self.__components.get(label, []))
        
        if label in labels:
            return 

        labels.append(label)
        comps .append(component)

        self.__displayLabels[label] = display

        # Change __components first, so
        # any listeners on labels are
        # not notified before our intenral
        # state becomes consistent
        self.__components[label]     = comps        
        self.labels[      component] = labels

        log.debug('Label added to component: {} <-> {}'.format(component,
                                                               label))
 

    def removeLabel(self, component, label):
        """Removes the given label from the given component. """

        label  = label.lower()
        labels = list(self.labels[component])
        comps  = list(self.__components.get(label, []))

        if label not in labels:
            return

        labels.remove(label)
        comps .remove(component)

        self.__components[label]     = comps        
        self.labels[      component] = labels

        log.debug('Label removed from component: {} <-> {}'.format(component,
                                                                   label))

    
    def clearLabels(self, component):
        """Removes all labels from the given component. """
        
        labels = self.getLabels(component)

        self.disableNotification('labels')
        
        for l in labels:
            self.removeLabel(component, l)
            
        self.enableNotification('labels')
        self.notify('labels')

        log.debug('Labels cleared from component: {}'.format(component))

    
    def getComponents(self, label):
        """Returns a list of all components which have the given label. """
        label = label.lower()
        return list(self.__components.get(label, []))

    
    def hasComponent(self, label, component):
        """Returns ``True`` if the given compoennt has the given label,
        ``False`` otherwise.
        """
        return component in self.getComponents(label)

    
    def addComponent(self, label, component):
        """Adds the given label to the given component. """
        self.addLabel(component, label)


    def removeComponent(self, label, component):
        """Removes the given label from the given component. """
        self.removeLabel(component, label)

    
    def clearComponents(self, label):
        """Removes the given label from all components. """
        
        components = self.getComponents(label)

        self.disableNotification('labels') 

        for c in components:
            self.removeComponent(label, c)
            
        self.enableNotification('labels')
        self.notify('labels')


class InvalidFixFileError(Exception):
    """
    """
    pass
