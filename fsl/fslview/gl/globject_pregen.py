#!/usr/bin/env python
#
# globject_pregen.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import wx

import numpy                   as np
import OpenGL.GL               as gl

import fsl.fslview.gl.textures as textures
import fsl.utils.transform     as transform


log = logging.getLogger(__name__)


class GLImageObject_pregen(object):

    def __init__(self, realGLObj):

        self.__maxTextures = 256
        self.__realGLObj   = realGLObj

        self.__textureDirty   = []
        self.__textures       = []

        self.__lastDrawnTexture = None
        self.__updateQueue      = []

        self.__realGLObj.addUpdateListener(
            '{}_{}'.format(type(self).__name__, id(self)),
            self.__refreshAllTextures)

        wx.GetApp().Bind(wx.EVT_IDLE, self.__textureUpdateLoop)

            
    def __refreshAllTextures(self, *a):

        # if self.__lastDrawnTexture is not None:
        #     lastIdx = self.__lastDrawnTexture
        # else:
        #     lastIdx = len(self.__textures) / 2

        # idxs   = np.zeros(len(self.__textures), dtype=np.uint32)

        idxs = list(range(len(self.__textures)))

        # idxs[  0::2] = np.arange(lastIdx - 1,     -1,                 -1)
        # idxs[  1::2] = np.arange(lastIdx,  len(self.__textures), 1)

        self.__textureDirty = [True] * len(self.__textures)
        self.__updateQueue  = idxs


    def __zposToIndex(self, zpos):
        zmin  = self.__zmin
        zmax  = self.__zmax
        ntexs = len(self.__textures)
        return int(ntexs * (zpos - zmin) / (zmax - zmin))

    
    def __indexToZpos(self, index):
        zmin  = self.__zmin
        zmax  = self.__zmax
        ntexs = len(self.__textures)
        return index * (zmax - zmin) / ntexs + zmin


    def __textureUpdateLoop(self, ev):
        ev.Skip()

        if len(self.__updateQueue) == 0 or len(self.__textures) == 0:
            return

        idx = self.__updateQueue.pop(0)

        if not self.__textureDirty[idx]:
            return

        tex = self.__textures[idx]
        
        log.debug('Refreshing texture slice {} (zax {})'.format(
            idx, self.__realGLObj.zax))
        
        self.__refreshTexture(tex, idx)

        if len(self.__updateQueue) > 0:
            ev.RequestMore()

            
    def getRealGLObject(self):
        return self.__realGLObj

    
    def setAxes(self, xax, yax):

        self.__realGLObj.setAxes(xax, yax)

        image   = self.__realGLObj.image
        display = self.__realGLObj.display
        zax     = self.__realGLObj.zax
 
        if display.transform in ('id', 'pixdim'):
            numTextures = image.shape[zax]
        else:
            numTextures = self.__maxTextures

        lo, hi = display.getDisplayBounds()

        self.__zmin = lo[zax]
        self.__zmax = hi[zax]

        self.__destroyTextures()
        
        for i in range(numTextures):
            self.__textures.append(
                textures.ImageRenderTexture(
                    None, image, display, xax, yax))

        self.__textureDirty = [True] * numTextures
        self.__refreshAllTextures()

        
    def __destroyTextures(self):
        texes = self.__textures
        self.__textures = []
        for tex in texes:
            wx.CallLater(50, tex.destroy)
        
    
    def destroy(self):
        self.__destroyTextures()

    
    def preDraw(self):
        pass


    def __refreshTexture(self, tex, idx):

        display = self.__realGLObj.display
        xax     = self.__realGLObj.xax
        yax     = self.__realGLObj.yax
        zax     = self.__realGLObj.zax
        zpos    = self.__indexToZpos(idx)

        log.debug('Refreshing render texture for slice {} (zpos {}, '
                  'zax {})'.format(idx, zpos, self.__realGLObj.zax))

        lo, hi = display.getDisplayBounds() 

        width, height = tex.getSize()
        oldSize       = gl.glGetIntegerv(gl.GL_VIEWPORT)
        oldProjMat    = gl.glGetFloatv(  gl.GL_PROJECTION_MATRIX)
        oldMVMat      = gl.glGetFloatv(  gl.GL_MODELVIEW_MATRIX)

        gl.glViewport(0, 0, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()

        gl.glOrtho(lo[xax], hi[xax],
                   lo[yax], hi[yax],
                   -1,      1)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
        if zax == 0:
            gl.glRotatef(-90, 1, 0, 0)
            gl.glRotatef(-90, 0, 0, 1)
        elif zax == 1:
            gl.glRotatef(270, 1, 0, 0)

        trans = [0, 0, 0]
        trans[zax] = -zpos
        gl.glTranslatef(*trans)                

        tex.bindAsRenderTarget()
        self.__realGLObj.preDraw()
        self.__realGLObj.draw(zpos)
        self.__realGLObj.postDraw()
        tex.unbindAsRenderTarget()
        
        gl.glViewport(*oldSize)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadMatrixf(oldProjMat)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadMatrixf(oldMVMat)

        self.__textureDirty[idx] = False

    
    def draw(self, zpos, xform=None):

        display = self.__realGLObj.display
        xax     = self.__realGLObj.xax
        yax     = self.__realGLObj.yax
        zax     = self.__realGLObj.zax

        if not display.enabled:
            return
        
        texIdx                  = self.__zposToIndex(zpos)
        self.__lastDrawnTexture = texIdx

        if texIdx < 0 or texIdx >= len(self.__textures):
            return

        lo, hi  = display.getDisplayBounds()
        texture = self.__textures[texIdx]

        if self.__textureDirty[texIdx]:
            self.__refreshTexture(texture, texIdx)

        vertices = np.zeros((6, 3), dtype=np.float32)
        vertices[:, zax] = zpos
        vertices[0, [xax, yax]] = lo[xax], lo[yax]
        vertices[1, [xax, yax]] = lo[xax], hi[yax]
        vertices[2, [xax, yax]] = hi[xax], lo[yax]
        vertices[3, [xax, yax]] = hi[xax], lo[yax]
        vertices[4, [xax, yax]] = lo[xax], hi[yax]
        vertices[5, [xax, yax]] = hi[xax], hi[yax]

        if xform is not None:
            vertices = transform.transform(vertices, xform=xform)

        texture.draw(vertices)


    def drawAll(self, zposes, xforms):
        for zpos, xform in zip(zposes, xforms):
            self.draw(zpos, xform)
    

    def postDraw(self):
        pass
