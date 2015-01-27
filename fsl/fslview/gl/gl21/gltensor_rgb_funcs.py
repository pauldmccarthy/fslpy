#!/usr/bin/env python
#
# gltensor_rgb_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import numpy                as np
import OpenGL.GL            as gl
import OpenGL.raw.GL._types as gltypes

import fsl.fslview.gl.shaders  as shaders
import fsl.fslview.gl.globject as globject


log = logging.getLogger(__name__)


def init(self):

    self.worldCoordBuffer = gl.glGenBuffers(1)
    self.indexBuffer      = gl.glGenBuffers(1)

    vertShaderSrc = shaders.getVertexShader(  'gltensor_rgb')
    fragShaderSrc = shaders.getFragmentShader('gltensor_rgb')
    self.shaders  = shaders.compileShaders(vertShaderSrc, fragShaderSrc)

    self.worldToWorldMatPos = gl.glGetUniformLocation(self.shaders,
                                                      'worldToWorldMat')
    self.xaxPos             = gl.glGetUniformLocation(self.shaders,
                                                      'xax')
    self.yaxPos             = gl.glGetUniformLocation(self.shaders,
                                                      'yax')
    self.zaxPos             = gl.glGetUniformLocation(self.shaders,
                                                      'zax')
    self.worldCoordPos      = gl.glGetAttribLocation( self.shaders,
                                                      'worldCoords') 
    self.zCoordPos          = gl.glGetUniformLocation(self.shaders,
                                                      'zCoord')

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
    self.imageShapePos      = gl.glGetUniformLocation(self.shaders,
                                                      'imageShape')
    self.useSplinePos       = gl.glGetUniformLocation(self.shaders,
                                                      'useSpline')
    self.displayToVoxMatPos = gl.glGetUniformLocation(self.shaders,
                                                      'displayToVoxMat')


def destroy(self):
    gl.glDeleteProgram(self.shaders)
    gl.glDeleteBuffers(1, gltypes.GLuint(self.worldCoordBuffer))
    gl.glDeleteBuffers(1, gltypes.GLuint(self.indexBuffer)) 


def setAxes(self):

    worldCoords, indices = globject.slice2D(self.image.shape,
                                            self.xax,
                                            self.yax,
                                            self.display.voxToDisplayMat)

    worldCoords = worldCoords[:, [self.xax, self.yax]]

    worldCoords = worldCoords.ravel('C')
    indices     = indices    .ravel('C')

    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.worldCoordBuffer)
    gl.glBufferData(gl.GL_ARRAY_BUFFER, 
                    worldCoords.nbytes,
                    worldCoords,
                    gl.GL_STATIC_DRAW)

    gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.indexBuffer)
    gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER,
                    indices.nbytes,
                    indices,
                    gl.GL_STATIC_DRAW) 


def preDraw(self):

    display = self.display
    
    # load the shaders
    gl.glUseProgram(self.shaders)

    # bind the current interpolation setting,
    # image shape, and image->screen axis
    # mappings
    gl.glUniform1f( self.useSplinePos,     display.interpolation == 'spline')
    
    gl.glUniform3fv(self.imageShapePos, 1, np.array(self.image.shape,
                                                     dtype=np.float32))
    gl.glUniform1i( self.xaxPos,           self.xax)
    gl.glUniform1i( self.yaxPos,           self.yax)
    gl.glUniform1i( self.zaxPos,           self.zax)

    # Bind transformation matrices to transform
    # display coordinates to voxel coordinates,
    # and to scale voxel values to colour map
    # texture coordinates
    w2v = np.array(display.displayToVoxMat, dtype=np.float32).ravel('C')
    
    gl.glUniformMatrix4fv(self.displayToVoxMatPos, 1, False, w2v)

    # Set up the colour texture
    gl.glUniform1i(self.imageTexturePos,   0)
    gl.glUniform1i(self.modTexturePos,     1)
    gl.glUniform1i(self.xColourTexturePos, 2)
    gl.glUniform1i(self.yColourTexturePos, 3)
    gl.glUniform1i(self.zColourTexturePos, 4)

    # Bind the world x/y coordinate buffer
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.worldCoordBuffer)
    gl.glVertexAttribPointer(
        self.worldCoordPos,
        2,
        gl.GL_FLOAT,
        gl.GL_FALSE,
        0,
        None)
    gl.glEnableVertexAttribArray(self.worldCoordPos)

    # Bind the vertex index buffer
    gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.indexBuffer) 


def draw(self, zpos, xform=None):
    
    if xform is None: xform = np.identity(4)
    
    w2w = np.array(xform, dtype=np.float32).ravel('C')

    # Bind the current world z position, and
    # the xform transformation matrix
    gl.glUniform1f(       self.zCoordPos,                    zpos)
    gl.glUniformMatrix4fv(self.worldToWorldMatPos, 1, False, w2w)

    # Draw all of the triangles!
    gl.glDrawElements(gl.GL_TRIANGLE_STRIP,
                      4,
                      gl.GL_UNSIGNED_INT,
                      None) 


def postDraw(self):
    
    gl.glDisableVertexAttribArray(self.worldCoordPos)
    
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER,         0)
    gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, 0)
    gl.glUseProgram(0)
