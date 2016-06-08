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

        # Save the number of 'real' dimensions,
        # that is the number of dimensions minus
        # any trailing dimensions of length 1
        self.__numRealDims = len(image.shape)
        for d in reversed(image.shape):
            if d == 1: self.__numRealDims -= 1
            else:      break

        # And save the number of
        # 'padding' dimensions too.
        self.__numPadDims = len(image.shape) - self.__numRealDims

        hdr = image.get_header()

        # The current known image data range. This
        # gets updated as more image data gets read.
        # We default to whatever is stored in the
        # header (which may or may not contain useful
        # values).
        self.__range = (float(hdr['cal_min']), float(hdr['cal_max']))

        # For each entry in the last (real) dimension of
        # the image (slice for 3D or volume for 4D), we
        # record the portions of the image that have
        # been included in the data range calculation, so
        # we do not unnecessarily re-calculate ranges on
        # the same part of the image.
        self.__sliceCoverage = []
        
        # This is a list of lists of (low, high) pairs,
        # one list for each entry in the last dimension
        # (e.g. one list per 2D slice or 3D volume), and
        # one pair for each dimension in the entry (e.g.
        # row/column for each slice, or row/column/depth
        # for each volume).
        for i in range(image.shape[self.__numRealDims - 1]):

            cov = [[None, None] for i in range(self.__numRealDims - 1)]
            self.__sliceCoverage.append(cov)

        if loadData:
            self.loadData()

        
    @property
    def dataRange(self):
        """Returns the currently known data range as a tuple of ``(min, max)``
        values.
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


    def __getData(self, sliceobj, isTuple=False):
        """
        """

        if isTuple:
            sliceobj = sliceTupletoSliceObj(sliceobj)

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
        if self.__image.in_memory: return self.__image.get_data()[sliceobj]
        else:                      return self.__image.dataobj[   sliceobj] 


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
        
        :arg data:   The image data at the given ``slices`` (as a ``numpy``
                     array).
        """

        oldmin, oldmax = self.__range

        log.debug('Updating image {} data range (current range: '
                  '[{}, {}]; current coverage: {})'.format(
                      self.__name,
                      self.__range[0],
                      self.__range[1],
                      self.__sliceCoverage))

        volumes, expansions = calcSliceExpansion(slices,
                                                 self.__sliceCoverage,
                                                 self.__numRealDims,
                                                 self.__numPadDims)

        newmin = oldmin
        newmax = oldmax

        for vol, exp in zip(volumes, expansions):

            data = self.__getData(exp, isTuple=True)
            dmin = float(np.nanmin(data))
            dmax = float(np.nanmax(data))

            if newmin is None or dmin < newmin: newmin = dmin
            if newmax is None or dmax > newmax: newmax = dmax

        self.__range = (newmin, newmax)

        for vol, exp in zip(volumes, expansions):
            self.__sliceCoverage[vol] = adjustSliceCoverage(
                self.__sliceCoverage[vol],
                exp,
                self.__numRealDims)

        # TODO floating point error
        if newmin != oldmin or newmax != oldmax:
            log.debug('Image {} range changed: [{}, {}] -> [{}, {}]'.format(
                self.__name,
                oldmin,
                oldmax,
                newmin,
                newmax))
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

        data = self.__getData(sliceobj)

        # TODO If full range is 
        #      known, return now.

        slices = sliceObjToSliceTuple(sliceobj, self.__image.shape)

        if not sliceCovered(slices,
                            self.__sliceCoverage,
                            self.__image.shape,
                            self.__numRealDims):
            
            self.__updateDataRangeOnRead(slices, data)

        return data



def sliceObjToSliceTuple(sliceobj, shape):
    """Turns an array slice object into a tuple of (low, high) index
    pairs, one pair for each dimension in the given shape
    """

    indices = []

    for dim, s in enumerate(sliceobj):

        # each element in the slices tuple should 
        # be a slice object or an integer
        if isinstance(s, slice): i = [s.start, s.stop]
        else:                    i = [s,       s + 1]

        if i[0] is None: i[0] = 0
        if i[1] is None: i[1] = shape[dim]

        indices.append(tuple(i))

    return tuple(indices)


def sliceTupletoSliceObj(slices):
    """
    """

    sliceobj = []

    for lo, hi in slices:
        sliceobj.append(slice(lo, hi, 1))

    return tuple(sliceobj)



def sliceCovered(slices, sliceCoverage, shape, realDims):
    """Returns ``True`` if the portion of the image data calculated by
    the given ``slices` has already been calculated, ``False`` otherwise.
    """

    lowVol, highVol = slices[realDims - 1]
    shape           = shape[:realDims - 1]

    for vol in range(lowVol, highVol):

        coverage = sliceCoverage[vol]

        for dim, size in enumerate(shape):

            lowCover, highCover = coverage[dim]

            if lowCover is None or highCover is None:
                return False

            lowSlice, highSlice = slices[dim]

            if lowSlice  is None: lowSlice  = 0
            if highSlice is None: highSlice = size

            if lowSlice  < lowCover:  return False
            if highSlice > highCover: return False

    return True


def calcSliceExpansion(slices, sliceCoverage, realDims, padDims):
    """
    """

    # One per volume
    lowVol, highVol = slices[realDims - 1] 

    expansions = []
    volumes    = list(range(lowVol, highVol))

    # TODO Reduced slice duplication.
    #      You know what this means.

    for vol in volumes:

        coverage  = sliceCoverage[vol]
        expansion = []

        for dim in range(realDims - 1):

            lowCover, highCover = coverage[dim]
            lowSlice, highSlice = slices[  dim]

            if lowCover  is None: lowCover  = lowSlice
            if highCover is None: highCover = highSlice

            expansion.append((min(lowCover,  lowSlice),
                              max(highCover, highSlice)))

        expansion.append((vol, vol + 1))
        for i in range(padDims):
            expansion.append((0, 1))

        expansions.append(expansion)

    return volumes, expansions


def adjustSliceCoverage(oldCoverage, slices, realDims): 
    """
    """

    newCoverage = []

    for dim in range(realDims - 1):

        low,      high      = slices[     dim]
        lowCover, highCover = oldCoverage[dim]

        if lowCover  is None or low  < lowCover:  lowCover  = low
        if highCover is None or high < highCover: highCover = high

        newCoverage.append((lowCover, highCover))

    return newCoverage
