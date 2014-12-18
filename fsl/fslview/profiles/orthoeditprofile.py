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
import fsl.data.image               as fslimage
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

    def createMaskFromSelection(self):

        selection = self._editor.getSelection()
        
        imageIdx = self._displayCtx.selectedImage
        image    = self._imageList[imageIdx]
        xyzs     = selection.getSelection()

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

        selection = self._editor.getSelection()

        imageIdx = self._displayCtx.selectedImage
        image    = self._imageList[imageIdx]
        xyzs     = selection.getSelection()

        xs = xyzs[:, 0]
        ys = xyzs[:, 1]
        zs = xyzs[:, 2]
        
        roi             = np.zeros(image.shape, image.data.dtype)
        roi[xs, ys, zs] = image.data[xs, ys, zs]

        xform = image.voxToWorldMat
        name  = '{}_roi'.format(image.name)

        roiImage = fslimage.Image(roi, xform, name)
        self._imageList.insert(imageIdx + 1, roiImage)


    def clearSelection(self):
        self._editor.getSelection().clearSelection()


    def fillSelection(self):
        self._editor.fillSelection(self.fillValue)


    def undo(self):
        self._editor.undo() 


    def redo(self):
        self._editor.redo()

    
    def __init__(self, canvasPanel, imageList, displayCtx):

        actions = {
            'undo'                    : self.undo,
            'redo'                    : self.redo,
            'fillSelection'           : self.fillSelection,
            'clearSelection'          : self.clearSelection,
            'createMaskFromSelection' : self.createMaskFromSelection,
            'createROIFromSelection'  : self.createROIFromSelection}
        

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
        
        self._editor         = editor.Editor(imageList, displayCtx)
        self._voxelSelection = None

        displayCtx.addListener('selectedImage',
                               self._name,
                               self._selectedImageChanged)
        imageList.addListener( 'images',
                               self._name,
                               self._selectedImageChanged)

        self._selectedImageChanged()
        self._selectionChanged()

        
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

        selection = editorselection.Selection(image)
        selection.addToSelection(block)

        for canvas in [self._xcanvas, self._ycanvas, self._zcanvas]:
            canvas.getAnnotations().selection(
                selection.selection,
                display.displayToVoxMat,
                display.voxToDisplayMat,
                colour=(1, 1, 0))

            
    def _selModeMouseWheel(self, canvas, wheelDir, mousePos, canvasPos):

        if   wheelDir > 0: self.selectionSize += 1
        elif wheelDir < 0: self.selectionSize -= 1

        voxel = self._getVoxelLocation(canvasPos)
        self._makeSelectionAnnotation(canvas, voxel)


    def _selModeMouseMove(self, canvas, mousePos, canvasPos):

        voxel = self._getVoxelLocation(canvasPos)
        self._makeSelectionAnnotation(canvas, voxel)


    def _selModeLeftMouseDrag(self, canvas, mousePos, canvasPos):

        voxel = self._getVoxelLocation(canvasPos)

        if self.selectionIs3D: axes = (0, 1, 2)
        else:                  axes = (canvas.xax, canvas.yax)
                  
        self._editor.getSelection().selectBlock(voxel,
                                                self.selectionSize,
                                                axes)
        self._makeSelectionAnnotation(canvas, voxel) 


    def _deselModeLeftMouseDrag(self, canvas, mousePos, canvasPos):
        
        voxel = self._getVoxelLocation(canvasPos)

        if self.selectionIs3D: axes = (0, 1, 2)
        else:                  axes = (canvas.xax, canvas.yax)
                  
        self._editor.getSelection().deselectBlock(voxel,
                                                  self.selectionSize,
                                                  axes)
        self._makeSelectionAnnotation(canvas, voxel)


    def _selintModeMouseMove(self, canvas, mousePos, canvasPos):
        voxel = self._getVoxelLocation(canvasPos)
        self._makeSelectionAnnotation(canvas, voxel, 1)

        
    def _selintModeLeftMouseDrag(self, canvas, mousePos, canvasPos):
        
        voxel = self._getVoxelLocation(canvasPos)
        
        self._editor.getSelection().clearSelection()
        self._editor.getSelection().selectByValue(
            voxel, precision=self.intensityThres, local=self.localFill)
        
        self._makeSelectionAnnotation(canvas, voxel, 1) 

        
    def _selintModeMouseWheel(self, canvas, wheel, mousePos, canvasPos):

        if wheel > 0: self.intensityThres += 10
        else:         self.intensityThres -= 10

        self._selintModeLeftMouseDrag(canvas, *self.getLastMouseLocation())
