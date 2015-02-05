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
log = logging.getLogger(__name__)

import collections

import numpy as np

import scipy.ndimage.measurements as ndimeas

import props


class Selection(props.HasProperties):


    selection = props.Object()
    
    def __init__(self, image):
        self._image            = image
        self._lastSelection    = None
        self._currentSelection = None
        self.selection         = np.zeros(image.shape[:3], dtype=np.bool)


    def _filterVoxels(self, xyzs):

        if len(xyzs.shape) == 1:
            xyzs = xyzs.reshape(1, 3) 
        
        xs   = xyzs[:, 0]
        ys   = xyzs[:, 1]
        zs   = xyzs[:, 2]
        xyzs = xyzs[(xs >= 0)                    & 
                    (xs <  self._image.shape[0]) & 
                    (ys >= 0)                    & 
                    (ys <  self._image.shape[1]) & 
                    (zs >= 0)                    & 
                    (zs <  self._image.shape[2]), :]

        return xyzs

    
    def getSelectionSize(self):
        return self.selection.sum()


    def _updateSelection(self, selected, xyzs=None):

        lastSelection = self._realGetIndices()

        if xyzs is not None:
            xyzs = self._filterVoxels(xyzs)
            xs   = xyzs[:, 0]
            ys   = xyzs[:, 1]
            zs   = xyzs[:, 2]
            self.selection[xs, ys, zs] = selected
        else:
            self.selection[:] = selected

        self._lastSelection    = lastSelection
        self._currentSelection = self._realGetIndices()
        self.notify('selection')


    def setSelection(self, xyzs):
        self.selection[:] = False
        self._updateSelection(True, xyzs)

        
    def addToSelection(self, xyzs):
        self._updateSelection(True, xyzs)


    def removeFromSelection(self, xyzs):
        self._updateSelection(False, xyzs)
    
    
    def clearSelection(self):
        self._updateSelection(False)


    def getPreviousIndices(self):
        return self._lastSelection


    def getIndices(self, restrict=None):
        if restrict is None: return self._currentSelection
        else:                return self._realGetIndices(restrict)


    def _realGetIndices(self, restrict=None):

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
    def generateBlock(cls, voxel, blockSize, axes=(0, 1, 2)):
        
        if blockSize == 1:
            return np.array(voxel).reshape(1, 3)

        blockLo = int(np.floor(blockSize / 2.0))
        blockHi = int(np.ceil( blockSize / 2.0))
        
        ranges = list(voxel)
        for ax in axes:
            ranges[ax] = np.arange(voxel[ax] - blockLo,
                                   voxel[ax] + blockHi)

        blockx, blocky, blockz = np.meshgrid(*ranges)

        blockx = blockx.flat
        blocky = blocky.flat
        blockz = blockz.flat
        block  = np.vstack((blockx, blocky, blockz)).T

        return block


    def selectBlock(self, voxel, blockSize, axes=(0, 1, 2)):
        self.addToSelection(self.generateBlock(voxel, blockSize, axes))

        
    def deselectBlock(self, voxel, blockSize, axes=(0, 1, 2)):
        self.removeFromSelection(self.generateBlock(voxel, blockSize, axes)) 

    
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

        searchRadius = np.floor(searchRadius)

        # No search radius - search
        # through the entire image
        if np.any(searchRadius == 0):
            searchSpace = self._image
            searchMask  = None

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

            # Centre those indices and tyhe
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
            searchSpace = self._image[slices]
            searchMask  = dists <= 1
            
        if precision is None: hits = searchSpace == value
        else:                 hits = np.abs(searchSpace - value) < precision

        if searchMask is not None:
            hits[~searchMask] = False

        # If local is true, limit the selection to
        # adjacent points with the same/similar value
        # (using scipy.ndimage.measurements.label)
        if local:
            hits, _   = ndimeas.label(hits)
            seedLabel = hits[seedLoc[0], seedLoc[1], seedLoc[2]]
            block     = np.where(hits == seedLabel)

        # Otherwise, any same or similar 
        # values are part of the selection
        else:
            block = np.where(hits)

        if len(block[0]) == 0:
            return

        block = np.vstack(block).T

        # If the search space was restricted,
        # move the coordinates back to be
        # relative to the entire image
        if np.any(searchRadius > 0):
            block[:, 0] += ranges[0][0]
            block[:, 1] += ranges[1][0]
            block[:, 2] += ranges[2][0]

        self.addToSelection(block)
