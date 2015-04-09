#!/usr/bin/env python
#
# gltest_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import OpenGL.GL as gl

import fsl.utils.transform    as transform
import fsl.fslview.gl.shaders as shaders

log = logging.getLogger(__name__)

def init(self):

    vertShaderSrc = shaders.getVertexShader(  self)
    fragShaderSrc = shaders.getFragmentShader(self)

    self.shaders = shaders.compileShaders(vertShaderSrc, fragShaderSrc)

    self.colourTexturePos = gl.glGetUniformLocation(self.shaders, 'colourTexture')
    self.imageTexturePos  = gl.glGetUniformLocation(self.shaders, 'imageTexture')
    self.voxValueXformPos = gl.glGetUniformLocation(self.shaders, 'voxValueXform')

    self.vertexPos   = gl.glGetAttribLocation(self.shaders, 'vertex')
    self.texCoordPos = gl.glGetAttribLocation(self.shaders, 'texCoord')

    self.vertexBuffer   = gl.glGenBuffers(1)
    self.indexBuffer    = gl.glGenBuffers(1)
    self.texCoordBuffer = gl.glGenBuffers(1)


def destroy(self):
    pass


def preDraw(self):

    gl.glUseProgram(self.shaders)

    voxValueXform = transform.concat(
        self.imageTexture.voxValXform,
        self.colourTexture.getCoordinateTransform()).ravel('C')
    
    gl.glUniformMatrix4fv(
        self.voxValueXformPos,
        1,
        False,
        voxValueXform)

    gl.glUniform1i(self.imageTexturePos,  0)
    gl.glUniform1i(self.colourTexturePos, 1)


def draw(self, vertices, indices, texCoords):
    
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vertexBuffer)
    gl.glBufferData(gl.GL_ARRAY_BUFFER, 
                    vertices.nbytes,
                    vertices,
                    gl.GL_STATIC_DRAW) 
    gl.glVertexAttribPointer(
        self.vertexPos,
        3,
        gl.GL_FLOAT,
        gl.GL_FALSE,
        0,
        None)
    gl.glEnableVertexAttribArray(self.vertexPos)
    
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.texCoordBuffer)
    gl.glBufferData(gl.GL_ARRAY_BUFFER, 
                    texCoords.nbytes,
                    texCoords,
                    gl.GL_STATIC_DRAW) 
    gl.glVertexAttribPointer(
        self.texCoordPos,
        3,
        gl.GL_FLOAT,
        gl.GL_FALSE,
        0,
        None)
    gl.glEnableVertexAttribArray(self.texCoordPos)

    gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.indexBuffer)
    gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER,
                    indices.nbytes,
                    indices,
                    gl.GL_STATIC_DRAW)

    gl.glDrawElements(gl.GL_TRIANGLE_STRIP, 4, gl.GL_UNSIGNED_INT, None) 

    
def postDraw(self):

    gl.glDisableVertexAttribArray(self.vertexPos)
    gl.glDisableVertexAttribArray(self.texCoordPos)
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER,         0)
    gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, 0) 
    gl.glUseProgram(0)
