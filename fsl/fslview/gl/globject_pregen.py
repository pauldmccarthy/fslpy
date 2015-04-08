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

        self.__renderTextures = []
        self.__renderDirty    = []
        self.__numTextures    = 0

        self.__updating       = False
        self.__updateIdx      = 0

        self.__realGLObj.addUpdateListener(
            '{}_{}'.format(type(self).__name__, id(self)),
            self.__updateTextures)


    def __updateTextures(self, *a):

        self.__renderDirty = [True] * self.__numTextures

        # An update is already in
        # progress - reset it
        if self.__updating:
            self.__updateIdx = 0
            return

        self.__updating = True
        
        ntexes = self.__numTextures
        zmin   = self.__zmin
        zmax   = self.__zmax
        texes  = self.__renderTextures
        zposes = np.arange(ntexes) * (zmax - zmin) / ntexes + zmin

        def updateOneTexture():

            idx  = self.__updateIdx
            tex  = texes[ idx]
            zpos = zposes[idx]
            
            if self.__renderDirty[idx]:
                log.debug('Refreshing texture slice {} ({}, zax {})'.format(
                    idx, zpos, self.__realGLObj.zax))
                self.__refreshTexture(tex, idx, zpos)

            idx              = (idx + 1) % ntexes
            self.__updateIdx = idx

            # The update is finished - 
            # clear the update flag
            if idx == 0:
                self.__updating = False

            # Queue the next slice
            else:
                wx.CallLater(50, updateOneTexture)
            

        wx.CallAfter(updateOneTexture)

            
    def getRealGLObject(self):
        return self.__realGLObj

    
    def setAxes(self, xax, yax):

        self.__realGLObj.setAxes(xax, yax)

        image   = self.__realGLObj.image
        display = self.__realGLObj.display
        zax     = self.__realGLObj.zax

        # reconfigure render textures
        for tex in self.__renderTextures:
            tex.destroy()
 
        if display.transform in ('id', 'pixdim'):
            self.__numTextures = image.shape[zax]
        else:
            self.__numTextures = self.__maxTextures

        lo, hi = display.getDisplayBounds()

        self.__zmin = lo[zax]
        self.__zmax = hi[zax]

        self.__renderTextures = []

        for i in range(self.__numTextures):
            self.__renderTextures.append(
                textures.ImageRenderTexture(
                    None, image, display, xax, yax))

        self.__renderDirty = [True] * self.__numTextures

        self.__updateTextures()

    
    def destroy(self):

        # This is slow, so should be done in a separate thread
        for tex in self.__renderTextures:
            tex.destroy()
            
        self.__renderTextures = []

    
    def preDraw(self):
        pass


    def __refreshTexture(self, tex, idx, zpos):

        log.debug('Refreshing render texture for slice {} (zpos {}, '
                  'zax {})'.format(idx, zpos, self.__realGLObj.zax))

        display = self.__realGLObj.display
        xax     = self.__realGLObj.xax
        yax     = self.__realGLObj.yax
        zax     = self.__realGLObj.zax

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
        
        self.__renderDirty[idx] = False

        gl.glViewport(*oldSize)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadMatrixf(oldProjMat)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadMatrixf(oldMVMat)

    
    def draw(self, zpos, xform=None):

        display = self.__realGLObj.display
        xax     = self.__realGLObj.xax
        yax     = self.__realGLObj.yax
        zax     = self.__realGLObj.zax
        zmin    = self.__zmin
        zmax    = self.__zmax

        if not display.enabled:
            return
        
        texIdx = int(self.__numTextures * (zpos - zmin) / (zmax - zmin))

        if texIdx < 0 or texIdx >= self.__numTextures:
            return

        lo, hi        = display.getDisplayBounds()
        renderTexture = self.__renderTextures[texIdx]

        if self.__renderDirty[texIdx]:
            self.__refreshTexture(renderTexture, texIdx, zpos)

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

        renderTexture.draw(vertices)


    def drawAll(self, zposes, xforms):
        for zpos, xform in zip(zposes, xforms):
            self.draw(zpos, xform)
    

    def postDraw(self):
        pass
