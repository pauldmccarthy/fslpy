#!/usr/bin/env python
#
# gllinevector.py - Displays vector data as lines.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import numpy                   as np

import fsl.utils.transform     as transform
import fsl.fslview.gl          as fslgl
import fsl.fslview.gl.globject as globject
import fsl.fslview.gl.glvector as glvector


log = logging.getLogger(__name__)


class GLLineVector(glvector.GLVector):


    __vertices = {}


    def __init__(self, image, display):
        glvector.GLVector.__init__(self, image, display)

        self.opts = display.getDisplayOpts()

        self.__generateLineVertices()

        def vertexUpdate(*a):
            self.__generateLineVertices()
            self.updateShaderState()
            self.onUpdate()

        display  .addListener('transform',  self.name, vertexUpdate)
        display  .addListener('resolution', self.name, vertexUpdate)
        self.opts.addListener('directed',   self.name, vertexUpdate)

        fslgl.gllinevector_funcs.init(self)

        
    def destroy(self):
        
        fslgl.gllinevector_funcs.destroy(self)
        self.display.removeListener('transform',  self.name)
        self.display.removeListener('resolution', self.name)
        self.opts   .removeListener('directed',   self.name)


    def __generateLineVertices(self):

        display = self.display
        opts    = self.opts
        image   = self.image

        vertices, starts, steps, oldHash = GLLineVector.__vertices.get(
            image, (None, None, None, None))

        newHash = (hash(display.transform)  ^
                   hash(display.resolution) ^
                   hash(opts   .directed))

        if (vertices is not None) and (oldHash == newHash):
            
            log.debug('Using previously calculated line '
                      'vertices for {}'.format(image))
            self.voxelVertices = vertices
            self.sampleStarts  = starts
            self.sampleSteps   = steps 
            return

        log.debug('Re-generating line vertices for {}'.format(image))

        data, starts, steps = globject.subsample(image.data,
                                                 display.resolution,
                                                 image.pixdim)
        
        vertices = np.array(data, dtype=np.float32)
        x        = vertices[:, :, :, 0]
        y        = vertices[:, :, :, 1]
        z        = vertices[:, :, :, 2]
        lens     = np.sqrt(x ** 2 + y ** 2 + z ** 2)

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
        if opts.directed:
            origins  = np.zeros(vertices.shape, dtype=np.float32)
            vertices = np.concatenate((origins, vertices), axis=3)
        else:
            vertices = np.concatenate((-vertices, vertices), axis=3)
            
        vertices = vertices.reshape((data.shape[0],
                                     data.shape[1],
                                     data.shape[2],
                                     2,
                                     3))

        # Offset each vertex by the
        # corresponding voxel coordinates
        for i in range(data.shape[0]):
            vertices[i, :, :, :, 0] += starts[0] + i * steps[0]
            
        for i in range(data.shape[1]):
            vertices[:, i, :, :, 1] += starts[1] + i * steps[1]
            
        for i in range(data.shape[2]):
            vertices[:, :, i, :, 2] += starts[2] + i * steps[2]

        self.voxelVertices = vertices
        self.sampleStarts  = starts
        self.sampleSteps   = steps

        GLLineVector.__vertices[image] = vertices, starts, steps, newHash


    def getVertices(self, zpos):

        display = self.display
        image   = self.image
        xax     = self.xax
        yax     = self.yax
        zax     = self.zax
        shape   = self.voxelVertices.shape[:3]

        if display.transform in ('id', 'pixdim'):

            starts = self.sampleStarts
            steps  = self.sampleSteps

            if display.transform == 'pixdim':
                zpos = zpos / image.pixdim[zax]

            zpos = np.floor(zpos + 0.5)

            if zpos < 0 or zpos >= image.shape[zax]:
                return np.array([], dtype=np.float32)

            slices      = [slice(None)] * 3
            slices[zax] = np.floor((zpos - starts[zax]) / steps[zax])

            vertices = self.voxelVertices[slices[0],
                                          slices[1],
                                          slices[2],
                                          :, :]

        else:
            # sample a plane in the display coordinate system
            coords = globject.calculateSamplePoints(
                image.shape[:3],
                image.pixdim[:3],
                [display.resolution] * 3,
                display.getTransform('voxel', 'display'),
                xax,
                yax,
                upsample=True)[0]

            coords[:, zax] = zpos

            # transform that plane into voxel coordinates
            coords = transform.transform(
                coords, display.getTransform('display', 'voxel'))

            # remove any out-of-bounds voxel coordinates
            coords   = np.array(coords.round(), dtype=np.int32)
            coords   = coords[((coords >= [0, 0, 0]) &
                               (coords <  shape)).all(1), :]

            # pull out the vertex data
            vertices = self.voxelVertices[coords[:, 0],
                                          coords[:, 1],
                                          coords[:, 2], :, :] 

        return vertices


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
