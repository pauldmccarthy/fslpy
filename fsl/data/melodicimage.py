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

from . import image           as fslimage
from . import melodicanalysis as melanalysis


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


    The :attr:`tr` time of the ``MelodicImage`` may not be known when it is
    created. If it is updated at a later time, the ``MelodicImage`` will
    notify any listeners which are registerd on the ``'tr'`` topic (see the
    :class:`.Notifier` interface).
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

        if not melanalysis.isMelodicImage(path):
            raise ValueError('{} does not appear to be a '
                             'MELODIC component file'.format(path))

        fslimage.Image.__init__(self, path, *args, **kwargs)

        meldir            = op.dirname(path)
        self.__tr         = 1.0
        self.__meldir     = meldir
        self.__melmix     = melanalysis.getComponentTimeSeries(  meldir)
        self.__melFTmix   = melanalysis.getComponentPowerSpectra(meldir)

        # Automatically set the
        # TR value if possible
        dataFile = self.getDataFile()

        if dataFile is not None:
            dataImage = fslimage.Image(dataFile,
                                       loadData=False,
                                       calcRange=False)
            if dataImage.is4DImage():
                self.__tr = dataImage.pixdim[3]


    @property
    def tr(self):
        """The TR time of the raw data from which this ``MelodicImage`` was
        generated. If it is possible to do so, this is automatically
        initialised from the data file (see the :meth:`getDataFile` method).
        """
        return self.__tr


    @tr.setter
    def tr(self, val):
        """Set the :attr:`tr` time for this ``MelodicImage``. Any listeners
        registered on the ``'tr'`` topic are notified of the update.
        """
        oldval = self.__tr
        self.__tr = val

        if oldval != val:
            self.notify(topic='tr')


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


    def getReportFile(self):
        """Returns the path to the MELODIC report - see
        :func:`.melodicanalysis.getReportFile`.
        """
        return melanalysis.getReportFile(self.__meldir)


    def getTopLevelAnalysisDir(self):
        """Returns the top level analysis, if the melodic analysis for this
        ``MelodicImage`` is contained within another analysis. Otherwise,
        returns ``None``. See the
        :func:`.melodicanalysis.getTopLevelAnalysisDir` function.
        """
        return melanalysis.getTopLevelAnalysisDir(self.__meldir)


    def getDataFile(self):
        """Returns the file name of the data image from which this
        ``MelodicImage`` was generated, if possible. See the
        :func:`.melodicanalysis.getDataFile` function.
        """
        return melanalysis.getDataFile(self.__meldir)


    def getMeanFile(self):
        """Returns the file name of the mean data image associated with this
        ``MelodicImage``. See the :func:`.melodicanalysis.getMeanFile`
        function.
        """
        return melanalysis.getMeanFile(self.__meldir)
