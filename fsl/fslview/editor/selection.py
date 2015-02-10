#!/usr/bin/env python
#
# selection.py - Provides the Selection class, which represents a
# selection on a 3D image.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Selection` class.
"""

import logging
import collections

import numpy                      as np
import scipy.ndimage.measurements as ndimeas

import props


log = logging.getLogger(__name__)


class Selection(props.HasProperties):


    selection = props.Object()

    
    def __init__(self, image):
        self._image                = image
        self._lastChangeOffset     = None
        self._lastChangeOldBlock   = None
        self._lastChangeNewBlock   = None
        self.selection             = np.zeros(image.shape[:3], dtype=np.uint8)

    
    def getSelectionSize(self):
        return self.selection.sum()


    def getBoundedSelection(self):
        
        xs, ys, zs = np.where(self.selection > 0)

        xlo = xs.min()
        ylo = ys.min()
        zlo = zs.min()
        xhi = xs.max()
        yhi = ys.max()
        zhi = zs.max()

        selection = self.selection[xlo:xhi, ylo:yhi, zlo:zhi]

        return selection, (xlo, ylo, zlo)


    def _updateSelectionBlock(self, block, offset):

        block = np.array(block, dtype=np.uint8)

        if block.size == 0:
            return

        if offset is None:
            offset = (0, 0, 0)

        xlo, ylo, zlo = offset

        xhi = xlo + block.shape[0]
        yhi = ylo + block.shape[1]
        zhi = zlo + block.shape[2]

        self._lastChangeOffset   = offset
        self._lastChangeOldBlock = np.array(self.selection[xlo:xhi,
                                                           ylo:yhi,
                                                           zlo:zhi])
        self._lastChangeNewBlock = np.array(block)

        log.debug('Updating selection ({}) block [{}:{}, {}:{}, {}:{}]'.format(
            id(self), xlo, xhi, ylo, yhi, zlo, zhi))

        self.selection[xlo:xhi, ylo:yhi, zlo:zhi] = block
        self.notify('selection') 

        
    def _getSelectionBlock(self, size, offset):
        
        xlo, ylo, zlo = offset
        xhi, yhi, zhi = size

        xhi = xlo + size[0]
        yhi = ylo + size[1]
        zhi = zlo + size[2]

        return self.selection[xlo:xhi, ylo:yhi, zlo:zhi]


    def replaceSelection(self, block, offset):
        self.clearSelection()
        self._updateSelectionBlock(block, offset)

        
    def setSelection(self, block, offset):
        self._updateSelectionBlock(block, offset) 

        
    def addToSelection(self, block, offset):
        existing = self._getSelectionBlock(block.shape, offset)
        block    = np.logical_or(block, existing)
        self._updateSelectionBlock(block, offset)


    def removeFromSelection(self, block, offset):
        existing             = self._getSelectionBlock(block.shape, offset)
        existing[block != 0] = False
        self._updateSelectionBlock(existing, offset)

        
    def clearSelection(self):

        log.debug('Clearing selection ({})'.format(id(self)))
        
        self._lastChangeOffset     = [0, 0, 0]
        self._lastChangeOldBlock   = np.array(self.selection)
        self.selection[:]          = False
        self._lastChangeNewBlock   = np.array(self.selection)

        self.notify('selection')


    def getLastChange(self):
        return (self._lastChangeOldBlock,
                self._lastChangeNewBlock,
                self._lastChangeOffset)


    def getIndices(self, restrict=None):

        if restrict is None: selection = self.selection
        else:                selection = self.selection[restrict]

        xs, ys, zs = np.where(selection)

        result = np.vstack((xs, ys, zs)).T

        if restrict is not None:

            for ax in range(3):
                off = restrict[ax].start
                if off is None: off = 0
                result[:, ax] += off

        return result


    @classmethod
    def generateBlock(cls, voxel, blockSize, shape, axes=(0, 1, 2)):

        if blockSize == 1:
            return np.array([True], dtype=np.uint8).reshape(1, 1, 1), voxel

        blockLo = [v - int(np.floor((blockSize - 1) / 2.0)) for v in voxel]
        blockHi = [v + int(np.ceil(( blockSize - 1) / 2.0)) for v in voxel]

        for i in range(3):
            if i not in axes:
                blockLo[i] = voxel[i]
                blockHi[i] = voxel[i] + 1
            else:
                blockLo[i] = max(blockLo[i],     0)
                blockHi[i] = min(blockHi[i] + 1, shape[i])

            if blockHi[i] <= blockLo[i]:
                return np.ones((0, 0, 0), dtype=np.uint8), voxel

        block = np.ones((blockHi[0] - blockLo[0],
                         blockHi[1] - blockLo[1],
                         blockHi[2] - blockLo[2]), dtype=np.uint8)

        offset = blockLo

        return block, offset


    def selectBlock(self, voxel, blockSize, axes=(0, 1, 2)):
        self.addToSelection(*self.generateBlock(voxel,
                                                blockSize,
                                                self.selection.shape,
                                                axes))

        
    def deselectBlock(self, voxel, blockSize, axes=(0, 1, 2)):
        self.removeFromSelection(*self.generateBlock(voxel,
                                                     blockSize,
                                                     self.selection.shape,
                                                     axes)) 

    
    def selectByValue(self,
                      seedLoc,
                      precision=None,
                      searchRadius=None,
                      local=False):

        seedLoc = np.array(seedLoc)
        value   = self._image[seedLoc[0], seedLoc[1], seedLoc[2]]

        # Search radius may be either None, a scalar value,
        # or a sequence of three values (one for each axis).
        # If it is one of the first two options (None/scalar),
        # turn it into the third.
        if searchRadius is None:
            searchRadius = np.array([0, 0, 0])
        elif not isinstance(searchRadius, collections.Sequence):
            searchRadius = np.array([searchRadius] * 3)

        searchRadius = np.ceil(searchRadius)

        # No search radius - search
        # through the entire image
        if np.any(searchRadius == 0):
            searchSpace  = self._image
            searchOffset = (0, 0, 0)
            searchMask   = None

        # Search radius specified - limit
        # the search space, and specify
        # an ellipsoid mask with the
        # specified per-axis radii
        else:            
            ranges = [None, None, None]
            slices = [None, None, None]

            # Calculate xyz indices 
            # of the search space
            shape = self._image.shape
            for ax in range(3):

                idx = seedLoc[     ax]
                rad = searchRadius[ax]

                lo = idx - rad
                hi = idx + rad + 1

                if lo < 0:             lo = 0
                if hi > shape[ax] - 1: hi = shape[ax] - 1

                ranges[ax] = np.arange(lo, hi)
                slices[ax] = slice(    lo, hi)

            xs, ys, zs = np.meshgrid(*ranges, indexing='ij')

            # Centre those indices and the
            # seed location at (0, 0, 0)
            xs         -= seedLoc[0]
            ys         -= seedLoc[1]
            zs         -= seedLoc[2]
            seedLoc[0] -= ranges[0][0]
            seedLoc[1] -= ranges[1][0]
            seedLoc[2] -= ranges[2][0]

            # Distances from each point in the search
            # space to the centre of the search space
            dists = ((xs / searchRadius[0]) ** 2 +
                     (ys / searchRadius[1]) ** 2 +
                     (zs / searchRadius[2]) ** 2)

            # Extract the search space, and
            # create the ellipsoid mask
            searchSpace  = self._image[slices]
            searchOffset = (ranges[0][0], ranges[1][0], ranges[2][0])
            searchMask   = dists <= 1
            
        if precision is None: hits = searchSpace == value
        else:                 hits = np.abs(searchSpace - value) < precision

        if searchMask is not None:
            hits[~searchMask] = False

        # If local is true, limit the selection to
        # adjacent points with the same/similar value
        # (using scipy.ndimage.measurements.label)
        #
        # If local is not True, any same or similar 
        # values are part of the selection
        # 
        if local:
            hits, _   = ndimeas.label(hits)
            seedLabel = hits[seedLoc[0], seedLoc[1], seedLoc[2]]
            hits      = hits == seedLabel

        self.replaceSelection(hits, searchOffset)
