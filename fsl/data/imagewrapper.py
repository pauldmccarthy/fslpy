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

    def __init__(self, image, name=None):
        """

        :arg image: A ``nibabel.Nifti1Image``.

        :arg name:  A name for this ``ImageWrapper``, solely used for debug
                    log messages.
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
        self.__rangeCover = [[-1, -1] for i in range(len(image.shape))]

        
    @property
    def dataRange(self):
        return tuple(self.__range)


    def __rangeCovered(self, slices):
        """Returns ``True`` if the range for the image data calculated by
        the given ``slices` has already been calculated, ``False`` otherwise.
        """

        if self.__range == (None, None):
            return False

        # TODO You could adjust the slice so that 
        #      it only spans the portion of the 
        #      image that has not yet been covered.
        for dim, size in enumerate(self.__image.shape):

            lowCover, highCover = self.__rangeCover[dim]

            if lowCover == -1 or highCover == -1:
                return False

            lowSlice, highSlice = slices[dim]

            if lowSlice  is None: lowSlice  = 0
            if highSlice is None: highSlice = self.__image.shape[dim]
            
            if lowSlice  < lowCover:  return False
            if highSlice > highCover: return False

        return True


    def __updateCoveredRange(self, slices):
        """
        """

        for dim, (lowSlice, highSlice) in enumerate(slices):

            lowCover, highCover = self.__rangeCover[dim]

            if lowSlice  is None: lowSlice  = 0
            if highSlice is None: highSlice = self.__image.shape[dim]

            if lowSlice  < lowCover:  lowCover  = lowSlice
            if highSlice > highCover: highCover = highSlice

            self.__rangeCover[dim] = [lowCover, highCover]


    @memoize.Instanceify(memoize.memoize(args=[0]))
    def __updateRangeOnRead(self, slices, data):

        oldmin, oldmax = self.__range

        dmin = np.nanmin(data)
        dmax = np.nanmax(data)

        if oldmin is None: oldmin = dmin
        if oldmax is None: oldmax = dmax

        if dmin < oldmin: newmin = dmin
        else:             newmin = oldmin

        if dmax > oldmax: newmax = dmax
        else:             newmax = oldmax

        self.__range = (newmin, newmax)
        self.__updateCoveredRange(slices)

        if newmin != oldmin or newmax != oldmax:

            log.debug('Image {} data range adjusted: {} - {}'.format(
                self.__name, newmin, newmax))
            self.notify()

    
    # def __updateRangeOnWrite(self, oldvals, newvals):
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

        # If the image has noy been loaded
        # into memory,  we can use the nibabel
        # ArrayProxy. Otheriwse if it is in
        # memory, we can access it directly.
        #
        # Furthermore, if it is in memory and
        # has been modified, the ArrayProxy
        # will give us out-of-date values (as
        # the ArrayProxy reads from disk). So
        # we have to read from the in-memory
        # array.
        if self.__image.in_memory: data = self.__image.get_data()[sliceobj]
        else:                      data = self.__image.dataobj[   sliceobj]

        slices = tuple((s.start, s.stop) if isinstance(s, slice)
                  else (s, s + 1)
                  for s in sliceobj)

        if not self.__rangeCovered(slices):
            self.__updateRangeOnRead(slices, data)

        return data


    # def __setitem__(self, sliceobj, values):
        
    #     sliceobj = nib.fileslice.canonical_slicers(
    #         sliceobj, self.__image.shape)

    #     # This will cause the whole image to be
    #     # loaded into memory and cached by nibabel
    #     # (if it has not already done so).
    #     self.__image.get_data()[sliceobj] = values

    #     self.__updateRangeOnWrite(values)
