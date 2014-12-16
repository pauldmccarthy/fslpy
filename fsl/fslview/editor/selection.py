#!/usr/bin/env python
#
# selection.py - 
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)


import numpy as np


class Selection(object):
    
    def __init__(self, image):
        
        self._image     = image
        self._selection = np.zeros(image.shape, dtype=np.bool)


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
        return self._selection.sum()
    
        
    def addToSelection(self, xyzs):

        xyzs = self._filterVoxels(xyzs)
        xs   = xyzs[:, 0]
        ys   = xyzs[:, 1]
        zs   = xyzs[:, 2]

        self._selection[xs, ys, zs] = True


    def removeFromSelection(self, xyzs):
        
        xyzs = self._filterVoxels(xyzs)
        xs   = xyzs[:, 0]
        ys   = xyzs[:, 1]
        zs   = xyzs[:, 2]

        self._selection[xs, ys, zs] = False
    
    
    def clearSelection(self):
        self._selection[:] = False


    def getSelection(self, restrict=None):

        if restrict is None: selection = self._selection
        else:                selection = self._selection[restrict]

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

    
    def selectByValue(self, value, precision=None):

        if precision is None:
            block = np.where(self._image == value)
        else:
            block = np.where(np.abs(self._image - value) < precision)

        if len(block[0]) == 0:
            return

        self.addToSelection(np.vstack(block).T)
