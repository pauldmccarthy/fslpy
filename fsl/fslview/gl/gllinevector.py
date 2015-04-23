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


def cartesian(arrays, out=None):
    """Generate a cartesian product of input arrays.

    This function is used to generate line vector vertex indices (see
    :meth:`GLLineVector.generateLineVertices`).

    Courtesy of http://stackoverflow.com/a/1235363

    Parameters
    ----------
    arrays : list of array-like
        1-D arrays to form the cartesian product of.
    out : ndarray
        Array to place the cartesian product in.

    Returns
    -------
    out : ndarray
        2-D array of shape (M, len(arrays)) containing cartesian products
        formed of input arrays.

    Examples
    --------
    >>> cartesian(([1, 2, 3], [4, 5], [6, 7]))
    array([[1, 4, 6],
           [1, 4, 7],
           [1, 5, 6],
           [1, 5, 7],
           [2, 4, 6],
           [2, 4, 7],
           [2, 5, 6],
           [2, 5, 7],
           [3, 4, 6],
           [3, 4, 7],
           [3, 5, 6],
           [3, 5, 7]])

    """

    arrays = [np.asarray(x) for x in arrays]
    dtype = arrays[0].dtype

    n = np.prod([x.size for x in arrays])
    if out is None:
        out = np.zeros([n, len(arrays)], dtype=dtype)

    m = n / arrays[0].size
    out[:, 0] = np.repeat(arrays[0], m)
    if arrays[1:]:
        cartesian(arrays[1:], out=out[0:m, 1:])
        for j in xrange(1, arrays[0].size):
            out[j * m:(j + 1) * m, 1:] = out[0:m, 1:]
    return out


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

        vertices, oldHash = GLLineVector.__vertices.get(
            image, (None, None))

        newHash = (hash(display.transform)  ^
                   hash(display.resolution) ^
                   hash(opts   .directed))

        if (vertices is not None) and (oldHash == newHash):
            
            log.debug('Using previously calculated line '
                      'vertices for {}'.format(image))
            self.voxelVertices = vertices
            return

        log.debug('Re-generating line vertices for {}'.format(image))

        data     = globject.subsample(image.data,
                                      display.resolution,
                                      image.pixdim)
        vertices = np.array(data, dtype=np.float32)

        x    = vertices[:, :, :, 0]
        y    = vertices[:, :, :, 1]
        z    = vertices[:, :, :, 2]
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
        for i in range(data.shape[0]): vertices[i, :, :, :, 0] += i
        for i in range(data.shape[1]): vertices[:, i, :, :, 1] += i
        for i in range(data.shape[2]): vertices[:, :, i, :, 2] += i

        self.voxelVertices = vertices

        GLLineVector.__vertices[image] = vertices, newHash


    def generateVertexIndices(self, zpos):

        display = self.display
        image   = self.image
        xax     = self.xax
        yax     = self.yax
        zax     = self.zax
        shape   = self.voxelVertices.shape[:3]

        if display.transform in ('id', 'pixdim'):

            if display.transform == 'pixdim':
                zpos = zpos / image.pixdim[zax]

            zpos = np.floor(zpos + 0.5)

            if zpos < 0 or zpos >= image.shape[zax]:
                return np.array([], dtype=np.uint32)

            indices = [None] * 3
            indices[xax] = np.arange(image.shape[xax], dtype=np.uint32)
            indices[yax] = np.arange(image.shape[yax], dtype=np.uint32)
            indices[zax] = np.array([zpos],            dtype=np.uint32)

            indices = cartesian(indices)
            indices = np.ravel_multi_index((indices[:, 0],
                                            indices[:, 1],
                                            indices[:, 2]),
                                           shape,
                                           order='C')

        else:

            lo, hi = display.getDisplayBounds()

            if zpos <= lo[self.zax] or zpos >= hi[self.zax]:
                return np.array([], dtype=np.uint32)

            # sample a plane at the given display
            # coordinate system zpos, through the
            # image coordinate system space

            # TODO change calcSamPoin signature
            indices = globject.calculateSamplePoints(
                image, display, xax, yax)[0]

            indices[:, zax] = zpos

            # transform to voxel space
            indices = transform.transform(
                indices,
                display.getTransform('display', 'voxel'))

            indices = np.array(indices + 0.5, dtype=np.uint32)

            indices = indices[((indices >= [0, 0, 0]) & (indices < shape)).all(1), :]

            # flatten to 1D indices
            indices = np.ravel_multi_index((indices[:, 0],
                                            indices[:, 1],
                                            indices[:, 2]),
                                           shape,
                                           order='C')

        indices        = (indices * 2).repeat(2)
        indices[1::2] += 1 
        indices = np.array(indices, dtype=np.uint32)

        return indices


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
