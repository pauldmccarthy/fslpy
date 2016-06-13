#!/usr/bin/env python
#
# imagewrapper.py - The ImageWrapper class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ImageWrapper` class, which can be used
to manage data access to ``nibabel`` NIFTI images.

There are some confusing terms used in this module, so it may be of use to
get their definitions straight:

  - *Coverage*:  The portion of an image that has been covered in the data
                 range calculation. The ``ImageWrapper`` keeps track of
                 the coverage for individual volumes within a 4D image (or
                 slices in a 3D image).

  - *Slice*:     Portion of the image data which is being accessed. A slice
                 comprises either a tuple of ``slice`` objects (or integers),
                 or a sequence of ``(low, high)`` tuples, specifying the
                 index range into each image dimension that is covered by
                 the slice.

  - *Expansion*: A sequence of ``(low, high)`` tuples, specifying an
                 index range into each image dimension, that is used to
                 *expand* the *coverage* of an image, based on a given set of
                 *slices*.
"""


import logging
import collections
import itertools as it

import numpy     as np
import nibabel   as nib

import fsl.utils.notifier as notifier
import fsl.utils.memoize  as memoize


log = logging.getLogger(__name__)


class ImageWrapper(notifier.Notifier):
    """The ``ImageWrapper`` class is a convenience class which manages data
    access to ``nibabel`` NIFTI images. The ``ImageWrapper`` class can be
    used to:

    
      - Control whether the image is loaded into memory, or kept on disk
    
      - Incrementally update the known image data range, as more image
        data is read in.


    The ``ImageWrapper`` implements the :class:`.Notifier` interface.
    Listeners can register to be notified whenever the known image data range
    is updated. The data range can be accessed via the :attr:`dataRange`
    property.


    The ``ImageWrapper`` class uses the following functions (also defined in 
    this module) to keep track of the portion of the image that has currently
    been included in the data range calculation:

    .. autosummary::
       :nosignatures:

       sliceObjToSliceTuple
       sliceTupleToSliceObj
       sliceCovered
       calcExpansion
       adjustCoverage
    """

    
    def __init__(self, image, name=None, loadData=False, dataRange=None):
        """Create an ``ImageWrapper``.

        :arg image:     A ``nibabel.Nifti1Image``.

        :arg name:      A name for this ``ImageWrapper``, solely used for 
                        debug log messages.

        :arg loadData:  If ``True``, the image data is loaded into memory.
                        Otherwise it is kept on disk (and data access is
                        performed through the ``nibabel.Nifti1Image.dataobj``
                        array proxy).

        :arg dataRange: A tuple containing the initial ``(min, max)``  data
                        range to use.


        .. note:: The ``dataRange`` parameter is intended for situations where
                  the image data range is known (e.g. it was calculated
                  earlier, and the image is being re-loaded. If a
                  ``dataRange`` is passed in, it will *not* be overwritten by
                  any range calculated from the data, unless the calculated
                  data range is wider than the provided ``dataRange``.
        """

        if dataRange is None:
            dataRange = None, None
        
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

        # The current known image data range. This
        # gets updated as more image data gets read.
        self.__range = dataRange

        # The coverage array is used to keep track of
        # the portions of the image which have been
        # considered in the data range calculation.
        # We use this coverage to avoid unnecessarily
        # re-calculating the data range on the same
        # part of the image.
        #
        # First of all, we're going to store a separate
        # 'coverage' for each 2D slice in the 3D image
        # (or 3D volume for 4D images). This effectively
        # means a seaprate coverage for each index in the
        # last 'real' image dimension (see above).
        # 
        # For each slice/volume, the the coverage is
        # stored as sequences of (low, high) indices, one
        # for each dimension in the slice/volume (e.g.
        # row/column for a slice, or row/column/depth
        # for a volume).
        #
        # All of these indices are stored in a numpy array:
        #   - first dimension:  low/high index
        #   - second dimension: image dimension
        #   - third dimension:  slice/volume index
        self.__coverage = np.zeros(
            (2, self.__numRealDims - 1, image.shape[self.__numRealDims - 1]),
            dtype=np.float32)

        self.__coverage[:] = np.nan

        # This flag is set to true if/when the
        # full image data range becomes known
        # (i.e. when all data has been loaded in).
        self.__covered = False

        if loadData:
            self.loadData()

        
    @property
    def dataRange(self):
        """Returns the currently known data range as a tuple of ``(min, max)``
        values.
        """
        # If no image data has been read, we default
        # to whatever is stored in the header (which
        # may or may not contain useful values).
        low, high = self.__range
        hdr       = self.__image.get_header()

        if low  is None: low  = float(hdr['cal_min'])
        if high is None: high = float(hdr['cal_max'])

        return low, high


    def loadData(self):
        """Forces all of the image data to be loaded into memory.

        .. note:: This method will be called by :meth:`__init__` if its
                  ``loadData`` parameter is ``True``.
        """

        # If the data is not already loaded, this will
        # cause nibabel to load it. By default, nibabel
        # will cache the numpy array that contains the
        # image data, so subsequent calls to this
        # method will not overwrite any changes that
        # have been made to the data.
        self.__image.get_data()


    def __getData(self, sliceobj, isTuple=False):
        """Retrieves the image data at the location specified by ``sliceobj``.

        :arg sliceobj: Something which can be used to slice an array, or
                       a sequence of (low, high) index pairs.

        :arg isTuple:  Set to ``True`` if ``sliceobj`` is a sequence of
                       (low, high) index pairs.
        """

        if isTuple:
            sliceobj = sliceTupleToSliceObj(sliceobj)

        # If the image has not been loaded
        # into memory, we can use the nibabel
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


    def __imageIsCovered(self):
        """Returns ``True`` if all portions of the image have been covered
        in the data range calculation, ``False`` otherwise.
        """
        
        shape  = self.__image.shape
        slices = zip([0] * len(shape), shape)
        return sliceCovered(slices, self.__coverage, shape)
    

    @memoize.Instanceify(memoize.memoize(args=[0]))
    def __updateDataRangeOnRead(self, slices, data):
        """Called by :meth:`__getitem__`. Calculates the minimum/maximum
        values of the given data (which has been extracted from the portion of
        the image specified by ``slices``), and updates the known data range
        of the image.

        :arg slices: A tuple of tuples, each tuple being a ``(low, high)``
                     index pair, one for each dimension in the image. 
        
        :arg data:   The image data at the given ``slices`` (as a ``numpy``
                     array).

        .. note:: Tuples must be used instead of lists or ``slice`` objects fo
                  the ``slices`` argument, because this method is memoized
                  (and ``slice``/``list`` objects are unhashable).
        """

        oldmin, oldmax = self.__range

        log.debug('Updating image {} data range (current range: '
                  '[{}, {}]; current coverage: {})'.format(
                      self.__name,
                      self.__range[0],
                      self.__range[1],
                      self.__coverage))

        volumes, expansions = calcExpansion(slices, self.__coverage)

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
            self.__coverage[..., vol] = adjustCoverage(
                self.__coverage[..., vol], exp)

        self.__covered = self.__imageIsCovered()

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

        if not self.__covered:

            slices = sliceObjToSliceTuple(sliceobj, self.__image.shape)

            if not sliceCovered(slices, self.__coverage, self.__image.shape):
                self.__updateDataRangeOnRead(slices, data)

        return data


def sliceObjToSliceTuple(sliceobj, shape):
    """Turns an array slice object into a tuple of (low, high) index
    pairs, one pair for each dimension in the given shape

    :arg sliceobj: Something which can be used to slice an array of shape
                   ``shape``.

    :arg shape:    Shape of the array being sliced.
    """

    indices = []

    # The sliceobj could be a single sliceobj
    # or integer, instead of a tuple
    if not isinstance(sliceobj, collections.Sequence):
        sliceobj = [sliceobj]

    # Turn e.g. array[6] into array[6, :, :]
    if len(sliceobj) != len(shape):
        missing  = len(shape) - len(sliceobj)
        sliceobj = list(sliceobj) + [slice(None) for i in range(missing)]

    for dim, s in enumerate(sliceobj):

        # each element in the slices tuple should 
        # be a slice object or an integer
        if isinstance(s, slice): i = [s.start, s.stop]
        else:                    i = [s,       s + 1]

        if i[0] is None: i[0] = 0
        if i[1] is None: i[1] = shape[dim]

        indices.append(tuple(i))

    return tuple(indices)


def sliceTupleToSliceObj(slices):
    """Turns a sequence of (low, high) index pairs into a tuple of array
    ``slice`` objects.

    :arg slices: A sequence of (low, high) index pairs.
    """

    sliceobj = []

    for lo, hi in slices:
        sliceobj.append(slice(lo, hi, 1))

    return tuple(sliceobj)


def adjustCoverage(oldCoverage, slices): 
    """Adjusts/expands the given ``oldCoverage`` so that it covers the
    given set of ``slices``.

    :arg oldCoverage: A ``numpy`` array of shape ``(2, n)`` containing
                      the (low, high) index pairs for ``n`` dimensions of
                      a single slice/volume in the image.
    
    :arg slices:      A sequence of (low, high) index pairs. If ``slices``
                      contains more dimensions than are specified in
                      ``oldCoverage``, the trailing dimensions are ignored.

    :return: A ``numpy`` array containing the adjusted/expanded coverage.
    """

    newCoverage = np.zeros(oldCoverage.shape, dtype=np.uint32)

    for dim in range(oldCoverage.shape[1]):

        low,      high      = slices[        dim]
        lowCover, highCover = oldCoverage[:, dim]

        if np.isnan(lowCover)  or low  < lowCover:  lowCover  = low
        if np.isnan(highCover) or high > highCover: highCover = high

        newCoverage[:, dim] = lowCover, highCover

    return newCoverage


def sliceCovered(slices, coverage, shape):
    """Returns ``True`` if the portion of the image data calculated by
    the given ``slices` has already been calculated, ``False`` otherwise.

    :arg slices:    A sequence of (low, high) index pairs, assumed to cover
                    all image dimensions.
    :arg coverage:  A ``numpy`` array of shape ``(2, nd, nv)`` (where ``nd``
                    is the number of dimensions being covered, and ``nv`` is
                    the number of volumes (or vectors/slices) in the image,
                    which contains the (low, high) index pairs describing
                    the current image coverage.
    :arg shape:     The full image shape.
    """

    numDims         = coverage.shape[1]
    lowVol, highVol = slices[numDims]
    shape           = shape[:numDims]

    for vol in range(lowVol, highVol):

        for dim, size in enumerate(shape):

            lowCover, highCover = coverage[:, dim, vol]
            lowSlice, highSlice = slices[     dim] 

            if np.isnan(lowCover) or np.isnan(highCover):
                return False

            if lowSlice  is None: lowSlice  = 0
            if highSlice is None: highSlice = size

            if lowSlice  < lowCover:  return False
            if highSlice > highCover: return False

    return True


def calcExpansion(slices, coverage):
    """Calculates a series of *expansion* slices, which can be used to expand
    the given ``coverage`` so that it includes the given ``slices``.

    :arg slices:   Slices that the coverage needs to be expanded to cover.
    :arg coverage: Current image coverage.

    :returns: A list of volume indices, and a corresponding list of
              expansions.
    """

    numDims         = coverage.shape[1]
    padDims         = len(slices) - numDims - 1
    lowVol, highVol = slices[numDims] 

    expansions = []
    volumes    = []

    # Finish off an expansion by
    # adding indices for the vector/
    # slice/volume dimension, and for
    # 'padding' dimensions of size 1.
    def finishExpansion(exp, vol):
        exp.append((vol, vol + 1))
        for i in range(padDims):
            exp.append((0, 1))
        return exp
    
    for vol in range(lowVol, highVol):

        # No coverage of this volume - 
        # we need the whole slice.
        if np.any(np.isnan(coverage[:, :, vol])):
            exp = [(s[0], s[1]) for s in slices[:numDims]]
            exp = finishExpansion(exp, vol)
            volumes   .append(vol)
            expansions.append(exp)
            continue

        # First we'll figure out the index
        # range for each dimension that
        # needs to be added to the coverage.
        # We build a list of required ranges,
        # where each entry is a tuple
        # containing:
        #   (dimension, lowIndex, highIndex)
        reqRanges = []

        for dim in range(numDims):

            lowCover, highCover = coverage[:, dim, vol]
            lowSlice, highSlice = slices[     dim]

            # The slice covers a region
            # below the current coverage
            if lowCover - lowSlice > 0:
                reqRanges.append((dim, int(lowSlice), int(lowCover)))
                
            # The slice covers a region
            # above the current coverage
            if highCover - highSlice < 0:
                reqRanges.append((dim, int(highCover), int(highSlice)))

        # Now we generate an expansion for
        # each of those ranges.
        volExpansions = []
        for dimx, xlo, xhi in reqRanges:

            expansion = [[np.nan, np.nan] for d in range(numDims)]

            # The expansion for each
            # dimension will span the range
            # for that dimension...
            expansion[dimx][0] = xlo
            expansion[dimx][1] = xhi
                
            # And will span the union of
            # the coverage, and calculated
            # range for every other dimension.
            for dimy, ylo, yhi in reqRanges:
                if dimy == dimx:
                    continue

                yLowCover, yHighCover = coverage[:, dimy, vol]
                expLow,    expHigh    = expansion[  dimy]

                if np.isnan(expLow):  expLow  = yLowCover
                if np.isnan(expHigh): expHigh = yHighCover

                expLow  = min((ylo, yLowCover,  expLow))
                expHigh = max((yhi, yHighCover, expHigh))

                expansion[dimy][0] = expLow
                expansion[dimy][1] = expHigh

            # Finish off this expansion
            expansion = finishExpansion(expansion, vol)

            volumes.      append(vol)
            volExpansions.append(expansion)

        # We do a final run through all pairs
        # of expansions, and adjust their
        # range if they overlap with each other.
        for exp1, exp2 in it.product(volExpansions, volExpansions):

            # Check each dimension
            for dimx in range(numDims):

                xlo1, xhi1 = exp1[dimx]
                xlo2, xhi2 = exp2[dimx]

                # These expansions do not
                # overlap with each other
                # on this dimension (or at
                # all). No need to check
                # the other dimensions.
                if xhi1 <= xlo2: break
                if xlo1 >= xhi2: break

                # These expansions overlap on
                # this dimension - check to see
                # if exp1 is wholly contained
                # within exp2 in all other
                # dimensions.
                adjustable = True

                for dimy in range(numDims):

                    if dimy == dimx:
                        continue

                    ylo1, yhi1 = exp1[dimy]
                    ylo2, yhi2 = exp2[dimy]

                    # Exp1 is not contained within
                    # exp2 on another dimension -
                    # we can't reduce the overlap.
                    if ylo1 < ylo2 or yhi1 > yhi2:
                        adjustable = False
                        break

                # The x dimension range of exp1
                # can be reduced, as it is covered
                # by exp2.
                if adjustable:
                    if   xlo1 <  xlo2 and xhi1 <= xhi2 and xhi1 > xlo2:
                        xhi1 = xlo2

                    elif xlo1 >= xlo2 and xhi1 >  xhi2 and xlo1 < xhi2:
                        xlo1 = xhi2

                    exp1[dimx] = xlo1, xhi1

        expansions.extend(volExpansions)

    return volumes, expansions
