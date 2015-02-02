#!/usr/bin/env python
#
# glvector_rgb_funcs.py - 
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import numpy                          as np
import OpenGL.GL                      as gl
import OpenGL.raw.GL._types           as gltypes
import OpenGL.GL.ARB.fragment_program as arbfp
import OpenGL.GL.ARB.vertex_program   as arbvp

import fsl.fslview.gl.shaders  as shaders
import fsl.fslview.gl.globject as globject

log = logging.getLogger(__name__)


######################
# Methods for RGB mode
######################

# The vector data is stored as a 3D RGB texture,
# and rendered as a four-vertex slice through said
# texture. The fragment program looks up each of
# the texture values, and calculates the appropriate
# colour (red for axial, blue for sagittal, green
# for coronal?) for the fragment


def init(self):

    vertShaderSrc = shaders.getVertexShader('generic')
    fragShaderSrc = shaders.getFragmentShader(self)

    vertexProgram, fragmentProgram = shaders.compilePrograms(
        vertShaderSrc, fragShaderSrc)
    
    self.vertexProgram   = vertexProgram
    self.fragmentProgram = fragmentProgram


def destroy(self):

    arbvp.glDeleteProgramsARB(1, gltypes.GLuint(self.vertexProgram))
    arbfp.glDeleteProgramsARB(1, gltypes.GLuint(self.fragmentProgram))


def setAxes(self):

    worldCoords, idxs = globject.slice2D(self.image.shape,
                                         self.xax,
                                         self.yax,
                                         self.display.voxToDisplayMat)

    self.worldCoords = worldCoords
    self.indices     = idxs


def preDraw(self):

    gl.glEnable(arbvp.GL_VERTEX_PROGRAM_ARB) 
    gl.glEnable(arbfp.GL_FRAGMENT_PROGRAM_ARB)

    arbvp.glBindProgramARB(arbvp.GL_VERTEX_PROGRAM_ARB,
                           self.vertexProgram)
    arbfp.glBindProgramARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                           self.fragmentProgram)

    # the vertex program needs to be able to
    # transform from display space to voxel
    # space
    shaders.setVertexProgramMatrix(0, self.display.displayToVoxMat.T)

    # the fragment program needs to know the image
    # shape and its inverse, so it can scale voxel
    # coordinates to the range [0.0, 1.0], and so
    # it can clip fragments outside of the image
    # space
    shape    = list(self.image.shape)
    invshape = [1.0 / s for s in shape]
    shaders.setFragmentProgramVector(0, shape    + [0])
    shaders.setFragmentProgramVector(1, invshape + [0])
    shaders.setFragmentProgramMatrix(2, np.eye(4))


def draw(self, zpos, xform=None):

    worldCoords  = self.worldCoords
    indices      = self.indices
    worldCoords[:, self.zax] = zpos

    worldCoords = worldCoords.ravel('C')

    if xform is None:
        xform = np.eye(4)

    shaders.setVertexProgramMatrix(4, xform.T)

    gl.glVertexPointer(3, gl.GL_FLOAT, 0, worldCoords)

    gl.glDrawElements(gl.GL_TRIANGLE_STRIP,
                      len(indices),
                      gl.GL_UNSIGNED_INT,
                      indices) 


def postDraw(self):

    gl.glDisable(arbfp.GL_FRAGMENT_PROGRAM_ARB)
    gl.glDisable(arbvp.GL_VERTEX_PROGRAM_ARB)
