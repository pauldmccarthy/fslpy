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


class Change(object):
    
    def __init__(self, image, selection, oldVals, newVals):
        self.image     = image
        self.selection = selection
        self.oldVals   = oldVals
        self.newVals   = newVals


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

        
    def getSelection(self):
        return self._selection


    def makeChange(self, newVals):

        image = self._displayCtx.getSelectedImage().data
        nvox  = self.getSelectionSize()

        if not isinstance(newVals, collections.Sequence):
            newVals = [newVals] * nvox
        else:
            newVals = np.array(newVals)

        xyzs    = self.getSelection()
        oldVals = image[self._selection.selection]
        
        image[self._selection.selection] = newVals

        change = Change(image, xyzs, oldVals, newVals)

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
        change.image[change.selection] = change.newVals

        
    def _revertChange(self, change):
        change.image[change.selection] = change.oldVals
