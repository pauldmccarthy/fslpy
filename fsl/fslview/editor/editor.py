#!/usr/bin/env python
#
# editor.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import collections

import numpy as np

import props
import selection

import fsl.data.image as fslimage


class ValueChange(object):
    def __init__(self, image, selection, oldVals, newVals):
        self.image     = image
        self.selection = selection
        self.oldVals   = oldVals
        self.newVals   = newVals


class SelectionChange(object):
    def __init__(self, image, oldSelection, newSelection):
        self.image        = image
        self.oldSelection = oldSelection
        self.newSelection = newSelection


class Editor(props.HasProperties):

    canUndo = props.Boolean(default=False)
    canRedo = props.Boolean(default=False)

    def __init__(self, imageList, displayCtx):

        self._name         = '{}_{}'.format(self.__class__.__name__, id(self))
        self._imageList    = imageList
        self._displayCtx   = displayCtx
        self._selection    = None
        self._currentImage = None
 
        # Two stacks of Change objects, providing
        # records of what has been done and undone
        self._doneStack   = []
        self._undoneStack = []

        self._displayCtx.addListener('selectedImage',
                                     self._name,
                                     self._selectedImageChanged)
        self._imageList .addListener('images',
                                     self._name,
                                     self._selectedImageChanged) 

        self._selectedImageChanged()

        
    def __del__(self):
        self._displayCtx.removeListener('selectedImage', self._name)
        self._imageList .removeListener('images',        self._name)


    def _selectedImageChanged(self, *a):
        image = self._displayCtx.getSelectedImage()

        if image is None:
            self._currentImage = None
            self._selection    = None
            return

        if self._currentImage == image:
            return

        self._currentImage = image
        self._selection    = selection.Selection(image.data)

        self._selection.addListener('selection',
                                    self._name,
                                    self._selectionChanged)


    def _selectionChanged(self, *a):

        image  = self._displayCtx.getSelectedImage()
        oldSel = self._selection.getPreviousIndices()
        newSel = self._selection.getIndices()
        change = SelectionChange(image, oldSel, newSel)
        self._applyChange(change, True)

        
    def getSelection(self):
        return self._selection


    def fillSelection(self, newVals):

        image = self._displayCtx.getSelectedImage()
        nvox  = self._selection.getSelectionSize()

        if not isinstance(newVals, collections.Sequence):
            nv = np.zeros(nvox, dtype=np.float32)
            nv.fill(newVals)
            newVals = nv
        else:
            newVals = np.array(newVals)

        xyzs    = self._selection.getIndices()
        xyzt    = xyzs.T
        oldVals = image.data[xyzt[0], xyzt[1], xyzt[2]]
        
        change = ValueChange(image, xyzs, oldVals, newVals)
        self._applyChange(change)


    def undo(self):
        if len(self._doneStack) == 0:
            return
        
        self._revertChange()
        

    def redo(self):
        if len(self._undoneStack) == 0:
            return
        
        self._applyChange()


    def _applyChange(self, change=None, alreadyApplied=False):

        if change is None: change = self._undoneStack.pop()
        else:              self._undoneStack = []

        if len(self._undoneStack) == 0:
            self.canRedo = False 
            
        image = change.image
        if self._displayCtx.getSelectedImage() != image:
            self._displayCtx.selectImage(image)

        self._doneStack.append(change)
        self.canUndo = True

        if alreadyApplied:
            return
        
        if isinstance(change, ValueChange):
            change.image.applyChange(change.selection, change.newVals)
            
        elif isinstance(change, SelectionChange):
            self._selection.disableListener('selection', self._name)
            self._selection.setSelection(change.newSelection)
            self._selection.enableListener('selection', self._name)

        
    def _revertChange(self, change=None, alreadyApplied=False):

        if change is None: change = self._doneStack.pop()
        else:              self._doneStack = []

        if len(self._doneStack) == 0:
            self.canUndo = False 
         
        image = change.image
        if self._displayCtx.getSelectedImage() != image:
            self._displayCtx.selectImage(image)

        self._undoneStack.append(change)
        self.canRedo = True

        if alreadyApplied:
            return

        if isinstance(change, ValueChange):
            change.image.applyChange(change.selection, change.oldVals)
            
        elif isinstance(change, SelectionChange):
            self._selection.disableListener('selection', self._name)
            self._selection.setSelection(change.oldSelection)
            self._selection.enableListener('selection', self._name)


    def createMaskFromSelection(self):

        imageIdx = self._displayCtx.selectedImage
        image    = self._imageList[imageIdx]
        xyzs     = self._selection.getIndices()

        xs = xyzs[:, 0]
        ys = xyzs[:, 1]
        zs = xyzs[:, 2]
        
        roi             = np.zeros(image.shape, image.data.dtype)
        roi[xs, ys, zs] = 1

        xform = image.voxToWorldMat
        name  = '{}_mask'.format(image.name)

        roiImage = fslimage.Image(roi, xform, name)
        self._imageList.insert(imageIdx + 1, roiImage) 


    def createROIFromSelection(self):

        imageIdx = self._displayCtx.selectedImage
        image    = self._imageList[imageIdx]
        xyzs     = self._selection.getIndices()

        xs = xyzs[:, 0]
        ys = xyzs[:, 1]
        zs = xyzs[:, 2]
        
        roi             = np.zeros(image.shape, image.data.dtype)
        roi[xs, ys, zs] = image.data[xs, ys, zs]

        xform = image.voxToWorldMat
        name  = '{}_roi'.format(image.name)

        roiImage = fslimage.Image(roi, xform, name)
        self._imageList.insert(imageIdx + 1, roiImage)
