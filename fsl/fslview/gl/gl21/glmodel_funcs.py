#!/usr/bin/env python
#
# glmodel_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import OpenGL.GL              as gl

import fsl.fslview.gl.shaders as shaders


def compileShaders(self):
    vertShaderSrc = shaders.getVertexShader(  self)
    fragShaderSrc = shaders.getFragmentShader(self)
    self.shaders  = shaders.compileShaders(vertShaderSrc, fragShaderSrc)

    self.texPos       = gl.glGetUniformLocation(self.shaders, 'tex')
    self.texWidthPos  = gl.glGetUniformLocation(self.shaders, 'texWidth')
    self.texHeightPos = gl.glGetUniformLocation(self.shaders, 'texHeight') 


def destroy(self):
    gl.glDeleteProgram(self.shaders)


def updateShaders(self):

    width, height = self._renderTexture.getSize()
    gl.glUseProgram(self.shaders)
    gl.glUniform1i( self.texPos,       0)
    gl.glUniform1f( self.texWidthPos,  width)
    gl.glUniform1f( self.texHeightPos, height)
    gl.glUseProgram(0)


def loadShaders(self):
    gl.glUseProgram(self.shaders)


def unloadShaders(self):
    gl.glUseProgram(0)
