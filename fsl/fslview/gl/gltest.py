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

        texName = '{}_{}'.format(id(self.image), type(self).__name__)

        self.colourTexture = textures.ColourMapTexture(texName)
        self.imageTexture  = textures.getTexture(
            textures.ImageTexture,
            texName,
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


    def preDraw(self):

        self.imageTexture .bindTexture(gl.GL_TEXTURE0)
        self.colourTexture.bindTexture(gl.GL_TEXTURE1)
        fslgl.gltest_funcs.preDraw(self)


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
        
        fslgl.gltest_funcs.draw(self, vertices, indices, texCoords)


    def postDraw(self):
        self.imageTexture .unbindTexture()
        self.colourTexture.unbindTexture()
        fslgl.gltest_funcs.postDraw(self)
