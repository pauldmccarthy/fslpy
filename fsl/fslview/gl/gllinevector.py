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

        # Extract a sub-sample of the vector image
        # at the current display resolution
        data, starts, steps = globject.subsample(image.data,
                                                 display.resolution,
                                                 image.pixdim)

        # Pull out the xyz components of the 
        # vectors, and calculate vector lengths
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
        # representing a line through the origin.
        # Or, if displaying directed vectors,
        # add an origin point for each vector.
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

        # Offset each vertex by the corresponding
        # voxel coordinates, making sure to
        # transform from the sub-sampled indices
        # to the original data indices (offseting
        # and scaling by the starts and steps)
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

        display  = self.display
        image    = self.image
        xax      = self.xax
        yax      = self.yax
        zax      = self.zax
        vertices = self.voxelVertices
        starts   = self.sampleStarts
        steps    = self.sampleSteps

        # If in id/pixdim space, the display
        # coordinate system axes are parallel
        # to the voxeld coordinate system axes
        if display.transform in ('id', 'pixdim'):

            # Turn the z position into a voxel index
            if display.transform == 'pixdim':
                zpos = zpos / image.pixdim[zax]

            zpos = round(zpos)

            # Return no vertices if the requested z
            # position is out of the image bounds
            if zpos < 0 or zpos >= image.shape[zax]:
                return np.array([], dtype=np.float32)

            # Extract a slice at the requested
            # z position from the vertex matrix
            slices      = [slice(None)] * 3
            slices[zax] = np.floor((zpos - starts[zax]) / steps[zax])

            coords = vertices[slices[0],
                              slices[1],
                              slices[2],
                              :, :]

        # If in affine space, the display
        # coordinate system axes may not
        # be parallel to the voxel
        # coordinate system axes
        else:
            # Create a coordinate grid through
            # a plane at the requested z pos 
            # in the display coordinate system
            coords = globject.calculateSamplePoints(
                image.shape[ :3],
                [display.resolution] * 3,
                display.getTransform('voxel', 'display'),
                xax,
                yax)[0]
            
            coords[:, zax] = zpos

            # transform that plane of display
            # coordinates into voxel coordinates
            coords = transform.transform(
                coords, display.getTransform('display', 'voxel'))

            # The voxel vertex matrix may have
            # been sub-sampled (see the
            # __generateLineVertices method),
            # so we need to transform the image
            # data voxel coordinates to the
            # sub-sampled data voxel coordinates.
            coords = (coords - starts) / steps
            
            # remove any out-of-bounds voxel coordinates
            shape  = vertices.shape[:3]
            coords = np.array(coords.round(), dtype=np.int32)
            coords = coords[((coords >= [0, 0, 0]) &
                             (coords <  shape)).all(1), :]

            # pull out the vertex data
            coords = vertices[coords[:, 0],
                              coords[:, 1],
                              coords[:, 2],
                              :, :] 
        return coords


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
