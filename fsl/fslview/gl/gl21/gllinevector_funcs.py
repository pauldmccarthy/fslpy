#!/usr/bin/env python
#
# gllinevector_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import numpy                  as np
import OpenGL.GL              as gl
import OpenGL.raw.GL._types   as gltypes

import fsl.fslview.gl.shaders as shaders


def init(self):
    self.shaders = None

    compileShaders(   self)
    updateShaderState(self)

    self.vertexBuffer = gl.glGenBuffers(1) 

    
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
    self.voxToDisplayMatPos = gl.glGetUniformLocation(self.shaders,
                                                      'voxToDisplayMat')
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
    voxToDisplayMat = display.getTransform('voxel', 'display')
    useSpline       = display.interpolation == 'spline'
    imageShape      = np.array(self.image.shape, dtype=np.float32)

    voxValXform     = np.array(voxValXform,     dtype=np.float32).ravel('C')
    cmapXform       = np.array(cmapXform,       dtype=np.float32).ravel('C')
    voxToDisplayMat = np.array(voxToDisplayMat, dtype=np.float32).ravel('C')

    print voxToDisplayMat

    gl.glUseProgram(self.shaders)

    gl.glUniform1f( self.useSplinePos,     useSpline)
    gl.glUniform3fv(self.imageShapePos, 1, imageShape)
    
    gl.glUniformMatrix4fv(self.voxValXformPos,     1, False, voxValXform)
    gl.glUniformMatrix4fv(self.cmapXformPos,       1, False, cmapXform)
    gl.glUniformMatrix4fv(self.voxToDisplayMatPos, 1, False, voxToDisplayMat)

    gl.glUniform1f(self.modThresholdPos,   opts.modThreshold / 100.0)

    gl.glUniform1i(self.imageTexturePos,   0)
    gl.glUniform1i(self.modTexturePos,     1)
    gl.glUniform1i(self.xColourTexturePos, 2)
    gl.glUniform1i(self.yColourTexturePos, 3)
    gl.glUniform1i(self.zColourTexturePos, 4)

    gl.glUseProgram(0) 


def preDraw(self):
    gl.glUseProgram(self.shaders)

    
def draw(self, zpos, xform=None):

    if self.display.transform != 'id':
        print "oh no you don't ({})".format(self.display.transform)
        return

    slices           = [slice(None)] * 3
    slices[self.zax] = np.floor(zpos)

    vertices = self.voxelVertices[slices[0], slices[1], slices[2], :]

    nvertices = vertices.size / 3

    print vertices.shape
    
    vertices  = vertices.ravel('C')


    gl.glDrawArrays(gl.GL_LINES, 0, nvertices)


def drawAll(self, zposes, xforms):

    # TODO a proper implementation
    for zpos, xform in zip(zposes, xforms):
        draw(zpos, xform)


def postDraw(self):
    gl.glUseProgram(0)
