#!/usr/bin/env python
#
# gllinevector_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import numpy                   as np
import OpenGL.GL               as gl
import OpenGL.raw.GL._types    as gltypes

import fsl.utils.transform     as transform
import fsl.fslview.gl.globject as globject
import fsl.fslview.gl.shaders  as shaders


def cartesian(arrays, out=None):
    """Generate a cartesian product of input arrays.

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


def init(self):
    self.shaders = None

    self.vertexBuffer = gl.glGenBuffers(1)

    compileShaders(   self)
    updateShaderState(self)

    
def destroy(self):
    gl.glDeleteBuffers(1, gltypes.GLuint(self.vertexBuffer))
    gl.glDeleteProgram(self.shaders) 


def compileShaders(self):
    if self.shaders is not None:
        gl.glDeleteProgram(self.shaders) 
    
    vertShaderSrc = shaders.getVertexShader(  self, fast=self.display.fastMode)
    fragShaderSrc = shaders.getFragmentShader(self, fast=self.display.fastMode)
    
    self.shaders = shaders.compileShaders(vertShaderSrc, fragShaderSrc)

    self.vertexPos          = gl.glGetAttribLocation( self.shaders,
                                                      'vertex')
    self.imageShapePos      = gl.glGetUniformLocation(self.shaders,
                                                      'imageShape') 
    self.imageTexturePos    = gl.glGetUniformLocation(self.shaders,
                                                      'imageTexture')
    self.modTexturePos      = gl.glGetUniformLocation(self.shaders,
                                                      'modTexture')
    self.xColourTexturePos  = gl.glGetUniformLocation(self.shaders,
                                                      'xColourTexture')
    self.yColourTexturePos  = gl.glGetUniformLocation(self.shaders,
                                                      'yColourTexture') 
    self.zColourTexturePos  = gl.glGetUniformLocation(self.shaders,
                                                      'zColourTexture')
    self.modThresholdPos    = gl.glGetUniformLocation(self.shaders,
                                                      'modThreshold') 
    self.useSplinePos       = gl.glGetUniformLocation(self.shaders,
                                                      'useSpline')
    self.voxValXformPos     = gl.glGetUniformLocation(self.shaders,
                                                      'voxValXform')
    self.cmapXformPos       = gl.glGetUniformLocation(self.shaders,
                                                      'cmapXform')     


def updateShaderState(self):
    
    display = self.display
    opts    = self.displayOpts

    # The coordinate transformation matrices for 
    # each of the three colour textures are identical
    voxValXform     = self.imageTexture.voxValXform
    cmapXform       = self.xColourTexture.getCoordinateTransform()
    useSpline       = display.interpolation == 'spline'
    imageShape      = np.array(self.image.shape[:3], dtype=np.float32)

    voxValXform     = np.array(voxValXform,     dtype=np.float32).ravel('C')
    cmapXform       = np.array(cmapXform,       dtype=np.float32).ravel('C')

    gl.glUseProgram(self.shaders)

    gl.glUniform1f( self.useSplinePos,     useSpline)
    gl.glUniform3fv(self.imageShapePos, 1, imageShape)
    
    gl.glUniformMatrix4fv(self.voxValXformPos,     1, False, voxValXform)
    gl.glUniformMatrix4fv(self.cmapXformPos,       1, False, cmapXform)

    gl.glUniform1f(self.modThresholdPos,   opts.modThreshold / 100.0)

    gl.glUniform1i(self.imageTexturePos,   0)
    gl.glUniform1i(self.modTexturePos,     1)
    gl.glUniform1i(self.xColourTexturePos, 2)
    gl.glUniform1i(self.yColourTexturePos, 3)
    gl.glUniform1i(self.zColourTexturePos, 4)

    # TODO share this buffer across instances
    vertices  = self.voxelVertices.ravel('C')

    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vertexBuffer)
    gl.glBufferData(
        gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)

    gl.glUseProgram(0) 


def preDraw(self):
    gl.glUseProgram(self.shaders)

    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vertexBuffer)
    gl.glVertexAttribPointer(
        self.vertexPos, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, None)
    gl.glEnableVertexAttribArray(self.vertexPos)

    voxToDisplayMat = self.display.getTransform('voxel', 'display')
    voxToDisplayMat = np.array(voxToDisplayMat, dtype=np.float32).ravel('C')

    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glPushMatrix()
    gl.glMultMatrixf(voxToDisplayMat)

    
def draw(self, zpos, xform=None):

    image   = self.image
    display = self.display
    opts    = self.opts

    if display.transform in ('id', 'pixdim'):

        if display.transform == 'pixdim':
            zpos = zpos / image.pixdim[self.zax]
            
        zpos = np.floor(zpos + 0.5)

        if zpos < 0 or zpos >= image.shape[self.zax]:
            return

        indices = [None] * 3
        indices[self.xax] = np.arange(image.shape[self.xax], dtype=np.uint32)
        indices[self.yax] = np.arange(image.shape[self.yax], dtype=np.uint32)
        indices[self.zax] = np.array([zpos],                 dtype=np.uint32)

        indices = cartesian((indices[0], indices[1], indices[2], [0, 1], [0]))

        indices = np.ravel_multi_index((indices[:, 0],
                                        indices[:, 1],
                                        indices[:, 2],
                                        indices[:, 3],
                                        indices[:, 4]),
                                       self.voxelVertices.shape,
                                       order='C')
        
        indices = np.array(indices, dtype=np.uint32) / 3
        
    else:
        print 'Too hard for now!'
        return

    if xform is not None:
        gl.glPushMatrix()
        gl.glMultMatrixf(xform.ravel('C'))
    
    gl.glLineWidth(opts.lineWidth)
    gl.glDrawElements(gl.GL_LINES, indices.size, gl.GL_UNSIGNED_INT, indices)

    if xform is not None:
        gl.glPopMatrix()


def drawAll(self, zposes, xforms):

    # TODO a proper implementation
    for zpos, xform in zip(zposes, xforms):
        self.draw(zpos, xform)


def postDraw(self):
    gl.glUseProgram(0)
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
    gl.glDisableVertexAttribArray(self.vertexPos)

    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glPopMatrix()
