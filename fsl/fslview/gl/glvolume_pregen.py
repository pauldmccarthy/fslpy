#!/usr/bin/env python
#
# glvolume_pregen.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""When the :attr:`.Display.transform` property is ``id`` or ``pixdim``, one
off-screen texture is created for every slice along the depth (``z``) axis;
these textures have the same resolution as the image, along the corresponding
``x`` and ``y`` axes.

When the :attr:`.Display.transform` is ``affine``, a collection of off-screen
textures are created at a fixed rate along the depth axis; each of these
textures has a size which is unrelated to the image resolution.
"""

import logging

import OpenGL.GL               as gl
import numpy                   as np

import fsl.utils.transform     as transform
import fsl.fslview.gl.textures as fsltextures
import fsl.fslview.gl.glvolume as glvolume


log = logging.getLogger(__name__)


class GLVolume_pregen(glvolume.GLVolume):

    
    def __init__(self, image, display):

        glvolume.GLVolume.__init__(self, image, display)

        self.maxSliceTextures = 256

    
    def init(self):

        self.sliceTextures = []
        self.sliceDirty    = []
        self.numSlices     = 0

        glvolume.GLVolume.init(self)

    
    def setAxes(self, xax, yax):

        glvolume.GLVolume.setAxes(self, xax, yax)

        self.xax = xax
        self.yax = yax
        self.zax = 3 - xax - yax

        for tex in self.sliceTextures:
            tex.destroy()

        if self.display.transform in ('id', 'pixdim'):
            self.numSlices = self.image.shape[self.zax]
        else:
            self.numSlices = self.maxSliceTextures

        lo, hi = self.display.getDisplayBounds()

        self.zmin = lo[self.zax]
        self.zmax = hi[self.zax]

        self.sliceTextures = []

        for i in range(self.numSlices):
            self.sliceTextures.append(
                fsltextures.ImageRenderTexture(
                    self.image, self.display, xax, yax))

        self.sliceDirty = [True] * self.numSlices


    def destroy(self):
        glvolume.GLVolume.destroy(self)

        for tex in self.sliceTextures:
            tex.destroy()
        
    
    def preDraw(self):
        pass

    
    def draw(self, zpos, xform=None):

        if not self.display.enabled:
            return

        texIdx = int(
            self.numSlices * (zpos - self.zmin) / (self.zmax - self.zmin))

        if texIdx < 0 or texIdx >= self.numSlices:
            return

        renderTexture = self.sliceTextures[texIdx]

        lo, hi = self.display.getDisplayBounds()

        if self.sliceDirty[texIdx]:

            width, height = renderTexture.getSize()
            oldSize       = gl.glGetIntegerv(gl.GL_VIEWPORT)
            oldProjMat    = gl.glGetFloatv(  gl.GL_PROJECTION_MATRIX)
            oldMVMat      = gl.glGetFloatv(  gl.GL_MODELVIEW_MATRIX)

            gl.glViewport(0, 0, width, height)
            gl.glMatrixMode(gl.GL_PROJECTION)
            gl.glLoadIdentity()

            gl.glOrtho(lo[self.xax], hi[self.xax],
                       lo[self.yax], hi[self.yax],
                       -1,           1)

            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glLoadIdentity() 
            
            renderTexture.bindAsRenderTarget()
            glvolume.GLVolume.preDraw( self)
            glvolume.GLVolume.draw(    self, zpos)
            glvolume.GLVolume.postDraw(self)
            renderTexture.unbind()
            self.sliceDirty[texIdx] = False

            gl.glViewport(*oldSize)
            gl.glMatrixMode(gl.GL_PROJECTION)
            gl.glLoadMatrixf(oldProjMat)

            gl.glOrtho(lo[self.xax], hi[self.xax],
                       lo[self.yax], hi[self.yax],
                       -1,           1)
            print 'Drawing dirty slice {}'.format(texIdx)
        else:
            print 'Drawing clean slice {}'.format(texIdx)

        vertices = np.zeros((6, 3), dtype=np.float32)
        vertices[:, self.zax] = zpos
        vertices[0, [self.xax, self.yax]] = lo[self.xax], lo[self.yax]
        vertices[1, [self.xax, self.yax]] = lo[self.xax], hi[self.yax]
        vertices[2, [self.xax, self.yax]] = hi[self.xax], lo[self.yax]
        vertices[3, [self.xax, self.yax]] = hi[self.xax], lo[self.yax]
        vertices[4, [self.xax, self.yax]] = lo[self.xax], hi[self.yax]
        vertices[5, [self.xax, self.yax]] = hi[self.xax], hi[self.yax]

        if xform is not None:
            vertices = transform.transform(vertices, xform=xform)

        renderTexture.draw(vertices)
        

    def drawAll(self, zposes, xforms):
        for zpos, xform in zip(zposes, xforms):
            self.draw(zpos, xform)

            
    def postDraw(self):
        pass
