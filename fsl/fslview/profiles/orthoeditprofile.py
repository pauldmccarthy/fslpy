#!/usr/bin/env python
#
# orthoeditprofile.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)


from collections import OrderedDict

import numpy                      as np

import                               props
import fsl.utils.transform        as transform
import fsl.fslview.editor.editor  as editor
import fsl.fslview.gl.annotations as annotations

import orthoviewprofile


class OrthoEditProfile(orthoviewprofile.OrthoViewProfile):

    mode = props.Choice(
        OrderedDict([
            ('loc',    'Location'),
            ('sel',    'Select'),
            ('selint', 'Select by intensity')]))


    selectionSize  = props.Int(minval=1, maxval=30, default=3, clamped=True)
    selectionIs3D  = props.Boolean(default=False)
    intensityThres = props.Real(default=10)
    
    def __init__(self, canvasPanel, imageList, displayCtx):

        orthoviewprofile.OrthoViewProfile.__init__(
            self,
            canvasPanel,
            imageList,
            displayCtx)
        
        self._xcanvas = canvasPanel.getXCanvas()
        self._ycanvas = canvasPanel.getYCanvas()
        self._zcanvas = canvasPanel.getZCanvas() 
        
        self._editor         = editor.Editor(imageList, displayCtx)
        self._voxelSelection = None

        self.addAltHandler('sel', 'LeftMouseDown', 'sel', 'LeftMouseDrag')
        self.addAltHandler('selint', 'LeftMouseDown',
                           'selint', 'LeftMouseDrag')

        displayCtx.addListener('selectedImage',
                               self._name,
                               self._selectedImageChanged)
        imageList.addListener( 'images',
                               self._name,
                               self._selectedImageChanged)

        self._selectedImageChanged()


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


    def _selModeLeftMouseDrag(self, canvas, mousePos, canvasPos):

        image   = self._displayCtx.getSelectedImage()
        display = self._displayCtx.getDisplayProperties(image)

        voxel = transform.transform([canvasPos], display.displayToVoxMat)[0]

        # Using floor(voxel+0.5) because, when at the
        # midpoint, I want to round up. np.round rounds
        # to the nearest even number, which is not ideal
        voxel = np.array(np.floor(voxel + 0.5), dtype=np.int32)

        if self.selectionIs3D:
            self._editor.getSelection().selectBlock(voxel, self.selectionSize)
        else:
            self._editor.getSelection().selectBlock(voxel,
                                                    self.selectionSize,
                                                    (canvas.xax, canvas.yax))

        
    def _selintModeLeftMouseDrag(self, canvas, mousePos, canvasPos):
        
        image   = self._displayCtx.getSelectedImage()
        display = self._displayCtx.getDisplayProperties(image)
        
        voxel = transform.transform([canvasPos], display.displayToVoxMat)[0]
        voxel = np.array(np.floor(voxel + 0.5), dtype=np.int32)
        value = image.data[voxel[0], voxel[1], voxel[2]]
        
        self._editor.getSelection().clearSelection()
        self._editor.getSelection().selectByValue(
            value, precision=self.intensityThres)

        
    def _selintModeMouseWheel(self, canvas, wheel):

        if wheel > 0: self.intensityThres += 10
        else:         self.intensityThres -= 10

        self._selintModeLeftMouseDrag(canvas, *self.getLastMouseLocation())
