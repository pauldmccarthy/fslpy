#!/usr/bin/env python
#
# glvector_line_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import numpy                   as np
import OpenGL.GL               as gl
import OpenGL.raw.GL._types    as gltypes

import fsl.fslview.gl.shaders  as shaders
import fsl.fslview.gl.globject as globject


log = logging.getLogger(__name__)


def init(self):

    vertShaderSrc = shaders.getVertexShader(  'glvector_line')
    fragShaderSrc = shaders.getFragmentShader('glvector_rgb')
    
    self.shaders          = shaders.compileShaders(vertShaderSrc,
                                                   fragShaderSrc)
    self.shaderParams     = {}
    self.worldCoordBuffer = gl.glGenBuffers(1)
    self.vertexIDBuffer   = gl.glGenBuffers(1)
    self.indexBuffer      = gl.glGenBuffers(1)

    s = self.shaders
    p = self.shaderParams

    # parameters for common_vert.glsl
    p['displayToVoxMat'] = gl.glGetUniformLocation(s, 'displayToVoxMat')
    p['voxToDisplayMat'] = gl.glGetUniformLocation(s, 'voxToDisplayMat')
    p['worldToWorldMat'] = gl.glGetUniformLocation(s, 'worldToWorldMat')
    p['xax']             = gl.glGetUniformLocation(s, 'xax')
    p['yax']             = gl.glGetUniformLocation(s, 'yax')
    p['zax']             = gl.glGetUniformLocation(s, 'zax')
    p['zCoord']          = gl.glGetUniformLocation(s, 'zCoord')
    p['worldCoords']     = gl.glGetAttribLocation( s, 'worldCoords')

    # parameters for glvector_line_vert/glvector_line_frag.glsl
    p['imageTexture']    = gl.glGetUniformLocation( s, 'imageTexture')
    p['imageValueXform'] = gl.glGetUniformLocation( s, 'imageValueXform')
    p['modTexture']      = gl.glGetUniformLocation( s, 'modTexture')
    p['xColourTexture']  = gl.glGetUniformLocation( s, 'xColourTexture')
    p['yColourTexture']  = gl.glGetUniformLocation( s, 'yColourTexture')
    p['zColourTexture']  = gl.glGetUniformLocation( s, 'zColourTexture')
    p['imageShape']      = gl.glGetUniformLocation( s, 'imageShape')
    p['imageDims']       = gl.glGetUniformLocation( s, 'imageDims')
    p['useSpline']       = gl.glGetUniformLocation( s, 'useSpline')
    p['vertexID']        = gl.glGetAttribLocation(  s, 'vertexID')

    def coordUpdate(*a):
        self.setAxes(self.xax, self.yax)

    self.display.addListener('transform',  self.name, coordUpdate)
    self.display.addListener('resolution', self.name, coordUpdate)

    
def destroy(self):
    gl.glDeleteProgram(self.shaders)
    gl.glDeleteBuffers(1, gltypes.GLuint(self.worldCoordBuffer))
    gl.glDeleteBuffers(1, gltypes.GLuint(self.vertexIDBuffer))
    gl.glDeleteBuffers(1, gltypes.GLuint(self.indexBuffer))

    self.display.removeListener('transform',  self.name)
    self.display.removeListener('resolution', self.name)


def setAxes(self):
    
    worldCoords, xpixdim, ypixdim, lenx, leny = \
        globject.calculateSamplePoints(
            self.image,
            self.display,
            self.xax,
            self.yax)

    worldCoords = worldCoords[:, [self.xax, self.yax]]

    self.nVertices = worldCoords.shape[0] * 2

    worldCoords = np.repeat(worldCoords, 2, 0)
    worldCoords = np.array(worldCoords, dtype=np.float32).ravel('C')
    indices     = np.arange(self.nVertices, dtype=np.uint32)
    vertexIDs   = np.arange(self.nVertices, dtype=np.float32)
    
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.worldCoordBuffer)
    gl.glBufferData(gl.GL_ARRAY_BUFFER, 
                    worldCoords.nbytes,
                    worldCoords,
                    gl.GL_STATIC_DRAW)

    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vertexIDBuffer)
    gl.glBufferData(gl.GL_ARRAY_BUFFER,
                    vertexIDs.nbytes,
                    vertexIDs,
                    gl.GL_STATIC_DRAW) 

    gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.indexBuffer)
    gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER,
                    indices.nbytes,
                    indices,
                    gl.GL_STATIC_DRAW)


def preDraw(self):

    display = self.display
    
    gl.glUseProgram(self.shaders)
    
    pars            = self.shaderParams
    useSpline       = display.interpolation == 'spline'

    imageShape      = np.array(self.image.shape,        dtype=np.float32)
    imageDims       = np.array(self.image.pixdim,       dtype=np.float32) 
    displayToVoxMat = np.array(display.displayToVoxMat, dtype=np.float32)
    voxToDisplayMat = np.array(display.voxToDisplayMat, dtype=np.float32)
    imageValueXform = np.array(self.imageTexture.voxValXform.T,
                               dtype=np.float32)
    
    displayToVoxMat = displayToVoxMat.ravel('C')
    voxToDisplayMat = voxToDisplayMat.ravel('C')        
    imageValueXform = imageValueXform.ravel('C')

    gl.glUniform1f(       pars['useSpline'],                 useSpline)
    gl.glUniform3fv(      pars['imageShape'], 1,             imageShape)
    gl.glUniform3fv(      pars['imageDims'],  1,             imageDims)
    gl.glUniform1i(       pars['xax'],                       self.xax)
    gl.glUniform1i(       pars['yax'],                       self.yax)
    gl.glUniform1i(       pars['zax'],                       self.zax)
    gl.glUniformMatrix4fv(pars['displayToVoxMat'], 1, False, displayToVoxMat)
    gl.glUniformMatrix4fv(pars['voxToDisplayMat'], 1, False, voxToDisplayMat)
    gl.glUniformMatrix4fv(pars['imageValueXform'], 1, False, imageValueXform)
    
    gl.glUniform1i(       pars['imageTexture'],   0)
    gl.glUniform1i(       pars['modTexture'],     1)
    gl.glUniform1i(       pars['xColourTexture'], 2)
    gl.glUniform1i(       pars['yColourTexture'], 3)
    gl.glUniform1i(       pars['zColourTexture'], 4)

    # Bind the world x/y coordinate buffer
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.worldCoordBuffer)
    gl.glVertexAttribPointer(
        pars['worldCoords'],
        2,
        gl.GL_FLOAT,
        gl.GL_FALSE,
        0,
        None)
    gl.glEnableVertexAttribArray(pars['worldCoords'])

    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vertexIDBuffer)
    gl.glVertexAttribPointer(
        pars['vertexID'],
        1,
        gl.GL_FLOAT,
        gl.GL_FALSE,
        0,
        None)
    gl.glEnableVertexAttribArray(pars['vertexID']) 

    # Bind the vertex index buffer
    gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.indexBuffer) 


def draw(self, zpos, xform=None):
    if xform is None: xform = np.identity(4)
    
    xform = np.array(xform, dtype=np.float32).ravel('C')
    pars  = self.shaderParams

    # Bind the current world z position, and
    # the xform transformation matrix
    gl.glUniform1f(       pars['zCoord'],                    zpos)
    gl.glUniformMatrix4fv(pars['worldToWorldMat'], 1, False, xform)

    # Draw all of the triangles!
    gl.glLineWidth(2)
    gl.glDrawElements(gl.GL_LINES,
                      self.nVertices,
                      gl.GL_UNSIGNED_INT,
                      None) 


def postDraw(self):
    gl.glDisableVertexAttribArray(self.shaderParams['worldCoords'])
    gl.glDisableVertexAttribArray(self.shaderParams['vertexID'])
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER,         0)
    gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, 0)
    gl.glUseProgram(0) 
