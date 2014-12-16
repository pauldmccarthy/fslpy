#!/usr/bin/env python
#
# orthoeditprofile.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)


from collections import OrderedDict

import                                 wx
import numpy                        as np

import                                 props
import fsl.utils.transform          as transform
import fsl.fslview.editor.editor    as editor
import fsl.fslview.editor.selection as editorselection
import fsl.fslview.gl.annotations   as annotations

import orthoviewprofile


class OrthoEditProfile(orthoviewprofile.OrthoViewProfile):

    mode = props.Choice(
        OrderedDict([
            ('loc',    'Location'),
            ('sel',    'Select'),
            ('desel',  'Deselect'),
            ('selint', 'Select by intensity')]))


    selectionSize  = props.Int(minval=1, maxval=30, default=3, clamped=True)
    selectionIs3D  = props.Boolean(default=False)
    intensityThres = props.Real(default=10)
    fillValue      = props.Real(default=0)


    def createMaskFromSelection(self):
        pass


    def clearSelection(self):
        self._editor.getSelection().clearSelection()


    def fillSelection(self):
        self._editor.fillSelection(self.fillValue)


    def undo(self):
        if self._editor.canUndo():
            self._editor.undo() 


    def redo(self):
        if self._editor.canRedo():
            self._editor.redo()

    
    def __init__(self, canvasPanel, imageList, displayCtx):

        orthoviewprofile.OrthoViewProfile.__init__(
            self,
            canvasPanel,
            imageList,
            displayCtx)

        self.addAction('undo',
                       'Undo',
                       self.undo)
        self.addAction('redo',
                       'Redo',
                       self.redo)
        self.addAction('fillSelection',
                       'Fill selection',
                       self.fillSelection)
        self.addAction('clearSelection',
                       'Clear selection',
                       self.clearSelection)
        self.addAction('createMaskFromSelection',
                       'Create mask',
                       self.createMaskFromSelection) 

        self.addTempMode('sel', wx.WXK_ALT, 'desel')
        
        self._xcanvas = canvasPanel.getXCanvas()
        self._ycanvas = canvasPanel.getYCanvas()
        self._zcanvas = canvasPanel.getZCanvas() 
        
        self._editor         = editor.Editor(imageList, displayCtx)
        self._voxelSelection = None

        self.addAltHandler('sel',   'LeftMouseDown', 'sel',   'LeftMouseDrag')
        self.addAltHandler('desel', 'LeftMouseDown', 'desel', 'LeftMouseDrag')
        self.addAltHandler('desel', 'MouseMove',     'sel',   'MouseMove')
        self.addAltHandler('selint', 'LeftMouseDown',
                           'selint', 'LeftMouseDrag')


        displayCtx.addListener('selectedImage',
                               self._name,
                               self._selectedImageChanged)
        imageList.addListener( 'images',
                               self._name,
                               self._selectedImageChanged)

        self._selectedImageChanged()


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
        
        selection = self._editor._selection

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
            selection,
            display.displayToVoxMat,
            display.voxToDisplayMat)

        self._xcanvas.getAnnotations().obj(self._voxelSelection, hold=True)
        self._ycanvas.getAnnotations().obj(self._voxelSelection, hold=True)
        self._zcanvas.getAnnotations().obj(self._voxelSelection, hold=True)
        self._canvasPanel.Refresh()

    
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
                selection,
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
        
        image = self._displayCtx.getSelectedImage()
        voxel = self._getVoxelLocation(canvasPos)
        value = image.data[voxel[0], voxel[1], voxel[2]]
        
        self._editor.getSelection().clearSelection()
        self._editor.getSelection().selectByValue(
            value, precision=self.intensityThres)
        
        self._makeSelectionAnnotation(canvas, voxel, 1) 

        
    def _selintModeMouseWheel(self, canvas, wheel, mousePos, canvasPos):

        if wheel > 0: self.intensityThres += 10
        else:         self.intensityThres -= 10

        self._selintModeLeftMouseDrag(canvas, *self.getLastMouseLocation())
