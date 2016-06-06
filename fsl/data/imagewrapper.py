#!/usr/bin/env python
#
# imagewrapper.py - The ImageWrapper class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ImageWrapper` class, which can be used
to manage data access to ``nibabel`` NIFTI images.
"""


import logging 

import numpy   as np
import nibabel as nib

import fsl.utils.notifier as notifier
import fsl.utils.memoize  as memoize


log = logging.getLogger(__name__)


class ImageWrapper(notifier.Notifier):
    """The ``ImageWrapper`` class is a convenience class which manages data
    access to ``nibabel`` NIFTI images. The ``ImageWrapper`` class can be
    used to:
    
      - Control whether the image is loaded into memory, or kept on disk
    
      - Incrementally update the known image  data range, as more image
        data is read in.


    The ``ImageWrapper`` implements the :class:`.Notifier` interface.
    Listeners can register to be notified whenever the known image data range
    is updated. The data range can be accessed via the :attr:`dataRange`
    property.


    .. todo:: Figure out if NIFTI2 can be supported as well.
    """

    def __init__(self, image, name=None, loadData=False):
        """Create an ``ImageWrapper``.

        :arg image:    A ``nibabel.Nifti1Image``.

        :arg name:     A name for this ``ImageWrapper``, solely used for debug
                       log messages.

        :arg loadData: If ``True``, the image data is loaded into memory.
                       Otherwise it is kept on disk (and data access is
                       performed through the ``nibabel.Nifti1Image.dataobj``
                       array proxy).
        """
        
        self.__image = image
        self.__name  = name

        # The current known image data range. This
        # gets updated as more image data gets read.
        self.__range = None, None

        # We record the portions of the image that have
        # been included in the data range calculation, so
        # we do not unnecessarily re-calculate ranges on
        # the same part of the image. This is a list of
        # (low, high) pairs, one pair for each dimension
        # in the image data.
        self.__sliceCoverage = [[None, None] for i in range(len(image.shape))]

        if loadData:
            self.loadData()

        
    @property
    def dataRange(self):
        """Returns the currently known data range as a tuple of ``(min, max)``
        values.

        If the data range is completely unknown, returns ``(None, None)``.
        """
        return tuple(self.__range)


    def loadData(self):
        """Forces all of the image data to be loaded into memory.

        .. note:: This method will be called by :meth:`__init__` if its
                  ``loadData`` parameter is ``True``.
        """

        # If the data is not already
        # loaded, this will cause 
        # nibabel to load and cache it
        self.__image.get_data()


    def __sanitiseSlices(self, slices):
        """Turns an array slice object into a tuple of (low, high) index
        pairs, one pair for each dimension in the image data.
        """
        
        indices = []

        for dim, s in enumerate(slices):

            # each element in the slices tuple should 
            # be a slice object or an integer
            if isinstance(s, slice): i = [s.start, s.stop]
            else:                    i = [s,       s + 1]

            if i[0] is None: i[0] = 0
            if i[1] is None: i[1] = self.__image.shape[dim]

            indices.append(tuple(i))

        return tuple(indices)


    def __sliceCovered(self, slices):
        """Returns ``True`` if the portion of the image data calculated by
        the given ``slices` has already been calculated, ``False`` otherwise.
        """

        if self.__range == (None, None):
            return False

        # TODO You could adjust the slice so that 
        #      it only spans the portion of the 
        #      image that has not yet been covered,
        #      and return it to minimise the portion
        #      of the image over which the range is
        #      updated.
        for dim, size in enumerate(self.__image.shape):

            lowCover, highCover = self.__sliceCoverage[dim]

            if lowCover is None or highCover is None:
                return False

            lowSlice, highSlice = slices[dim]

            if lowSlice  is None: lowSlice  = 0
            if highSlice is None: highSlice = self.__image.shape[dim]
            
            if lowSlice  < lowCover:  return False
            if highSlice > highCover: return False

        return True


    def __updateSliceCoverage(self, slices):
        """Updates the known portion of the image (with respect to the image
        data range) according to the given set of slice indices.

        :arg slices: A sequence of ``(low, high)`` index pairs, one for each
                     dimension in the image. 
        """

        for dim, (lowSlc, highSlc) in enumerate(slices):

            lowCov, highCov = self.__sliceCoverage[dim]

            if lowSlc  is None: lowSlc  = 0
            if highSlc is None: highSlc = self.__image.shape[dim]

            if lowCov  is None or lowSlc  < lowCov:  lowCov  = lowSlc
            if highCov is None or highSlc > highCov: highCov = highSlc

            self.__sliceCoverage[dim] = [lowCov, highCov]


    @memoize.Instanceify(memoize.memoize(args=[0]))
    def __updateDataRangeOnRead(self, slices, data):
        """Called by :meth:`__getitem__`. Calculates the minimum/maximum
        values of the given data (which has been extracted from the portion of
        the image specified by ``slices``), and updates the known data range
        of the image.

        :arg slices: A sequence of ``(low, high)`` index pairs, one for each
                     dimension in the image. Tuples are used instead of
                     ``slice`` objects, because this method is memoized (and
                     ``slice`` objects are unhashable).
        """

        oldmin, oldmax = self.__range

        log.debug('Updating image {} data range (current range: '
                  '[{}, {}]; current coverage: {})'.format(
                      self.__name,
                      self.__range[0],
                      self.__range[1],
                      self.__sliceCoverage))

        dmin = float(np.nanmin(data))
        dmax = float(np.nanmax(data))

        if oldmin is None or dmin < oldmin: newmin = dmin
        else:                               newmin = oldmin

        if oldmax is None or dmax > oldmax: newmax = dmax
        else:                               newmax = oldmax

        self.__range = (newmin, newmax)
        self.__updateSliceCoverage(slices)

        if newmin != oldmin or newmax != oldmax:
            log.debug('Image {} range changed: [{}, {}]'.format(
                self.__name, self.__range[0], self.__range[1]))
            self.notify()


    def __getitem__(self, sliceobj):
        """Returns the image data for the given ``sliceobj``, and updates
        the known image data range if necessary.

        .. note:: If the image data is in memory, it is accessed 
                  directly, via the ``nibabel.Nifti1Image.get_data`` 
                  method. Otherwise the image data is accessed through 
                  the ``nibabel.Nifti1Image.dataobj`` array proxy.

        :arg sliceobj: Something which can slice the image data.
        """

        log.debug('Getting image data: {}'.format(sliceobj))

        sliceobj = nib.fileslice.canonical_slicers(
            sliceobj, self.__image.shape)

        # TODO Cache 3D images for large 4D volumes, 
        #      so you don't have to hit the disk?

        # If the image has not been loaded
        # into memory,  we can use the nibabel
        # ArrayProxy. Otheriwse if it is in
        # memory, we can access it directly.
        #
        # Furthermore, if it is in memory and
        # has been modified, the ArrayProxy
        # will give us out-of-date values (as
        # the ArrayProxy reads from disk). So
        # we have to read from the in-memory
        # array to get changed values.
        if self.__image.in_memory: data = self.__image.get_data()[sliceobj]
        else:                      data = self.__image.dataobj[   sliceobj]

        slices = self.__sanitiseSlices(sliceobj)

        if not self.__sliceCovered(slices):
            self.__updateDataRangeOnRead(slices, data)

        return data
