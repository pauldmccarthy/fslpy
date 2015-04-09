#!/usr/bin/env python
#
# gltest.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging


import numpy     as np
import OpenGL.GL as gl

import fsl.fslview.gl          as fslgl
import fsl.fslview.gl.textures as textures
import fsl.fslview.gl.globject as globject
import fsl.utils.transform     as transform


log = logging.getLogger(__name__)


class GLTest(globject.GLImageObject):

    def __init__(self, image, display):
        globject.GLImageObject.__init__(self, image, display)

        self.texName = '{}_{}'.format(id(self.image), type(self).__name__)

        self.renderTexture = None
        self.colourTexture = textures.ColourMapTexture(self.texName)
        self.imageTexture  = textures.getTexture(
            textures.ImageTexture,
            self.texName,
            self.image,
            self.display)

        fslgl.gltest_funcs.init(self)

        self.refreshColourTexture()


    def refreshColourTexture(self):
        display = self.display
        opts    = self.displayOpts

        alpha  = display.alpha / 100.0
        cmap   = opts.cmap
        invert = opts.invert
        dmin   = opts.displayRange[0]
        dmax   = opts.displayRange[1]

        self.colourTexture.set(cmap=cmap,
                               invert=invert,
                               alpha=alpha,
                               displayRange=(dmin, dmax))
        


    def destroy(self):
        self.colourTexture.destroy()
        textures.deleteTexture(self.imageTexture)

        self.colourTexture = None
        self.imageTexture  = None

        fslgl.gltest_funcs.destroy(self)


    def setAxes(self, xax, yax):
        self.xax = xax
        self.yax = yax
        self.zax = 3 - xax - yax

        if self.renderTexture is not None:
            self.renderTexture.destroy()

        self.renderTexture = textures.ImageRenderTexture(
            self.texName,
            self.image,
            self.display,
            self.xax,
            self.yax) 


    def preDraw(self):
        pass

    def draw(self, zpos, xform=None):

        voxToDisplayMat = self.display.getTransform('voxel',   'display')
        displayToVoxMat = self.display.getTransform('display', 'voxel')

        vertices, indices = globject.slice2D(
            self.image.shape[:3],
            self.xax,
            self.yax,
            voxToDisplayMat)

        vertices[:, self.zax] = zpos

        texCoords  = transform.transform(vertices, displayToVoxMat)
        texCoords /= self.image.shape[:3]

        vertices  = np.array(vertices,  dtype=np.float32).ravel('C')
        texCoords = np.array(texCoords, dtype=np.float32).ravel('C')
        indices   = np.array(indices,   dtype=np.uint32) .ravel('C')

        lo, hi = self.display.getDisplayBounds() 

        width, height = self.renderTexture.getSize()
        oldSize       = gl.glGetIntegerv(gl.GL_VIEWPORT)
        oldProjMat    = gl.glGetFloatv(  gl.GL_PROJECTION_MATRIX)
        oldMVMat      = gl.glGetFloatv(  gl.GL_MODELVIEW_MATRIX)

        gl.glViewport(0, 0, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()

        gl.glOrtho(lo[self.xax], hi[self.xax],
                   lo[self.yax], hi[self.yax],
                   -1,      1)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
        if self.zax == 0:
            gl.glRotatef(-90, 1, 0, 0)
            gl.glRotatef(-90, 0, 0, 1)
        elif self.zax == 1:
            gl.glRotatef(270, 1, 0, 0)

        trans = [0, 0, 0]
        trans[self.zax] = -zpos
        gl.glTranslatef(*trans)                

        self.renderTexture.bindAsRenderTarget()
        self.imageTexture .bindTexture(gl.GL_TEXTURE0)
        self.colourTexture.bindTexture(gl.GL_TEXTURE1)
        fslgl.gltest_funcs.preDraw(self)
        fslgl.gltest_funcs.draw(self, vertices, indices, texCoords)
        self.imageTexture .unbindTexture()
        self.colourTexture.unbindTexture()
        fslgl.gltest_funcs.postDraw(self)        
        self.renderTexture.unbindAsRenderTarget()
        
        gl.glViewport(*oldSize)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadMatrixf(oldProjMat)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadMatrixf(oldMVMat)

        xax = self.xax
        yax = self.yax
        zax = self.zax

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

        self.renderTexture.draw(vertices)        


    def postDraw(self):
        pass
