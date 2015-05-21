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
import fsl.data.image               as fslimage
import fsl.fslview.editor.editor    as editor
import fsl.fslview.gl.annotations   as annotations

import orthoviewprofile


class OrthoEditProfile(orthoviewprofile.OrthoViewProfile):

    selectionSize  = props.Int(minval=1, default=3)
    selectionIs3D  = props.Boolean(default=False)
    fillValue      = props.Real(default=0)

    intensityThres = props.Real(minval=0.0, default=10)
    localFill      = props.Boolean(default=False)

    selectionCursorColour  = props.Colour(default=(1, 1, 0, 0.7))
    selectionOverlayColour = props.Colour(default=(1, 0, 1, 0.7))

    searchRadius   = props.Real(minval=0.0, default=0.0)

    
    def clearSelection(self, *a):
        self._editor.getSelection().clearSelection()


    def fillSelection(self, *a):
        self._editor.fillSelection(self.fillValue)


    def undo(self, *a):

        # We're disabling notification of changes to the selection
        # during undo/redo. This is because a single undo
        # will probably involve multiple modifications to the
        # selection (as changes are grouped by the editor),
        # with each of those changes causing the selection object
        # to notify its listeners. As one of these listeners is a
        # SelectionTexture, these notifications can get expensive,
        # due to updates to the GL texture buffer. So we disable
        # notification, and then manually refresh the texture
        # afterwards
        self._editor.getSelection().disableNotification('selection')
        self._editor.undo()
        self._editor.getSelection().enableNotification('selection')
        
        self._selectionChanged()
        self._selAnnotation.texture.refresh()


    def redo(self, *a):

        self._editor.getSelection().disableNotification('selection')
        self._editor.redo()
        self._editor.getSelection().enableNotification('selection')
        self._selectionChanged()
        self._selAnnotation.texture.refresh() 
 

    def __init__(self, canvasPanel, overlayList, displayCtx):

        self._editor         = editor.Editor(overlayList, displayCtx) 
        self._xcanvas        = canvasPanel.getXCanvas()
        self._ycanvas        = canvasPanel.getYCanvas()
        self._zcanvas        = canvasPanel.getZCanvas() 
        self._selAnnotation  = None
        self._selecting      = False
        self._lastDist       = None
        self._currentOverlay = None
        
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
            overlayList,
            displayCtx,
            ['sel', 'desel', 'selint'],
            actions)

        displayCtx .addListener('selectedOverlay',
                                self._name,
                                self._selectedOverlayChanged)
        overlayList.addListener('overlays',
                                self._name,
                                self._selectedOverlayChanged)

        self._editor.addListener('canUndo',
                                 self._name,
                                 self._undoStateChanged)
        self._editor.addListener('canRedo',
                                 self._name,
                                 self._undoStateChanged)

        self.addListener('selectionOverlayColour',
                         self._name,
                         self._selectionColoursChanged)
        self.addListener('selectionCursorColour',
                         self._name,
                         self._selectionColoursChanged) 

        self._selectedOverlayChanged()
        self._selectionChanged()
        self._undoStateChanged()


    def _undoStateChanged(self, *a):
        self.enable('undo', self._editor.canUndo)
        self.enable('redo', self._editor.canRedo)


    def _selectionColoursChanged(self, *a):
        if self._selAnnotation is not None:
            self._selAnnotation.colour = self.selectionOverlayColour


    def _selectedOverlayChanged(self, *a):

        overlay   = self._displayCtx.getSelectedOverlay()
        selection = self._editor.getSelection() 
        xannot    = self._xcanvas.getAnnotations()
        yannot    = self._ycanvas.getAnnotations()
        zannot    = self._zcanvas.getAnnotations()        

        # If the selected overlay hasn't changed,
        # we don't need to do anything
        if overlay == self._currentOverlay:
            return

        # If there's already an existing
        # selection object, clear it 
        if self._selAnnotation is not None:
            xannot.dequeue(self._selAnnotation, hold=True)
            yannot.dequeue(self._selAnnotation, hold=True)
            zannot.dequeue(self._selAnnotation, hold=True)
            
            self._selAnnotation.destroy()
            self._selAnnotation = None

        self._currentOverlay = overlay

        # If there is no selected overlay (the overlay
        # list is empty), don't do anything.
        if overlay is None:
            return

        display = self._displayCtx.getDisplay(overlay)

        # Edit mode is only supported on images with
        # the 'volume' type, in 'id' or 'pixdim'
        # transformation for the time being
        if not isinstance(overlay, fslimage.Image) or \
           display.overlayType != 'volume'         or \
           display.transform not in ('id', 'pixdim'):
            
            self._currentOverlay = None
            log.warn('Editing is only possible on volume '
                     'images, in ID or pixdim space.')
            return

        # Otherwise, create a selection annotation
        # and queue it on the canvases for drawing

        selection.addListener('selection', self._name, self._selectionChanged)

        self._selAnnotation = annotations.VoxelSelection( 
            selection,
            display.getTransform('display', 'voxel'),
            display.getTransform('voxel',   'display'),
            colour=self.selectionOverlayColour)
        
        xannot.obj(self._selAnnotation,  hold=True)
        yannot.obj(self._selAnnotation,  hold=True)
        zannot.obj(self._selAnnotation,  hold=True)
        self._canvasPanel.Refresh()


    def _selectionChanged(self, *a):
        selection = self._editor.getSelection()
        selSize   = selection.getSelectionSize()

        self.enable('createMaskFromSelection', selSize > 0)
        self.enable('createROIFromSelection',  selSize > 0)
        self.enable('clearSelection',          selSize > 0)
        self.enable('fillSelection',           selSize > 0)

    
    def deregister(self):
        if self._selAnnotation is not None:
            sa = self._selAnnotation
            self._xcanvas.getAnnotations().dequeue(sa, hold=True)
            self._ycanvas.getAnnotations().dequeue(sa, hold=True)
            self._zcanvas.getAnnotations().dequeue(sa, hold=True)
            sa.destroy()
            
        orthoviewprofile.OrthoViewProfile.deregister(self)

        
    def _getVoxelLocation(self, canvasPos):
        """Returns the voxel location, for the currently selected overlay,
        which corresponds to the specified canvas position.
        """
        display = self._displayCtx.getDisplay(self._currentOverlay)

        voxel = transform.transform(
            [canvasPos], display.getTransform('display', 'voxel'))[0]

        # Using floor(voxel+0.5) because, when at the
        # midpoint, I want to round up. np.round rounds
        # to the nearest even number, which is not ideal
        voxel = np.array(np.floor(voxel + 0.5), dtype=np.int32)

        return voxel
        

    def _makeSelectionAnnotation(self, canvas, voxel, blockSize=None):
        """Highlights the specified voxel with a selection annotation.
        This is used by mouse motion event handlers, so the user can
        see the possible selection, and thus what would happen if they
        were to click.
        """

        display = self._displayCtx.getDisplay(self._currentOverlay)
        shape   = self._currentOverlay.shape
        
        if self.selectionIs3D: axes = (0, 1, 2)
        else:                  axes = (canvas.xax, canvas.yax)

        if blockSize is None:
            blockSize = self.selectionSize

        block, offset = self._editor.getSelection().generateBlock(
            voxel, blockSize, shape, axes)

        colour    = self.selectionCursorColour
        colour[3] = 1.0

        for canvas in [self._xcanvas, self._ycanvas, self._zcanvas]:
            canvas.getAnnotations().grid(
                block,
                display.getTransform('display', 'voxel'),
                display.getTransform('voxel',   'display'),
                offsets=offset,
                colour=colour)


    def _applySelection(self, canvas, voxel, add=True):

        if self.selectionIs3D: axes = (0, 1, 2)
        else:                  axes = (canvas.xax, canvas.yax)        

        selection     = self._editor.getSelection()
        block, offset = selection.generateBlock(voxel,
                                                self.selectionSize,
                                                selection.selection.shape,
                                                axes)

        if add: selection.addToSelection(     block, offset)
        else:   selection.removeFromSelection(block, offset)

            
    def _selModeMouseWheel(self, ev, canvas, wheelDir, mousePos, canvasPos):

        if   wheelDir > 0: self.selectionSize += 1
        elif wheelDir < 0: self.selectionSize -= 1

        voxel = self._getVoxelLocation(canvasPos)
        self._makeSelectionAnnotation(canvas, voxel)


    def _selModeMouseMove(self, ev, canvas, mousePos, canvasPos):
        voxel = self._getVoxelLocation(canvasPos)
        self._makeSelectionAnnotation(canvas, voxel)


    def _selModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        self._editor.startChangeGroup()

        voxel = self._getVoxelLocation(canvasPos)
        self._applySelection(         canvas, voxel)
        self._makeSelectionAnnotation(canvas, voxel) 


    def _selModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        voxel = self._getVoxelLocation(canvasPos)
        self._applySelection(         canvas, voxel)
        self._makeSelectionAnnotation(canvas, voxel)


    def _selModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        self._editor.endChangeGroup()

        
    def _deselModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):

        self._editor.startChangeGroup()

        voxel = self._getVoxelLocation(canvasPos)
        self._applySelection(         canvas, voxel, False)
        self._makeSelectionAnnotation(canvas, voxel) 


    def _deselModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        voxel = self._getVoxelLocation(canvasPos)
        self._applySelection(         canvas, voxel, False)
        self._makeSelectionAnnotation(canvas, voxel)

        
    def _deselModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        self._editor.endChangeGroup()

        
    def _selintModeMouseMove(self, ev, canvas, mousePos, canvasPos):
        voxel = self._getVoxelLocation(canvasPos)
        self._makeSelectionAnnotation(canvas, voxel, 1)

        
    def _selintModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):

        self._editor.startChangeGroup()
        self._editor.getSelection().clearSelection() 
        self._selecting = True
        self._lastDist  = 0
        self._selintSelect(self._getVoxelLocation(canvasPos))

        
    def _selintModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):

        mouseDownPos, canvasDownPos = self.getMouseDownLocation()
        voxel                       = self._getVoxelLocation(canvasDownPos)

        cx,  cy,  cz  = canvasPos
        cdx, cdy, cdz = canvasDownPos

        dist = np.sqrt((cx - cdx) ** 2 + (cy - cdy) ** 2 + (cz - cdz) ** 2)
        self.searchRadius = dist

        self._selintSelect(voxel)

        
    def _selintModeMouseWheel(self, ev, canvas, wheel, mousePos, canvasPos):

        if not self._selecting:
            return

        overlay = self._displayCtx.getSelectedOverlay()
        opts    = self._displayCtx.getOpts(overlay)

        step = opts.displayRange.xlen / 50.0

        if   wheel > 0: self.intensityThres += step
        elif wheel < 0: self.intensityThres -= step

        mouseDownPos, canvasDownPos = self.getMouseDownLocation()
        voxel                       = self._getVoxelLocation(canvasDownPos) 

        self._selintSelect(voxel)
        
            
    def _selintSelect(self, voxel):
        
        overlay = self._displayCtx.getSelectedOverlay()
        
        if self.searchRadius == 0:
            searchRadius = None
        else:
            searchRadius = (self.searchRadius / overlay.pixdim[0],
                            self.searchRadius / overlay.pixdim[1],
                            self.searchRadius / overlay.pixdim[2])

        # If the last selection covered a bigger radius
        # than this selection, clear the whole selection 
        if self._lastDist is None or \
           np.any(np.array(searchRadius) < self._lastDist):
            self._editor.getSelection().clearSelection()

        self._editor.getSelection().selectByValue(
            voxel,
            precision=self.intensityThres,
            searchRadius=searchRadius,
            local=self.localFill)

        self._lastDist = searchRadius

        
    def _selintModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        self._editor.endChangeGroup()
        self._selecting = False
