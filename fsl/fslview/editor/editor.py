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
    def __init__(self, image, offset, oldVals, newVals):
        self.image   = image
        self.offset  = offset
        self.oldVals = oldVals
        self.newVals = newVals


class SelectionChange(object):
    def __init__(self, image, offset, oldSelection, newSelection):
        self.image        = image
        self.offset       = offset
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

        image            = self._displayCtx.getSelectedImage()
        old, new, offset = self._selection.getLastChange()
        
        change = SelectionChange(image, offset, old, new)
        self._applyChange(change, True)

        
    def getSelection(self):
        return self._selection


    def fillSelection(self, newVals):

        image = self._displayCtx.getSelectedImage()

        selectBlock, offset = self._selection.getBoundedSelection()

        if not isinstance(newVals, collections.Sequence):
            nv = np.zeros(selectBlock.shape, dtype=np.float32)
            nv.fill(newVals)
            newVals = nv
        else:
            newVals = np.array(newVals)

        xlo, ylo, zlo = offset
        xhi = xlo + selectBlock.shape[0]
        yhi = ylo + selectBlock.shape[1]
        zhi = zlo + selectBlock.shape[2]

        oldVals = image.data[xlo:xhi, ylo:yhi, zlo:zhi]

        selectBlock = selectBlock == 0
        newVals[selectBlock] = oldVals[selectBlock]
        
        change = ValueChange(image, offset, oldVals, newVals)
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
            
        image   = change.image
        display = self._displayCtx.getDisplayProperties(image)

        if image.is4DImage(): volume = display.volume
        else:                 volume = None
        
        if self._displayCtx.getSelectedImage() != image:
            self._displayCtx.selectImage(image)

        self._doneStack.append(change)
        self.canUndo = True

        if alreadyApplied:
            return
        
        if isinstance(change, ValueChange):
            change.image.applyChange(change.offset, change.newVals, volume)
            
        elif isinstance(change, SelectionChange):
            self._selection.disableListener('selection', self._name)
            self._selection.setSelection(change.offset, change.newSelection)
            self._selection.enableListener('selection', self._name)

        
    def _revertChange(self, change=None, alreadyApplied=False):

        if change is None: change = self._doneStack.pop()
        else:              self._doneStack = []

        if len(self._doneStack) == 0:
            self.canUndo = False 
         
        image   = change.image
        display = self._displayCtx.getDisplayProperties(image)
        
        if self._displayCtx.getSelectedImage() != image:
            self._displayCtx.selectImage(image)

        if image.is4DImage(): volume = display.volume
        else:                 volume = None 

        self._undoneStack.append(change)
        self.canRedo = True

        if alreadyApplied:
            return

        if isinstance(change, ValueChange):
            change.image.applyChange(change.offset, change.oldVals, volume)
            
        elif isinstance(change, SelectionChange):
            self._selection.disableListener('selection', self._name)
            self._selection.setSelection(change.offset, change.oldSelection)
            self._selection.enableListener('selection', self._name)


    def createMaskFromSelection(self):

        imageIdx = self._displayCtx.selectedImage
        image    = self._imageList[imageIdx]
        mask     = np.array(self._selection.selection, dtype=np.uint8)

        xform = image.voxToWorldMat
        name  = '{}_mask'.format(image.name)

        roiImage = fslimage.Image(mask, xform, name)
        self._imageList.insert(imageIdx + 1, roiImage) 


    def createROIFromSelection(self):

        imageIdx = self._displayCtx.selectedImage
        image    = self._imageList[imageIdx]
        
        roi = np.zeros(image.shape, dtype=image.data.dtype)
        
        roi[self._selection.selection] = image.data[self._selection.selection]

        xform = image.voxToWorldMat
        name  = '{}_roi'.format(image.name)

        roiImage = fslimage.Image(roi, xform, name)
        self._imageList.insert(imageIdx + 1, roiImage)
