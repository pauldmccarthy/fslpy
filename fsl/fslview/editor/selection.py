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
        
        self.image     = image
        self.selection = np.zeros(image.shape, dtype=np.bool)


    def _filterVoxels(self, xyzs):

        if len(xyzs.shape) == 1:
            xyzs = xyzs.reshape(1, 3) 
        
        xs   = xyzs[:, 0]
        ys   = xyzs[:, 1]
        zs   = xyzs[:, 2]
        xyzs = xyzs[(xs >= 0)                   & 
                    (xs <  self.image.shape[0]) & 
                    (ys >= 0)                   & 
                    (ys <  self.image.shape[1]) & 
                    (zs >= 0)                   & 
                    (zs <  self.image.shape[2]), :]

        return xyzs

    
    def getSelectionSize(self):
        return self.selection.sum()
    
        
    def addToSelection(self, xyzs):

        xyzs = self._filterVoxels(xyzs)
        xs   = xyzs[:, 0]
        ys   = xyzs[:, 1]
        zs   = xyzs[:, 2]

        self.selection[xs, ys, zs] = True


    def removeFromSelection(self, xyzs):
        
        xyzs = self._filterVoxels(xyzs)
        xs   = xyzs[:, 0]
        ys   = xyzs[:, 1]
        zs   = xyzs[:, 2]

        self.selection[xs, ys, zs] = False
    
    
    def clearSelection(self):
        self.selection[:]   = False


    def getSelection(self, restrict=None):

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


    def selectBlock(self, voxel, blockSize, axes=(0, 1, 2)):

        if blockSize == 1:
            self.addToSelection(voxel)
            return

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
        
        self.addToSelection(block)         

    
    def selectByValue(self, value, precision=None):

        if precision is None:
            block = np.where(self.image == value)
        else:
            block = np.where(np.abs(self.image - value) < precision)

        if len(block[0]) == 0:
            return

        self.addToSelection(np.vstack(block).T)
