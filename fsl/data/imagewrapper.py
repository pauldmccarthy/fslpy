#!/usr/bin/env python
#
# imagewrapper.py - The ImageWrapper class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ImageWrapper` class,
"""


import logging 

import numpy   as np
import nibabel as nib

import fsl.utils.notifier as notifier
import fsl.utils.memoize  as memoize


log = logging.getLogger(__name__)


class ImageWrapper(notifier.Notifier):
    """

    Incrementally updates the data range as more image data is accessed.
    """

    def __init__(self, image, name=None, loadData=False):
        """

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
        """
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
        """

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

        dmin = np.nanmin(data)
        dmax = np.nanmax(data)

        if oldmin is None: oldmin = dmin
        if oldmax is None: oldmax = dmax

        if dmin < oldmin: newmin = dmin
        else:             newmin = oldmin

        if dmax > oldmax: newmax = dmax
        else:             newmax = oldmax

        self.__range = (newmin, newmax)
        self.__updateSliceCoverage(slices)

        if newmin != oldmin or newmax != oldmax:
            log.debug('Image {} range changed: [{}, {}]'.format(
                self.__name, self.__range[0], self.__range[1]))
            self.notify()

    
    # def __updateDataRangeOnWrite(self, oldvals, newvals):
    #     """Called by :meth:`__setitem__`. Re-calculates the image data
    #     range, and returns a tuple containing the ``(min, max)`` values.
    #     """

    #     # The old known image wide data range.
    #     oldmin, oldmax = self.dataRange

    #     # The data range of the changed sub-array.
    #     newvalmin = np.nanmin(newvals)
    #     newvalmax = np.nanmax(newvals)

    #     # Has the entire image been updated?
    #     wholeImage = tuple(newvals.shape) == tuple(self.image.shape)

    #     # If the minimum of the new values
    #     # is less than the old image minimum, 
    #     # then it becomes the new minimum.
    #     if (newvalmin <= oldmin) or wholeImage:
    #         newmin = newvalmin

    #     # Or, if the old minimum is being
    #     # replaced by the new values, we
    #     # need to re-calculate the minimum
    #     # from scratch.
    #     elif np.nanmin(oldvals) == oldmin:
    #         newmin = None

    #     # Otherwise, the image minimum
    #     # has not changed.
    #     else:
    #         newmin = oldmin

    #     # The same logic applies to the maximum.
    #     if   (newvalmax >= oldmax) or wholeImage: newmax = newvalmax
    #     elif np.nanmax(oldvals) == oldmax:        newmax = None
    #     else:                                     newmax = oldmax

    #     if newmin is not None and np.isnan(newmin): newmin = oldmin
    #     if newmax is not None and np.isnan(newmax): newmax = oldmax

    #     if newmin != oldmin or newmax != oldmax:

    #         log.debug('Image {} data range adjusted: {} - {}'.format(
    #             self.__name, newmin, newmax))
    #         self.notify() 
    

    def __getitem__(self, sliceobj):
        """
        """

        sliceobj = nib.fileslice.canonical_slicers(
            sliceobj, self.__image.shape)

        # TODO Cache 3D images for large 4D volumes, 
        #      so you don't have to hit the disk

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


    # def __setitem__(self, sliceobj, values):
        
    #     sliceobj = nib.fileslice.canonical_slicers(
    #         sliceobj, self.__image.shape)

    #     # This will cause the whole image to be
    #     # loaded into memory and cached by nibabel
    #     # (if it has not already done so).
    #     self.__image.get_data()[sliceobj] = values

    #     self.__updateDataRangeOnWrite(values)
