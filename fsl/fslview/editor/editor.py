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
 
        # A list of state objects, providing
        # records of what has been done. The
        # doneIndex points to the current
        # state. Everything before the doneIndex
        # represents previous states, and
        # everything after the doneIndex
        # represents states which have been
        # undone.
        self._doneList  = []
        self._doneIndex = -1
        self._inGroup   = False

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
        self._changeMade(change)


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
        self._changeMade( change)

        
    def startChangeGroup(self):
        self._inGroup    = True
        self._doneIndex += 1
        self._doneList.append([])

        log.debug('Starting change group - merging subsequent '
                  'changes at index {} of {}'.format(self._doneIndex,
                                                     len(self._doneList)))

        
    def endChangeGroup(self):
        self._inGroup = False
        log.debug('Ending change group at {} of {}'.format(
            self._doneIndex, len(self._doneList))) 

        
    def _changeMade(self, change):

        if self._inGroup:
            self._doneList[self._doneIndex].append(change)
        else:
            del self._doneList[self._doneIndex + 1:]
            self._doneList.append(change)
            self._doneIndex += 1
            
        self.canUndo = True
        self.canRedo = False

        log.debug('New change ({} of {})'.format(self._doneIndex,
                                                 len(self._doneList)))


    def undo(self):
        if self._doneIndex == -1:
            return

        log.debug('Undo change {} of {}'.format(self._doneIndex,
                                                len(self._doneList)))        

        change = self._doneList[self._doneIndex]

        if not isinstance(change, collections.Sequence):
            change = [change]

        for c in reversed(change):
            self._revertChange(c)

        self._doneIndex -= 1

        self._inGroup = False
        self.canRedo  = True
        if self._doneIndex == -1:
            self.canUndo = False
        

    def redo(self):
        if self._doneIndex == len(self._doneList) - 1:
            return

        log.debug('Redo change {} of {}'.format(self._doneIndex + 1,
                                                len(self._doneList))) 

        change = self._doneList[self._doneIndex + 1]
        
        if not isinstance(change, collections.Sequence):
            change = [change] 

        for c in change:
            self._applyChange(c)

        self._doneIndex += 1

        self._inGroup = False
        self.canUndo  = True
        if self._doneIndex == len(self._doneList) - 1:
            self.canRedo = False


    def _applyChange(self, change):

        image   = change.image
        display = self._displayCtx.getDisplayProperties(image)

        if image.is4DImage(): volume = display.volume
        else:                 volume = None
        
        if self._displayCtx.getSelectedImage() != image:
            self._displayCtx.selectImage(image)

        if isinstance(change, ValueChange):
            change.image.applyChange(change.offset, change.newVals, volume)
            
        elif isinstance(change, SelectionChange):
            self._selection.disableListener('selection', self._name)
            self._selection.setSelection(change.newSelection, change.offset)
            self._selection.enableListener('selection', self._name)

        
    def _revertChange(self, change):

        image   = change.image
        display = self._displayCtx.getDisplayProperties(image)
        
        if self._displayCtx.getSelectedImage() != image:
            self._displayCtx.selectImage(image)

        if image.is4DImage(): volume = display.volume
        else:                 volume = None 

        if isinstance(change, ValueChange):
            change.image.applyChange(change.offset, change.oldVals, volume)
            
        elif isinstance(change, SelectionChange):
            self._selection.disableListener('selection', self._name)
            self._selection.setSelection(change.oldSelection, change.offset)
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
