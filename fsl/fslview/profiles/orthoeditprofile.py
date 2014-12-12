#!/usr/bin/env python
#
# orthoeditprofile.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)


import numpy                      as np
import                               wx

import fsl.utils.transform        as transform
import fsl.fslview.editor.editor  as editor
import fsl.fslview.gl.annotations as annotations


def register(canvasPanel, imageList,  displayCtx):
    return OrthoEditProfile(canvasPanel, imageList,  displayCtx)


def deregister(orthoEditProf):
    orthoEditProf.deregister()


class OrthoEditProfile(object):

    def __init__(self, canvasPanel, imageList, displayCtx):
        self._canvasPanel = canvasPanel
        self._imageList   = imageList
        self._displayCtx  = displayCtx
        self._editor      = editor.Editor(imageList, displayCtx)
        self._name        = '{}_{}'.format(self.__class__.__name__, id(self))

        self.register()


    def register(self):

        xcanvas = self._canvasPanel.getXCanvas()
        ycanvas = self._canvasPanel.getYCanvas()
        zcanvas = self._canvasPanel.getZCanvas()

        xcanvas.Bind(wx.EVT_LEFT_DOWN, self._onMouseEvent)
        ycanvas.Bind(wx.EVT_LEFT_DOWN, self._onMouseEvent)
        zcanvas.Bind(wx.EVT_LEFT_DOWN, self._onMouseEvent)
        xcanvas.Bind(wx.EVT_MOTION,    self._onMouseEvent)
        ycanvas.Bind(wx.EVT_MOTION,    self._onMouseEvent)
        zcanvas.Bind(wx.EVT_MOTION,    self._onMouseEvent)

        selection = self._editor._selection

        image   = self._displayCtx.getSelectedImage()
        display = self._displayCtx.getDisplayProperties(image)

        self.voxelSelection = annotations.VoxelSelection(
            selection,
            display.displayToVoxMat,
            display.voxToDisplayMat)

        xcanvas.getAnnotations().obj(self.voxelSelection, hold=True)
        ycanvas.getAnnotations().obj(self.voxelSelection, hold=True)
        zcanvas.getAnnotations().obj(self.voxelSelection, hold=True)

    
    def deregister(self):
        xcanvas = self._canvasPanel.getXCanvas()
        ycanvas = self._canvasPanel.getYCanvas()
        zcanvas = self._canvasPanel.getZCanvas() 
        xcanvas.Bind(wx.EVT_LEFT_DOWN, None)
        ycanvas.Bind(wx.EVT_LEFT_DOWN, None)
        zcanvas.Bind(wx.EVT_LEFT_DOWN, None)
        xcanvas.Bind(wx.EVT_MOTION,    None)
        ycanvas.Bind(wx.EVT_MOTION,    None)
        zcanvas.Bind(wx.EVT_MOTION,    None)

        xcanvas.getAnnotations().dequeue(self.voxelSelection)
        ycanvas.getAnnotations().dequeue(self.voxelSelection)
        zcanvas.getAnnotations().dequeue(self.voxelSelection)

        
    def _onMouseEvent(self, ev):

        if not ev.LeftIsDown():       return
        if len(self._imageList) == 0: return

        image   = self._displayCtx.getSelectedImage()
        display = self._displayCtx.getDisplayProperties(image)

        mx, my  = ev.GetPositionTuple()
        source  = ev.GetEventObject()
        w, h    = source.GetClientSize()

        my = h - my

        xpos, ypos = source.canvasToWorld(mx, my)
        zpos       = source.pos.z

        voxel = np.zeros(3)
        voxel[source.xax] = xpos
        voxel[source.yax] = ypos
        voxel[source.zax] = zpos
        
        voxel = transform.transform(
            [voxel],
            display.displayToVoxMat)[0]

        voxel = np.array(np.round(voxel), dtype=np.int32)

        if wx.GetKeyState(wx.WXK_CONTROL):
            value = image.data[voxel[0], voxel[1], voxel[2]]
            self._editor.getSelection().clearSelection()
            self._editor.getSelection().selectByValue(value, precision=100)
        else:
            self._editor.getSelection().selectBlock(
                voxel, 25) # , [source.xax, source.yax])

        self._canvasPanel.Refresh()
