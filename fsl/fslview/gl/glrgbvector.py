#!/usr/bin/env python
#
# glrgbvector.py - Display vector images in RGB mode.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This mdoule provides the :class:`GLRGBVector` class, for displaying 3D
vector images in RGB mode.
"""

import numpy                   as np
import fsl.fslview.gl          as fslgl
import fsl.fslview.gl.routines as glroutines
import fsl.fslview.gl.glvector as glvector
import fsl.utils.transform     as transform


class GLRGBVector(glvector.GLVector):


    def __prefilter(self, data):
        return np.abs(data)


    def __init__(self, image, display):

        glvector.GLVector.__init__(self, image, display, self.__prefilter)
        fslgl.glrgbvector_funcs.init(self)


    def generateVertices(self, zpos, xform):
        vertices, voxCoords, texCoords = glroutines.slice2D(
            self.image.shape[:3],
            self.xax,
            self.yax,
            zpos, 
            self.displayOpts.getTransform('voxel',   'display'),
            self.displayOpts.getTransform('display', 'voxel'))

        if xform is not None: 
            vertices = transform.transform(vertices, xform)

        return vertices, voxCoords, texCoords 


    def compileShaders(self):
        fslgl.glrgbvector_funcs.compileShaders(self)
        

    def updateShaderState(self):
        fslgl.glrgbvector_funcs.updateShaderState(self)


    def preDraw(self):
        glvector.GLVector.preDraw(self)
        fslgl.glrgbvector_funcs.preDraw(self)


    def draw(self, zpos, xform=None):
        fslgl.glrgbvector_funcs.draw(self, zpos, xform)

    
    def drawAll(self, zposes, xforms):
        fslgl.glrgbvector_funcs.drawAll(self, zposes, xforms) 

    
    def postDraw(self):
        glvector.GLVector.postDraw(self)
        fslgl.glrgbvector_funcs.postDraw(self) 
