#!/usr/bin/env python
#
# melodicimage.py - An Image subclass which has some MELODIC-specific
# functionality.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`MelodicImage` class, an :class:`.Image`
sub-class which encapsulates data from a MELODIC analysis.
"""


import os.path as op

import props

from . import image          as fslimage
from . import melodicresults as melresults


class MelodicImage(fslimage.Image):
    """The ``MelodicImage`` class is an :class:`.Image` which encapsulates
    the results of a FSL MELODIC analysis. A ``MelodicImage`` corresponds to
    the spatial component map file, generally called ``melodic_IC.nii.gz``.

    The ``MelodicImage`` class provides a few MELODIC-specific attributes and
    methods:

    
    .. autosummary::
       :nosignatures:

       tr
       getComponentTimeSeries
       getComponentPowerSpectrum
       numComponents
       getMelodicDir
       getTopLevelAnalysisDir
       getDataFile
       getICClassification
    """


    tr = props.Real(default=1.0)
    """The TR time of the raw data from which this ``MelodicImage`` was
    generated. If it is possible to do so, this is automatically initialised
    from the data file (see the :meth:`getDataFile` method).
    """
    

    def __init__(self, path, *args, **kwargs):
        """Create a ``MelodicImage``.

        :arg path: A path specifying the ``melodic_IC`` image file, or the
                   ``.ica`` directory.

        All other arguments are passed through to the :meth:`.Image.__init__`
        method.
        """

        if op.isdir(path):
            path = op.join(path, 'melodic_IC')

        if not melresults.isMelodicImage(path):
            raise ValueError('{} does not appear to be a '
                             'MELODIC component file'.format(path)) 
            
        fslimage.Image.__init__(self, path, *args, **kwargs)

        meldir            = op.dirname(path)
        self.__meldir     = meldir
        self.__melmix     = melresults.getComponentTimeSeries(  meldir)
        self.__melFTmix   = melresults.getComponentPowerSpectra(meldir)
        self.__melICClass = melresults.MelodicClassification(   self)

        # Automatically set the
        # TR value if possible
        dataFile = self.getDataFile()

        if dataFile is not None: 
            dataImage = fslimage.Image(dataFile, loadData=False)
            if dataImage.is4DImage():
                self.tr = dataImage.pixdim[3]

        # TODO load classifications if present
        for i in range(self.numComponents()):
            self.__melICClass.addLabel(i, 'Unknown')

        
    def getComponentTimeSeries(self, component):
        """Returns the time course for the specified (0-indexed) component. """
        return self.__melmix[:, component]

    
    def getComponentPowerSpectrum(self, component):
        """Returns the power spectrum for the time course of the specified
        (0-indexed) component.
        """
        return self.__melFTmix[:, component] 


    def numComponents(self):
        """Returns the number of components in this ``MelodicImage``. """
        return self.shape[3]

    
    def getMelodicDir(self):
        """Returns the melodic output directory in which this image is
        contained.
        """
        return self.__meldir
    

    def getTopLevelAnalysisDir(self):
        """Returns the top level analysis, if the melodic analysis for this
        ``MelodicImage`` is contained within another analysis. Otherwise,
        returns ``None``. See the
        :func:`.melodicresults.getTopLevelAnalysisDir` function.
        """
        return melresults.getTopLevelAnalysisDir(self.__meldir)


    def getDataFile(self):
        """Returns the file name of the data image from which this
        ``MelodicImage`` was generated, if possible. See the
        :func:`.melodicresults.getDataFile` function.
        """
        return melresults.getDataFile(self.__meldir)


    def getMeanFile(self):
        """Returns the file name of the mean data image associated with this
        ``MelodicImage``. See the :func:`.melodicresults.getMeanFile` function.
        """
        return melresults.getMeanFile(self.__meldir) 


    def getICClassification(self):
        """Return the :class:`.MelodicClassification` instance associated with
        this ``MelodicImage``.
        """
        return self.__melICClass
