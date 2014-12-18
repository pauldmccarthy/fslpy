#!/usr/bin/env python
#
# orthoeditprofile.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)


import numpy                        as np

import                                 props
import fsl.utils.transform          as transform
import fsl.fslview.editor.editor    as editor
import fsl.fslview.editor.selection as editorselection
import fsl.fslview.gl.annotations   as annotations

import orthoviewprofile


class OrthoEditProfile(orthoviewprofile.OrthoViewProfile):

    selectionSize  = props.Int(minval=1, maxval=30, default=3, clamped=True)
    selectionIs3D  = props.Boolean(default=False)
    fillValue      = props.Real(default=0)

    intensityThres = props.Real(default=10)
    localFill      = props.Boolean(default=False)


    def clearSelection(self):
        self._editor.getSelection().clearSelection()


    def fillSelection(self):
        self._editor.fillSelection(self.fillValue)


    def undo(self):
        self._editor.undo() 


    def redo(self):
        self._editor.redo()
 

    def __init__(self, canvasPanel, imageList, displayCtx):

        self._editor = editor.Editor(imageList, displayCtx) 

        actions = {
            'undo'                    : self.undo,
            'redo'                    : self.redo,
            'fillSelection'           : self.fillSelection,
            'clearSelection'          : self.clearSelection,
            'createMaskFromSelection' : self._editor.createMaskFromSelection,
            'createROIFromSelection'  : self._editor.createROIFromSelection}

        orthoviewprofile.OrthoViewProfile.__init__(
            self,
            canvasPanel,
            imageList,
            displayCtx,
            ['sel', 'desel', 'selint'],
            actions)

        
        self._xcanvas = canvasPanel.getXCanvas()
        self._ycanvas = canvasPanel.getYCanvas()
        self._zcanvas = canvasPanel.getZCanvas() 

        self._voxelSelection = None

        displayCtx.addListener('selectedImage',
                               self._name,
                               self._selectedImageChanged)
        imageList.addListener( 'images',
                               self._name,
                               self._selectedImageChanged)

        self._editor.addListener('canUndo',
                                 self._name,
                                 self._undoStateChanged)
        self._editor.addListener('canRedo',
                                 self._name,
                                 self._undoStateChanged) 

        self._selectedImageChanged()
        self._selectionChanged()
        self._undoStateChanged()


    def _undoStateChanged(self, *a):
        self.enable('undo', self._editor.canUndo)
        self.enable('redo', self._editor.canRedo)

        
    def _getVoxelLocation(self, canvasPos):
        """Returns the voxel location, for the currently selected image,
        which corresponds to the specified canvas position.
        """
        image   = self._displayCtx.getSelectedImage()
        display = self._displayCtx.getDisplayProperties(image)

        voxel = transform.transform([canvasPos], display.displayToVoxMat)[0]

        # Using floor(voxel+0.5) because, when at the
        # midpoint, I want to round up. np.round rounds
        # to the nearest even number, which is not ideal
        voxel = np.array(np.floor(voxel + 0.5), dtype=np.int32)

        return voxel


    def _selectedImageChanged(self, *a):
        
        selection = self._editor.getSelection()

        selection.addListener('selection', self._name, self._selectionChanged)

        image   = self._displayCtx.getSelectedImage()
        display = self._displayCtx.getDisplayProperties(image)

        if self._voxelSelection is not None:
            self._xcanvas.getAnnotations().dequeue(self._voxelSelection,
                                                   hold=True)
            self._ycanvas.getAnnotations().dequeue(self._voxelSelection,
                                                   hold=True)
            self._zcanvas.getAnnotations().dequeue(self._voxelSelection,
                                                   hold=True)

        self._voxelSelection = annotations.VoxelSelection(
            selection.selection,
            display.displayToVoxMat,
            display.voxToDisplayMat)

        self._tempSelection  = editorselection.Selection(image.data)
        self._tempAnnotation = annotations.VoxelSelection(
            self._tempSelection.selection,
            display.displayToVoxMat,
            display.voxToDisplayMat,
            colour=(1, 1, 0, 0.7))
        
        self._xcanvas.getAnnotations().obj(self._voxelSelection, hold=True)
        self._ycanvas.getAnnotations().obj(self._voxelSelection, hold=True)
        self._zcanvas.getAnnotations().obj(self._voxelSelection, hold=True)
        self._canvasPanel.Refresh()


    def _selectionChanged(self, *a):
        selection = self._editor.getSelection()
        selSize   = selection.getSelectionSize()

        self.enable('createMaskFromSelection', selSize > 0)
        self.enable('createROIFromSelection',  selSize > 0)
        self.enable('clearSelection',          selSize > 0)
        self.enable('fillSelection',           selSize > 0)

    
    def deregister(self):
        self._xcanvas.getAnnotations().dequeue(self._voxelSelection, hold=True)
        self._ycanvas.getAnnotations().dequeue(self._voxelSelection, hold=True)
        self._zcanvas.getAnnotations().dequeue(self._voxelSelection, hold=True)
        orthoviewprofile.OrthoViewProfile.deregister(self)


    def _makeSelectionAnnotation(self, canvas, voxel, blockSize=None):
        """Highlights the specified voxel with a selection annotation.
        This is used by mouse motion event handlers, so the user can
        see the possible selection, and thus what would happen if they
        were to click.
        """

        image   = self._displayCtx.getSelectedImage()
        display = self._displayCtx.getDisplayProperties(image) 
        
        if self.selectionIs3D: axes = (0, 1, 2)
        else:                  axes = (canvas.xax, canvas.yax)

        if blockSize is None:
            blockSize = self.selectionSize

        block = self._editor.getSelection().generateBlock(
            voxel,
            blockSize,
            axes)

        selection = editorselection.Selection(image.data)
        selection.addToSelection(block)

        for canvas in [self._xcanvas, self._ycanvas, self._zcanvas]:
            canvas.getAnnotations().selection(
                selection.selection,
                display.displayToVoxMat,
                display.voxToDisplayMat,
                colour=(1, 1, 0))

            
    def _selModeMouseWheel(self, ev, canvas, wheelDir, mousePos, canvasPos):

        if   wheelDir > 0: self.selectionSize += 1
        elif wheelDir < 0: self.selectionSize -= 1

        voxel = self._getVoxelLocation(canvasPos)
        self._makeSelectionAnnotation(canvas, voxel)


    def _selModeMouseMove(self, ev, canvas, mousePos, canvasPos):

        voxel = self._getVoxelLocation(canvasPos)
        self._makeSelectionAnnotation(canvas, voxel)


    def _selModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):

        voxel = self._getVoxelLocation(canvasPos)

        if self.selectionIs3D: axes = (0, 1, 2)
        else:                  axes = (canvas.xax, canvas.yax)

        self._tempSelection.selectBlock(voxel, self.selectionSize, axes)

        self._xcanvas.getAnnotations().obj(self._tempAnnotation, hold=True)
        self._ycanvas.getAnnotations().obj(self._tempAnnotation, hold=True)
        self._zcanvas.getAnnotations().obj(self._tempAnnotation, hold=True)

        self._makeSelectionAnnotation(canvas, voxel) 


    def _selModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):

        voxel = self._getVoxelLocation(canvasPos)

        if self.selectionIs3D: axes = (0, 1, 2)
        else:                  axes = (canvas.xax, canvas.yax)

        self._tempSelection.selectBlock(voxel, self.selectionSize, axes) 
        self._makeSelectionAnnotation(canvas, voxel)

        
    def _selModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        self._xcanvas.getAnnotations().dequeue(self._tempAnnotation, hold=True)
        self._ycanvas.getAnnotations().dequeue(self._tempAnnotation, hold=True)
        self._zcanvas.getAnnotations().dequeue(self._tempAnnotation, hold=True)
        
        self._editor.getSelection().addToSelection(
            self._tempSelection.getIndices())

        self._tempSelection.clearSelection()


    def _deselModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):

        voxel = self._getVoxelLocation(canvasPos)

        if self.selectionIs3D: axes = (0, 1, 2)
        else:                  axes = (canvas.xax, canvas.yax)
        
        self._tempSelection.clearSelection()
        self._tempSelection.selectBlock(voxel, self.selectionSize, axes)

        self._xcanvas.getAnnotations().obj(self._tempAnnotation, hold=True)
        self._ycanvas.getAnnotations().obj(self._tempAnnotation, hold=True)
        self._zcanvas.getAnnotations().obj(self._tempAnnotation, hold=True)

        self._makeSelectionAnnotation(canvas, voxel) 


    def _deselModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        
        voxel = self._getVoxelLocation(canvasPos)

        if self.selectionIs3D: axes = (0, 1, 2)
        else:                  axes = (canvas.xax, canvas.yax)
                  
        self._tempSelection.selectBlock(voxel, self.selectionSize, axes)
        self._makeSelectionAnnotation(canvas, voxel)

        
    def _deselModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        self._xcanvas.getAnnotations().dequeue(self._tempAnnotation, hold=True)
        self._ycanvas.getAnnotations().dequeue(self._tempAnnotation, hold=True)
        self._zcanvas.getAnnotations().dequeue(self._tempAnnotation, hold=True)
        
        self._editor.getSelection().removeFromSelection(
            self._tempSelection.getIndices())

        self._tempSelection.clearSelection() 


    def _selintModeMouseMove(self, ev, canvas, mousePos, canvasPos):
        voxel = self._getVoxelLocation(canvasPos)
        self._makeSelectionAnnotation(canvas, voxel, 1)

        
    def _selintModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):

        self._xcanvas.getAnnotations().obj(self._tempAnnotation, hold=True)
        self._ycanvas.getAnnotations().obj(self._tempAnnotation, hold=True)
        self._zcanvas.getAnnotations().obj(self._tempAnnotation, hold=True) 
        
        voxel = self._getVoxelLocation(canvasPos)

        self.intensityThres = 0
        self._tempSelection.clearSelection()
        self._tempSelection.selectByValue(
            voxel, precision=self.intensityThres, local=self.localFill)

        
    def _selintModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):

        mouseDownPos, canvasDownPos = self.getMouseDownLocation()
        voxel                      = self._getVoxelLocation(canvasDownPos)

        xdiff = mousePos[0] - mouseDownPos[0]
        ydiff = mousePos[1] - mouseDownPos[1]

        dist = np.sqrt(xdiff * xdiff + ydiff * ydiff)

        self.intensityThres = dist

        self._tempSelection.clearSelection()
        self._tempSelection.selectByValue(
            voxel, precision=self.intensityThres, local=self.localFill) 
        

    def _selintModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):

        self._xcanvas.getAnnotations().dequeue(self._tempAnnotation, hold=True)
        self._ycanvas.getAnnotations().dequeue(self._tempAnnotation, hold=True)
        self._zcanvas.getAnnotations().dequeue(self._tempAnnotation, hold=True)

        self._editor.getSelection().clearSelection()
        self._editor.getSelection().addToSelection(
            self._tempSelection.getIndices())

        self._tempSelection.clearSelection() 
