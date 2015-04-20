#!/usr/bin/env python
#
# gllinevector.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging


import numpy                   as np
import fsl.fslview.gl          as fslgl
import fsl.fslview.gl.globject as globject
import fsl.fslview.gl.glvector as glvector
import fsl.utils.transform     as transform


class GLLineVector(glvector.GLVector):

    def __init__(self, image, display):
        glvector.GLVector.__init__(self, image, display)

        self.__generateLineVertices()

        def vertexUpdate(*a):
            self.__generateLineVertices()
            self.updateShaderState()
            self.onUpdate()

        display.addListener('transform',  self.name, vertexUpdate)
        display.addListener('resolution', self.name, vertexUpdate)

        fslgl.gllinevector_funcs.init(self)

        
    def destroy(self):
        fslgl.gllinevector_funcs.destroy(self)
        self.display.removeListener('transform',  self.name)
        self.display.removeListener('resolution', self.name)


    def __generateLineVertices(self):

        display  = self.display
        image    = self.image
        data     = globject.subsample(image.data,
                                      display.resolution,
                                      image.pixdim)

        vertices = np.array(data, dtype=np.float32)

        x = vertices[:, :, :, 0]
        y = vertices[:, :, :, 1]
        z = vertices[:, :, :, 2]

        lens = np.sqrt(x ** 2 + y ** 2 + z ** 2)

        # scale the vector lengths to 0.5
        vertices[:, :, :, 0] = 0.5 * x / lens
        vertices[:, :, :, 1] = 0.5 * y / lens
        vertices[:, :, :, 2] = 0.5 * z / lens

        # Scale the vector data by the minimum
        # voxel length, so it is a unit vector
        # within real world space
        vertices /= (image.pixdim[:3] / min(image.pixdim[:3]))
        
        # Duplicate vector data so that each
        # vector is represented by two vertices,
        # representing a line through the origin
        vertices = np.concatenate((-vertices, vertices), axis=3)
        vertices = vertices.reshape((data.shape[0],
                                     data.shape[1],
                                     data.shape[2],
                                     2,
                                     3))

        # Offset each vertex by the
        # corresponding voxel coordinates
        for i in range(data.shape[0]): vertices[i, :, :, :, 0] += i
        for i in range(data.shape[1]): vertices[:, i, :, :, 1] += i
        for i in range(data.shape[2]): vertices[:, :, i, :, 2] += i

        self.voxelVertices = vertices
    

    def compileShaders(self):
        fslgl.gllinevector_funcs.compileShaders(self)
        

    def updateShaderState(self):
        fslgl.gllinevector_funcs.updateShaderState(self)
 

    def preDraw(self):
        glvector.GLVector.preDraw(self)
        fslgl.gllinevector_funcs.preDraw(self)


    def draw(self, zpos, xform=None):
        fslgl.gllinevector_funcs.draw(self, zpos, xform)

    
    def drawAll(self, zposes, xforms):
        fslgl.gllinevector_funcs.drawAll(self, zposes, xforms) 

    
    def postDraw(self):
        glvector.GLVector.postDraw(self)
        fslgl.gllinevector_funcs.postDraw(self) 
