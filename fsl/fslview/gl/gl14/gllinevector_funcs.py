#!/usr/bin/env python
#
# gllinevector_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import numpy                          as np

import OpenGL.GL                      as gl
import OpenGL.GL.ARB.fragment_program as arbfp
import OpenGL.GL.ARB.vertex_program   as arbvp
import OpenGL.raw.GL._types           as gltypes

import fsl.utils.transform            as transform
import fsl.fslview.gl.shaders         as shaders


log = logging.getLogger(__name__)


_vertices = {}


def init(self):

    self.vertexProgram   = None
    self.fragmentProgram = None

    compileShaders(   self)
    updateShaderState(self)
    updateVertices(   self)

    display = self.display
    opts    = self.opts

    display.addListener('resolution', self.name, updateVertices)
    opts   .addListener('directed',   self.name, updateVertices)


def destroy(self):
    arbvp.glDeleteProgramsARB(1, gltypes.GLuint(self.vertexProgram))
    arbfp.glDeleteProgramsARB(1, gltypes.GLuint(self.fragmentProgram))

    self.display.removeListener('resolution', self.name)
    self.opts   .removeListener('directed',   self.name)

    _vertices.pop(self.image, None)


def compileShaders(self):
    if self.vertexProgram is not None:
        arbvp.glDeleteProgramsARB(1, gltypes.GLuint(self.vertexProgram))
        
    if self.fragmentProgram is not None:
        arbfp.glDeleteProgramsARB(1, gltypes.GLuint(self.fragmentProgram)) 

    vertShaderSrc = shaders.getVertexShader(  self,
                                              sw=self.display.softwareMode)
    fragShaderSrc = shaders.getFragmentShader(self,
                                              sw=self.display.softwareMode)

    vertexProgram, fragmentProgram = shaders.compilePrograms(
        vertShaderSrc, fragShaderSrc)

    self.vertexProgram   = vertexProgram
    self.fragmentProgram = fragmentProgram


def updateVertices(self, *a):
    
    image   = self.image
    display = self.display
    opts    = self.opts
    
    vertices, starts, steps, oldHash = _vertices.get(
        image, (None, None, None, None))

    newHash = (hash(display.transform)  ^
               hash(display.resolution) ^
               hash(opts   .directed))

    if (vertices is not None) and (oldHash == newHash):
        
        log.debug('Using previously calculated line '
                  'vertices for {}'.format(image))
        self.lineVertices = vertices
        self.sampleStarts = starts
        self.sampleSteps  = steps
        return

    log.debug('Re-generating line vertices for {}'.format(image))

    vertices, starts, steps = self.generateLineVertices()

    _vertices[image] = vertices, starts, steps, newHash
    
    self.lineVertices = vertices
    self.sampleStarts = starts
    self.sampleSteps  = steps 


def updateShaderState(self):
    opts = self.displayOpts

    gl.glEnable(arbvp.GL_VERTEX_PROGRAM_ARB) 
    gl.glEnable(arbfp.GL_FRAGMENT_PROGRAM_ARB)

    arbvp.glBindProgramARB(arbvp.GL_VERTEX_PROGRAM_ARB,
                           self.vertexProgram)
    arbfp.glBindProgramARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                           self.fragmentProgram)
    
    voxValXform  = self.imageTexture.voxValXform
    cmapXform    = self.xColourTexture.getCoordinateTransform()
    shape        = np.array(list(self.image.shape[:3]) + [0], dtype=np.float32)
    invShape     = 1.0 / shape
    modThreshold = [opts.modThreshold / 100.0, 0.0, 0.0, 0.0]

    # Vertex program inputs
    shaders.setVertexProgramVector(  0, invShape)

    # Fragment program inputs
    shaders.setFragmentProgramMatrix(0, voxValXform)
    shaders.setFragmentProgramMatrix(4, cmapXform)
    shaders.setFragmentProgramVector(8, shape)
    shaders.setFragmentProgramVector(9, modThreshold)

    gl.glDisable(arbvp.GL_VERTEX_PROGRAM_ARB) 
    gl.glDisable(arbfp.GL_FRAGMENT_PROGRAM_ARB)
    

def preDraw(self):
    gl.glEnable(arbvp.GL_VERTEX_PROGRAM_ARB) 
    gl.glEnable(arbfp.GL_FRAGMENT_PROGRAM_ARB)

    gl.glEnableClientState(gl.GL_VERTEX_ARRAY)

    arbvp.glBindProgramARB(arbvp.GL_VERTEX_PROGRAM_ARB,
                           self.vertexProgram)
    arbfp.glBindProgramARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                           self.fragmentProgram) 


def draw(self, zpos, xform=None):

    opts     = self.displayOpts
    vertices = self.getVertices(
        zpos,
        self.lineVertices,
        self.sampleStarts,
        self.sampleSteps)

    vertices = vertices.ravel('C')
    v2d      = self.display.getTransform('voxel', 'display')

    if xform is None: xform = v2d
    else:             xform = transform.concat(v2d, xform)
 
    gl.glPushMatrix()
    gl.glMultMatrixf(np.array(xform, dtype=np.float32).ravel('C'))

    gl.glVertexPointer(3, gl.GL_FLOAT, 0, vertices)
    
    gl.glLineWidth(opts.lineWidth)
    gl.glDrawArrays(gl.GL_LINES, 0, vertices.size / 3)

    gl.glPopMatrix()


def drawAll(self, zposes, xforms):
    for zpos, xform in zip(zposes, xforms):
        draw(self, zpos, xform)


def postDraw(self):
    
    gl.glDisable(arbvp.GL_VERTEX_PROGRAM_ARB) 
    gl.glDisable(arbfp.GL_FRAGMENT_PROGRAM_ARB)
    
    gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
