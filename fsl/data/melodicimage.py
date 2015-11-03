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

import image          as fslimage
import melodicresults as melresults


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
       getTopLevelAnalysisDir
       getDataFile
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
            dirname  = path
            filename = 'melodic_IC'

        else:
            dirname  = op.dirname( path)
            filename = op.basename(path)

        dirname = dirname.rstrip(op.sep)

        if not melresults.isMelodicDir(dirname):
            raise ValueError('{} does not appear to be a '
                             'MELODIC directory'.format(dirname)) 
        
        if not filename.startswith('melodic_IC'):
            raise ValueError('{} does not appear to be a MELODIC '
                             'component file'.format(filename))
            
        fslimage.Image.__init__(self,
                                op.join(dirname, filename),
                                *args,
                                **kwargs)

        self.__meldir     = dirname
        self.__melmix     = melresults.getComponentTimeSeries(  dirname)
        self.__melFTmix   = melresults.getComponentPowerSpectra(dirname)
        self.__melICClass = melresults.MelodicClassification(
            self.numComponents())

        # Automatically set the
        # TR value if possible
        dataFile = self.getDataFile()

        if dataFile is not None: 
            dataImage = fslimage.Image(dataFile, loadData=False)
            if dataImage.is4DImage():
                self.tr = dataImage.pixdim[3]

        # TODO load classifications if present

        
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


    def getTopLevelAnalysisDir(self):
        """Returns the top level analysis, if the melodic analysis for this
        ``MelodicImage`` is contained within another analysis. Otherwise,
        returnsa ``None``. See the
        :func:`.melodicresults.getTopLevelAnalysisDir` function.
        """
        return melresults.getTopLevelAnalysisDir(self.__meldir)


    def getDataFile(self):
        """Returns the file name of the data image from which this
        ``MelodicImage`` was generated, if possible. See the
        :func:`.melodicresults.getDataFile` function.
        """
        return melresults.getDataFile(self.__meldir)


    def getICClassification(self):
        return self.__melICClass
