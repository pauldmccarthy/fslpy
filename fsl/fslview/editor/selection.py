#!/usr/bin/env python
#
# selection.py - 
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)


import numpy as np

import scipy.ndimage.measurements as ndimeas

import props


class Selection(props.HasProperties):


    selection = props.Object()
    
    def __init__(self, image):
        self._image            = image
        self._lastSelection    = None
        self._currentSelection = None
        self.selection         = np.zeros(image.shape, dtype=np.bool)


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


    def generateBlock(self, voxel, blockSize, axes=(0, 1, 2)):
        
        if blockSize == 1:
            return voxel

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

    
    def selectByValue(self, seedLoc, precision=None, local=False):

        value = self._image[seedLoc[0], seedLoc[1], seedLoc[2]]

        if precision is None: mask = self._image == value
        else:                 mask = np.abs(self._image - value) < precision 

        if local:
            mask, _ = ndimeas.label(mask)
            seedLabel = mask[seedLoc[0], seedLoc[1], seedLoc[2]]
            block     = np.where(mask == seedLabel) 
        else:
            block = np.where(mask)

        if len(block[0]) == 0:
            return

        self.addToSelection(np.vstack(block).T)
