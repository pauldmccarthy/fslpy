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

import selection


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
        

class Editor(object):

    def __init__(self, imageList, displayCtx):

        self._name       = '{}_{}'.format(self.__class__.__name__, id(self))
        self._imageList  = imageList
        self._displayCtx = displayCtx
        self._selection  = None
 
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

        if len(self._imageList) == 0:
            self._selection = None
            return
        
        image = self._displayCtx.getSelectedImage()
        
        self._selection = selection.Selection(image.data)

        self._selection.addListener('selection',
                                    self._name,
                                    self._selectionChanged)


    def _selectionChanged(self, *a):

        image  = self._displayCtx.getSelectedImage()
        oldSel = self._selection.getPreviousIndices()
        newSel = self._selection.getIndices()

        change = SelectionChange(image, oldSel, newSel)
        self._doneStack.append(change)

        
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

        xyzs    = self._selection.getSelection()
        xyzt    = xyzs.T
        oldVals = image.data[xyzt[0], xyzt[1], xyzt[2]]
        
        change = ValueChange(image, xyzs, oldVals, newVals)

        self._applyChange(change)
        self._doneStack.append(change)


    def canUndo(self):
        return len(self._doneStack) > 0

    
    def canRedo(self):
        return len(self._undoneStack) > 0 


    def undo(self):
        if not self.canUndo():
            return
        change = self._doneStack.pop()
        self._revertChange(change)
        self._undoneStack.append(change)
        

    def redo(self):
        if not self.canRedo():
            return        
        change = self._undoneStack.pop()
        self._applyChange(change)
        self._doneStack.append(change)


    def _applyChange(self, change):
        image = change.image
        if self._displayCtx.getSelectedImage() != image:
            self._displayCtx.selectImage(image)
        
        if isinstance(change, ValueChange):
            change.image.applyChange(change.selection, change.newVals)
        elif isinstance(change, SelectionChange):
            
            self._selection.disableListener('selection', self._name)
            self._selection.setSelection(change.newSelection)
            self._selection.enableListener('selection', self._name)


        
    def _revertChange(self, change):
        image = change.image
        if self._displayCtx.getSelectedImage() != image:
            self._displayCtx.selectImage(image)
        
        if isinstance(change, ValueChange):
            change.image.applyChange(change.selection, change.oldVals)
            
        elif isinstance(change, SelectionChange):
            self._selection.disableListener('selection', self._name)
            self._selection.setSelection(change.oldSelection)
            self._selection.enableListener('selection', self._name) 
