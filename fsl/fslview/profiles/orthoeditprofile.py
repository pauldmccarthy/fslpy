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


        # Do this on image changed
        image   = self._imageList[0]
        display = self._displayCtx.getDisplayProperties(image)

        self._region = annotations.VoxelRegion(display.voxToDisplayMat)
 

    
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

        block = np.tile(voxel, (9, 1))

        block[  :3, source.yax] += 1
        block[6:,   source.yax] -= 1
        block[ ::3, source.xax] -= 1
        block[2::3, source.xax] += 1

        self._editor.addToSelection(block)
        self._region.addVoxels(     block)

        xcanvas = self._canvasPanel.getXCanvas()
        ycanvas = self._canvasPanel.getYCanvas()
        zcanvas = self._canvasPanel.getZCanvas()

        # selected = self._editor.getSelection()

        xcanvas.getAnnotations().obj(self._region)
        ycanvas.getAnnotations().obj(self._region)
        zcanvas.getAnnotations().obj(self._region)

        xcanvas.Refresh()
        ycanvas.Refresh()
        zcanvas.Refresh()
